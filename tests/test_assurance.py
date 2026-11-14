from __future__ import annotations

import copy
import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from agent_evals import __main__, assurance, recording
from agent_evals.assurance import (
    AssuranceSnapshot,
    DATASET_NAME,
    JUDGEMENT_SCORES,
    compare_assurance_experiments,
    export_assurance_snapshot,
    load_assurance_snapshot,
)


@pytest.fixture
def snapshot_data():
    return {
        "rubric_version": "qa-evidence-v1",
        "commit": "a" * 40,
        "assessed_at": "2026-01-01T12:00:00Z",
        "requirements": [
            {
                "requirement_id": f"T{number}",
                "judgement": "covered_completely",
                "weight": 1,
                "evidence_ref": f"review.md#T{number}",
                "explanation": f"Reviewed evidence for T{number}.",
            }
            for number in range(1, 22)
        ],
    }


def snapshot(data):
    return AssuranceSnapshot.model_validate_json(json.dumps(data))


@pytest.mark.parametrize(
    "change",
    [
        lambda data: data["requirements"].pop(),
        lambda data: data["requirements"][0].update(requirement_id="T2"),
        lambda data: data["requirements"][0].update(weight=0),
        lambda data: data["requirements"][0].update(weight="1"),
        lambda data: data["requirements"][0].update(judgement="complete"),
        lambda data: data["requirements"][0].update(score=0.25),
        lambda data: data["requirements"][0].update(evidence_ref="  "),
        lambda data: data.update(assessed_at="2026-01-01T12:00:00"),
        lambda data: data.update(commit="unknown"),
        lambda data: data.update(rubric_version="unknown"),
    ],
)
def test_snapshot_rejects_invalid_input(snapshot_data, change):
    change(snapshot_data)
    with pytest.raises(ValidationError):
        snapshot(snapshot_data)


def test_weighted_score_uses_reviewed_judgements(snapshot_data):
    snapshot_data["requirements"][0].update(judgement="partially_covered", weight=2)
    snapshot_data["requirements"][1].update(judgement="not_covered", weight=3)
    assert snapshot(snapshot_data).score == pytest.approx(20 / 24)


def test_invalid_snapshot_is_rejected_before_phoenix_start(tmp_path, monkeypatch):
    path = tmp_path / "snapshot.json"
    path.write_text("{}", encoding="utf-8")
    ensure = Mock()
    monkeypatch.setattr(recording, "ensure_phoenix", ensure)
    monkeypatch.setattr(sys, "argv", ["agent_evals", "assurance", "--snapshot", str(path)])
    with pytest.raises(ValidationError):
        __main__.main()
    ensure.assert_not_called()


def test_cli_exports_reviewed_snapshot(snapshot_data, tmp_path, monkeypatch, capsys):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_data), encoding="utf-8")
    client = Mock()
    export = Mock(return_value={"dataset_id": "dataset", "experiment_id": "experiment", "score": 1.0})
    monkeypatch.setattr(recording, "ensure_phoenix", lambda: client)
    monkeypatch.setattr(assurance, "export_assurance_snapshot", export)
    monkeypatch.setattr(sys, "argv", ["agent_evals", "assurance", "--snapshot", str(path)])
    __main__.main()
    assert export.call_args.args[0].commit == snapshot_data["commit"]
    assert export.call_args.args[1] is client
    assert json.loads(capsys.readouterr().out)["experiment_id"] == "experiment"


def test_export_rejects_incompatible_dataset(snapshot_data):
    client = Mock()
    client.datasets.list.return_value = [{"name": DATASET_NAME, "id": "existing"}]
    client.datasets.get_dataset.return_value.examples = [{"input": {"requirement_id": "T1"}}]
    client.datasets.get_dataset.return_value.name = DATASET_NAME
    with pytest.raises(RuntimeError, match="T1-T21 exactly once"):
        export_assurance_snapshot(snapshot(snapshot_data), client)
    client.experiments.run_experiment.assert_not_called()


def test_export_reports_incomplete_experiment(snapshot_data):
    client = Mock()
    client.datasets.list.return_value = [{"name": DATASET_NAME, "id": "existing"}]
    client.datasets.get_dataset.return_value.examples = [
        {"input": {"requirement_id": f"T{number}"}} for number in range(1, 22)
    ]
    client.datasets.get_dataset.return_value.name = DATASET_NAME
    client.experiments.run_experiment.return_value = {
        "experiment_id": "failed",
        "task_runs": [],
        "evaluation_runs": [],
    }
    with pytest.raises(RuntimeError, match="failed.*did not complete"):
        export_assurance_snapshot(snapshot(snapshot_data), client)


