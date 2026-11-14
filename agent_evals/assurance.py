from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Annotated, Literal, TypedDict

from phoenix.client import Client
from phoenix.client.resources.datasets import Dataset
from phoenix.client.resources.experiments.types import RanExperiment
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    model_validator,
)

Judgement = Literal[
    "not_covered",
    "indirectly_covered",
    "partially_covered",
    "mostly_covered",
    "covered_completely",
]
JUDGEMENT_SCORES: dict[Judgement, float] = {
    "not_covered": 0.0,
    "indirectly_covered": 0.25,
    "partially_covered": 0.5,
    "mostly_covered": 0.75,
    "covered_completely": 1.0,
}
REQUIREMENT_IDS = tuple(f"T{number}" for number in range(1, 22))
DATASET_NAME = "spec-assurance-t1-t21-v1"
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class RequirementAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    requirement_id: Literal[
        "T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11",
        "T12", "T13", "T14", "T15", "T16", "T17", "T18", "T19", "T20", "T21",
    ]
    judgement: Judgement
    weight: float = Field(gt=0, allow_inf_nan=False)
    evidence_ref: NonEmptyText
    explanation: NonEmptyText


class AssuranceSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    rubric_version: Literal["qa-evidence-v1"]
    commit: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]
    assessed_at: AwareDatetime
    requirements: list[RequirementAssessment]

    @model_validator(mode="after")
    def require_all_requirements_once(self) -> AssuranceSnapshot:
        ids = [assessment.requirement_id for assessment in self.requirements]
        if len(ids) != len(REQUIREMENT_IDS) or set(ids) != set(REQUIREMENT_IDS):
            raise ValueError("requirements must contain each of T1-T21 exactly once")
        return self

    @property
    def score(self) -> float:
        maximum_weight = max(assessment.weight for assessment in self.requirements)
        scaled_weights = [assessment.weight / maximum_weight for assessment in self.requirements]
        return sum(
            weight * JUDGEMENT_SCORES[assessment.judgement]
            for weight, assessment in zip(scaled_weights, self.requirements)
        ) / sum(scaled_weights)


def load_assurance_snapshot(path: Path) -> AssuranceSnapshot:
    """Load an explicitly reviewed snapshot; validation errors are reported to the caller."""
    return AssuranceSnapshot.model_validate_json(path.read_bytes())


def _assurance_dataset(client: Client) -> Dataset:
    matches = [dataset for dataset in client.datasets.list() if dataset["name"] == DATASET_NAME]
    if len(matches) > 1:
        raise RuntimeError(f"Multiple Phoenix datasets named {DATASET_NAME!r}")
    if matches:
        dataset = client.datasets.get_dataset(dataset=matches[0]["id"])
    else:
        dataset = client.datasets.create_dataset(
            name=DATASET_NAME,
            examples=[
                {"input": {"requirement_id": requirement_id}, "output": {}}
                for requirement_id in REQUIREMENT_IDS
            ],
        )
    _validate_assurance_dataset(dataset)
    return dataset


def _validate_assurance_dataset(dataset: Dataset) -> None:
    inputs = [example["input"] for example in dataset.examples]
    if (
        dataset.name != DATASET_NAME
        or len(inputs) != len(REQUIREMENT_IDS)
        or any(
            not isinstance(item, dict)
            or set(item) != {"requirement_id"}
            or not isinstance(item["requirement_id"], str)
            for item in inputs
        )
        or {item["requirement_id"] for item in inputs} != set(REQUIREMENT_IDS)
    ):
        raise RuntimeError(f"Phoenix dataset {DATASET_NAME!r} must contain T1-T21 exactly once")