def test_export_reports_incomplete_persisted_experiment(snapshot_data):
    client = Mock()
    client.datasets.list.return_value = [{"name": DATASET_NAME, "id": "existing"}]
    dataset = client.datasets.get_dataset.return_value
    dataset.id = "existing"
    dataset.name = DATASET_NAME
    dataset.examples = [{"input": {"requirement_id": f"T{number}"}} for number in range(1, 22)]
    client.experiments.run_experiment.return_value = {
        "experiment_id": "incomplete",
        "task_runs": [{"output": {}} for _ in range(21)],
        "evaluation_runs": [Mock(error=None, result={"score": 1.0}) for _ in range(21)],
    }
    client.experiments.get_experiment.return_value = {
        "dataset_id": "existing",
        "experiment_metadata": {},
        "task_runs": [],
        "evaluation_runs": [],
    }
    with pytest.raises(RuntimeError, match="incomplete.*not persisted correctly"):
        export_assurance_snapshot(snapshot(snapshot_data), client)


def test_export_revalidates_mutated_snapshot(snapshot_data):
    reviewed = snapshot(snapshot_data)
    reviewed.requirements.pop()
    client = Mock()
    with pytest.raises(ValidationError):
        export_assurance_snapshot(reviewed, client)
    client.datasets.list.assert_not_called()


def test_export_persists_two_independent_snapshots(snapshot_data, tmp_path, isolated_phoenix):
    client = isolated_phoenix.client
    path = tmp_path / "review.json"
    path.write_text(json.dumps(snapshot_data), encoding="utf-8")
    first = export_assurance_snapshot(load_assurance_snapshot(path), client)

    updated = copy.deepcopy(snapshot_data)
    updated["commit"] = "b" * 40
    updated["assessed_at"] = "2026-02-01T12:00:00Z"
    updated["requirements"][0].update(
        judgement="partially_covered", weight=2, evidence_ref="later-review.md#T1",
        explanation="A gap was found.",
    )
    second = export_assurance_snapshot(snapshot(updated), client)

    assert first["dataset_id"] == second["dataset_id"]
    assert first["experiment_id"] != second["experiment_id"]
    assert first["score"] == 1
    assert second["score"] == pytest.approx(21 / 22)
    for result, data in ((first, snapshot_data), (second, updated)):
        experiment = client.experiments.get_experiment(experiment_id=result["experiment_id"])
        assert experiment["experiment_metadata"]["commit"] == data["commit"]
        assert experiment["experiment_metadata"]["rubric_version"] == data["rubric_version"]
        assert experiment["experiment_metadata"]["spec_assurance_score"] == result["score"]
        assert len(experiment["task_runs"]) == 21
        assert len(experiment["evaluation_runs"]) == 21
        t1_run = next(run for run in experiment["task_runs"] if run["output"]["requirement_id"] == "T1")
        t1_eval = next(item for item in experiment["evaluation_runs"] if item.experiment_run_id == t1_run["id"])
        assert t1_run["output"]["evidence_ref"] == data["requirements"][0]["evidence_ref"]
        assert t1_run["output"]["weight"] == data["requirements"][0]["weight"]
        assert t1_eval.result["label"] == data["requirements"][0]["judgement"]
        assert t1_eval.result["explanation"] == data["requirements"][0]["explanation"]

    with pytest.raises(ValueError, match="weights differ"):
        compare_assurance_experiments(client, first["experiment_id"], second["experiment_id"])


@pytest.fixture
def comparison_client(snapshot_data):
    def experiment(data, experiment_id):
        reviewed = snapshot(data)
        tasks = []
        evaluations = []
        for item in reviewed.requirements:
            run_id = f"{experiment_id}-{item.requirement_id}"
            score = JUDGEMENT_SCORES[item.judgement]
            tasks.append({
                "id": run_id,
                "dataset_example_id": item.requirement_id,
                "output": {**item.model_dump(), "score": score},
            })
            evaluations.append(SimpleNamespace(
                experiment_run_id=run_id,
                name="spec_assurance",
                error=None,
                result={"score": score, "label": item.judgement, "explanation": item.explanation},
            ))
        return {
            "experiment_id": experiment_id,
            "dataset_id": "dataset",
            "dataset_version_id": "version",
            "experiment_metadata": {
                "rubric_version": reviewed.rubric_version,
                "commit": reviewed.commit,
                "assessed_at": reviewed.assessed_at.isoformat(),
                "spec_assurance_score": reviewed.score,
            },
            "task_runs": tasks,
            "evaluation_runs": evaluations,
        }

    baseline_data = copy.deepcopy(snapshot_data)
    baseline_data["requirements"][1]["judgement"] = "mostly_covered"
    candidate_data = copy.deepcopy(snapshot_data)
    candidate_data["commit"] = "b" * 40
    candidate_data["requirements"][0].update(
        judgement="mostly_covered", evidence_ref="new-review.md#T1", explanation="New gap."
    )
    baseline = experiment(baseline_data, "baseline")
    candidate = experiment(candidate_data, "candidate")
    client = Mock()
    client.experiments.get_experiment.side_effect = lambda *, experiment_id: {
        "baseline": baseline, "candidate": candidate,
    }[experiment_id]
    dataset = client.datasets.get_dataset.return_value
    dataset.name = DATASET_NAME
    dataset.examples = [
        {"id": f"T{number}", "input": {"requirement_id": f"T{number}"}}
        for number in range(1, 22)
    ]
    return client, baseline, candidate


def test_comparison_reports_decrease_even_when_aggregate_is_unchanged(comparison_client):
    client, _, _ = comparison_client
    result = compare_assurance_experiments(client, "baseline", "candidate")
    assert result["aggregate_delta"] == 0
    assert result["decreased_requirements"] == ["T1"]
    assert len(result["requirements"]) == 21
    assert result["requirements"][0]["delta"] == -0.25
    assert result["requirements"][0]["candidate"]["evidence_ref"] == "new-review.md#T1"
    assert result["requirements"][1]["status"] == "increased"
    assert result["baseline"]["commit"] == "a" * 40
    client.experiments.run_experiment.assert_not_called()
    client.datasets.create_dataset.assert_not_called()


def test_comparison_uses_matching_nonuniform_weights(comparison_client):
    client, baseline, candidate = comparison_client
    for run in (baseline, candidate):
        run["task_runs"][0]["output"]["weight"] = 2
    baseline["experiment_metadata"]["spec_assurance_score"] = 21.75 / 22
    candidate["experiment_metadata"]["spec_assurance_score"] = 21.5 / 22
    result = compare_assurance_experiments(client, "baseline", "candidate")
    assert result["aggregate_delta"] == pytest.approx(-0.25 / 22)
    assert result["requirements"][0]["weight"] == 2


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda run: run.update(dataset_id="another"), "datasets differ"),
        (lambda run: run["experiment_metadata"].update(rubric_version="another"), "rubric versions differ"),
        (lambda run: run["task_runs"].pop(), "incomplete or failed"),
        (lambda run: run["task_runs"][0].update(error="task failed"), "incomplete or failed"),
        (lambda run: setattr(run["evaluation_runs"][0], "error", "evaluation failed"), "invalid assurance data"),
        (lambda run: run["task_runs"][0]["output"].update(score=1.0), "invalid assurance data"),
        (lambda run: run["experiment_metadata"].update(spec_assurance_score=0), "invalid assurance data"),
        (lambda run: run["task_runs"][0]["output"].update(requirement_id="T2"), "invalid assurance data"),
    ],
)
def test_comparison_rejects_incompatible_or_invalid_experiment(comparison_client, change, message):
    client, _, candidate = comparison_client
    change(candidate)
    with pytest.raises(ValueError, match=message):
        compare_assurance_experiments(client, "baseline", "candidate")


def test_comparison_reads_real_phoenix_without_creating_experiments(
    snapshot_data, isolated_phoenix, monkeypatch, capsys
):
    client = isolated_phoenix.client
    first_data = copy.deepcopy(snapshot_data)
    first_data["requirements"][1]["judgement"] = "mostly_covered"
    second_data = copy.deepcopy(snapshot_data)
    second_data["commit"] = "b" * 40
    second_data["requirements"][0].update(judgement="mostly_covered", explanation="New gap.")
    first = export_assurance_snapshot(snapshot(first_data), client)
    second = export_assurance_snapshot(snapshot(second_data), client)
    experiments_before = client.experiments.list(dataset_id=first["dataset_id"])
    capsys.readouterr()

    monkeypatch.setattr(recording, "local_phoenix_client", lambda: client)
    monkeypatch.setattr(sys, "argv", [
        "agent_evals", "assurance-compare", "--baseline", first["experiment_id"],
        "--candidate", second["experiment_id"],
    ])
    __main__.main()
    report = json.loads(capsys.readouterr().out)
    assert report["decreased_requirements"] == ["T1"]
    assert report["aggregate_delta"] == 0
    assert report["requirements"][1]["status"] == "increased"
    experiments_after = client.experiments.list(dataset_id=first["dataset_id"])
    assert {item["id"] for item in experiments_after} == {item["id"] for item in experiments_before}