def export_assurance_snapshot(snapshot: AssuranceSnapshot, client: Client) -> dict[str, str | float]:
    """Publish a reviewed snapshot as a Phoenix experiment; no tests or judges are run."""
    snapshot = AssuranceSnapshot.model_validate_json(snapshot.model_dump_json())
    dataset = _assurance_dataset(client)
    assessments = {item.requirement_id: item for item in snapshot.requirements}

    def task(input: dict[str, str]) -> dict[str, str | float]:
        assessment = assessments[input["requirement_id"]]
        return {
            "requirement_id": assessment.requirement_id,
            "judgement": assessment.judgement,
            "score": JUDGEMENT_SCORES[assessment.judgement],
            "weight": assessment.weight,
            "evidence_ref": assessment.evidence_ref,
            "explanation": assessment.explanation,
        }

    def evidence_eval(output: dict[str, str | float]) -> dict[str, str | float]:
        return {
            "score": output["score"],
            "label": output["judgement"],
            "explanation": output["explanation"],
        }

    metadata = {
        "rubric_version": snapshot.rubric_version,
        "commit": snapshot.commit,
        "assessed_at": snapshot.assessed_at.isoformat(),
        "spec_assurance_score": snapshot.score,
    }
    run = client.experiments.run_experiment(
        dataset=dataset,
        task=task,
        evaluators={"spec_assurance": evidence_eval},
        experiment_name=f"Spec Assurance {snapshot.commit[:12]} {snapshot.assessed_at.isoformat()}",
        experiment_metadata=metadata,
        print_summary=False,
        retries=0,
    )
    task_runs = run["task_runs"]
    evaluation_runs = run["evaluation_runs"]
    if (
        len(task_runs) != len(REQUIREMENT_IDS)
        or any(run.get("error") or not isinstance(run.get("output"), dict) for run in task_runs)
        or len(evaluation_runs) != len(REQUIREMENT_IDS)
        or any(evaluation.error or evaluation.result is None for evaluation in evaluation_runs)
    ):
        raise RuntimeError(f"Phoenix assurance experiment {run['experiment_id']} did not complete successfully")

    persisted = client.experiments.get_experiment(experiment_id=run["experiment_id"])
    outputs = {item["id"]: item["output"] for item in persisted["task_runs"] if not item.get("error")}
    expected_outputs = {requirement_id: task({"requirement_id": requirement_id}) for requirement_id in REQUIREMENT_IDS}
    actual_outputs = {
        output.get("requirement_id"): output
        for output in outputs.values()
        if isinstance(output, dict)
    }
    evaluations = persisted["evaluation_runs"]
    if (
        persisted["dataset_id"] != dataset.id
        or dict(persisted["experiment_metadata"]) != metadata
        or len(persisted["task_runs"]) != len(REQUIREMENT_IDS)
        or actual_outputs != expected_outputs
        or len(evaluations) != len(REQUIREMENT_IDS)
        or {evaluation.experiment_run_id for evaluation in evaluations} != set(outputs)
        or any(
            evaluation.name != "spec_assurance"
            or evaluation.error
            or evaluation.result != evidence_eval(outputs[evaluation.experiment_run_id])
            for evaluation in evaluations
        )
    ):
        raise RuntimeError(f"Phoenix assurance experiment {run['experiment_id']} was not persisted correctly")
    return {
        "experiment_id": run["experiment_id"],
        "dataset_id": run["dataset_id"],
        "score": snapshot.score,
    }


class ReviewResult(TypedDict):
    judgement: Judgement
    score: float
    evidence_ref: str
    explanation: str


class RequirementComparison(TypedDict):
    requirement_id: str
    weight: float
    baseline: ReviewResult
    candidate: ReviewResult
    delta: float
    status: Literal["decreased", "unchanged", "increased"]


class ComparisonReview(TypedDict):
    experiment_id: str
    commit: str
    assessed_at: str
    score: float


class AssuranceComparison(TypedDict):
    rubric_version: str
    baseline: ComparisonReview
    candidate: ComparisonReview
    aggregate_delta: float
    decreased_requirements: list[str]
    requirements: list[RequirementComparison]


def _read_persisted_snapshot(client: Client, experiment: RanExperiment) -> AssuranceSnapshot:
    experiment_id = experiment["experiment_id"]
    dataset = client.datasets.get_dataset(
        dataset=experiment["dataset_id"], version_id=experiment["dataset_version_id"]
    )
    _validate_assurance_dataset(dataset)
    example_requirements = {
        example["id"]: example["input"]["requirement_id"] for example in dataset.examples
    }
    task_runs = experiment["task_runs"]
    evaluations = experiment["evaluation_runs"]
    if (
        len(task_runs) != len(REQUIREMENT_IDS)
        or len(evaluations) != len(REQUIREMENT_IDS)
        or {run["dataset_example_id"] for run in task_runs} != set(example_requirements)
        or len({run["id"] for run in task_runs}) != len(REQUIREMENT_IDS)
        or any(run.get("error") or not isinstance(run["output"], dict) for run in task_runs)
        or {evaluation.experiment_run_id for evaluation in evaluations} != {run["id"] for run in task_runs}
    ):
        raise ValueError(f"Experiment {experiment_id} has incomplete or failed runs")

    evaluations_by_run = {evaluation.experiment_run_id: evaluation for evaluation in evaluations}
    assessments = []
    try:
        for run in task_runs:
            output = run["output"]
            if output["requirement_id"] != example_requirements[run["dataset_example_id"]]:
                raise ValueError("task output does not match its dataset requirement")
            assessment_data = {key: value for key, value in output.items() if key != "score"}
            assessment = RequirementAssessment.model_validate(assessment_data)
            score = JUDGEMENT_SCORES[assessment.judgement]
            evaluation = evaluations_by_run[run["id"]]
            if (
                isinstance(output["score"], bool)
                or not isinstance(output["score"], (int, float))
                or output["score"] != score
                or evaluation.name != "spec_assurance"
                or evaluation.error
                or evaluation.result != {
                    "score": score,
                    "label": assessment.judgement,
                    "explanation": assessment.explanation,
                }
            ):
                raise ValueError("stored score or evaluation does not match its judgement")
            assessments.append(assessment.model_dump())
        metadata = experiment["experiment_metadata"]
        snapshot = AssuranceSnapshot.model_validate_json(
            json.dumps({
                "rubric_version": metadata["rubric_version"],
                "commit": metadata["commit"],
                "assessed_at": metadata["assessed_at"],
                "requirements": assessments,
            })
        )
        stored_score = metadata["spec_assurance_score"]
        if (
            isinstance(stored_score, bool)
            or not isinstance(stored_score, (int, float))
            or not math.isclose(stored_score, snapshot.score, rel_tol=1e-12, abs_tol=1e-12)
        ):
            raise ValueError("stored aggregate does not match the reviewed scores and weights")
    except (KeyError, TypeError, ValidationError, ValueError) as error:
        raise ValueError(f"Experiment {experiment_id} contains invalid assurance data: {error}") from error
    return snapshot


def compare_assurance_experiments(
    client: Client, baseline_id: str, candidate_id: str
) -> AssuranceComparison:
    """Compare two complete, compatible reviewed experiments without modifying Phoenix."""
    baseline_run = client.experiments.get_experiment(experiment_id=baseline_id)
    candidate_run = client.experiments.get_experiment(experiment_id=candidate_id)
    if baseline_run["dataset_id"] != candidate_run["dataset_id"]:
        raise ValueError("Experiments are not comparable: datasets differ")
    if baseline_run["experiment_metadata"].get("rubric_version") != candidate_run["experiment_metadata"].get("rubric_version"):
        raise ValueError("Experiments are not comparable: rubric versions differ")
    baseline = _read_persisted_snapshot(client, baseline_run)
    candidate = _read_persisted_snapshot(client, candidate_run)
    baseline_by_id = {item.requirement_id: item for item in baseline.requirements}
    candidate_by_id = {item.requirement_id: item for item in candidate.requirements}
    if any(baseline_by_id[key].weight != candidate_by_id[key].weight for key in REQUIREMENT_IDS):
        raise ValueError("Experiments are not comparable: requirement weights differ")

    def review(item: RequirementAssessment) -> ReviewResult:
        return {
            "judgement": item.judgement,
            "score": JUDGEMENT_SCORES[item.judgement],
            "evidence_ref": item.evidence_ref,
            "explanation": item.explanation,
        }

    requirements: list[RequirementComparison] = []
    for requirement_id in REQUIREMENT_IDS:
        old = baseline_by_id[requirement_id]
        new = candidate_by_id[requirement_id]
        old_review, new_review = review(old), review(new)
        delta = new_review["score"] - old_review["score"]
        status: Literal["decreased", "unchanged", "increased"] = (
            "decreased" if delta < 0 else "increased" if delta > 0 else "unchanged"
        )
        requirements.append({
            "requirement_id": requirement_id,
            "weight": old.weight,
            "baseline": old_review,
            "candidate": new_review,
            "delta": delta,
            "status": status,
        })

    return {
        "rubric_version": baseline.rubric_version,
        "baseline": {
            "experiment_id": baseline_id,
            "commit": baseline.commit,
            "assessed_at": baseline.assessed_at.isoformat(),
            "score": baseline.score,
        },
        "candidate": {
            "experiment_id": candidate_id,
            "commit": candidate.commit,
            "assessed_at": candidate.assessed_at.isoformat(),
            "score": candidate.score,
        },
        "aggregate_delta": candidate.score - baseline.score,
        "decreased_requirements": [row["requirement_id"] for row in requirements if row["status"] == "decreased"],
        "requirements": requirements,
    }
