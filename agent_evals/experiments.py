from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from phoenix.client import Client

from .agent import AgentSettings, ChatProvider, OpenAIProvider, get_tool_definitions, run_agent
from .evaluators import (
    code_is_runnable,
    convergence_score,
    evaluate_final_answer_details,
    evaluate_sql_result,
    function_calling_evaluation,
)
from .recording import PROJECT_NAME
from .paths import resolve_root

EVALUATOR_NAMES = [
    "function_calling_eval",
    "evaluate_sql_result",
    "evaluate_clarity",
    "evaluate_entity_correctness",
    "code_is_runnable",
]


def _latest_dataset(client: Client, prefix: str):
    """Return the newest Phoenix dataset whose name begins with the given prefix.

    Raises:
        RuntimeError: If no matching dataset is found.
    """
    matches = [dataset for dataset in client.datasets.list() if dataset["name"].startswith(prefix)]
    if not matches:
        raise RuntimeError(f"No Phoenix dataset found with prefix {prefix!r}; run setup first")
    latest = max(matches, key=lambda dataset: dataset.get("created_at", ""))
    return client.datasets.get_dataset(dataset=latest["id"])


def _write_result(root: Path, version: str, result: dict[str, Any]) -> None:
    """Write a version's evaluation result to the results directory and track ordering.

    The JSON payload is saved under results/<version>.json and the
    evaluation_order.json file is updated so the results can be compared in the
    same sequence they were produced.
    """
    (root / "results").mkdir(exist_ok=True)
    target = root / "results" / f"{version}.json"
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    order_file = root / "results" / "evaluation_order.json"
    order = json.loads(order_file.read_text(encoding="utf-8")) if order_file.exists() else []
    if version in order:
        order.remove(version)
    order.append(version)
    order_file.write_text(json.dumps(order, indent=2) + "\n", encoding="utf-8")


def evaluate_version(
    version: str,
    client: Client,
    root: Path | None = None,
    provider: ChatProvider | None = None,
) -> dict[str, Any]:
    """Run the full evaluation pipeline for a single agent version.

    This loads the relevant dataset(s), executes the agent across all benchmark
    questions, scores overall and convergence metrics, writes the results to disk,
    and returns the aggregated summary for later comparison.
    """
    root = resolve_root(root)
    provider = provider or OpenAIProvider()
    version_settings = AgentSettings.load(version, root=root)
    judge_model = "gpt-4o"
    tool_definitions = get_tool_definitions(version_settings)
    overall_dataset = _latest_dataset(client, "overall_experiment_inputs-")
    questions = [example["input"]["question"] for example in overall_dataset.examples]
    overall_scores: dict[str, dict[str, float]] = {}
    records: dict[str, dict[str, Any]] = {}

    def task(input: dict[str, Any]) -> dict[str, Any]:
        """Run the agent for one question and store the resulting record by prompt."""
        question = str(input["question"])
        record = run_agent(question, version, provider=provider, root=root)
        records[question] = record
        return record

    def router_eval(output: dict[str, Any], input: dict[str, Any]) -> float:
        """Score the model's tool-calling behavior and save the result for the current question."""
        judgment = function_calling_evaluation(output, provider, judge_model, tool_definitions)
        value = judgment["score"]
        overall_scores.setdefault(input["question"], {})["function_calling_eval"] = value
        return judgment

    def sql_eval(output: dict[str, Any], expected: dict[str, Any], input: dict[str, Any]) -> float:
        """Evaluate whether the SQL output matches the expected result and log the score."""
        value = evaluate_sql_result(output, str(expected.get("sql_result", "")))
        overall_scores.setdefault(input["question"], {})["evaluate_sql_result"] = value
        return value

    def answer_eval(output: dict[str, Any], input: dict[str, Any]) -> list[dict[str, Any]]:
        """Score the final answer quality and merge those judgments into the overall result map."""
        judgments = evaluate_final_answer_details(output, provider, judge_model)
        overall_scores.setdefault(input["question"], {}).update(
            {name: judgment["score"] for name, judgment in judgments.items()}
        )
        return [
            {"name": name, **judgment}
            for name, judgment in judgments.items()
        ]

    def code_eval(output: dict[str, Any], input: dict[str, Any]) -> float:
        """Check whether the generated code executes successfully and save the result."""
        value = code_is_runnable(output)
        overall_scores.setdefault(input["question"], {})["code_is_runnable"] = value
        return value

    overall_run = client.experiments.run_experiment(
        dataset=overall_dataset,
        task=task,
        evaluators={
            "function_calling_eval": router_eval,
            "evaluate_sql_result": sql_eval,
            "answer_quality": answer_eval,
            "code_is_runnable": code_eval,
        },
        experiment_name=f"Overall Experiment {version}",
        print_summary=False,
        retries=0,
    )

    overall_cases = []
    for question in questions:
        score_map = overall_scores.get(question, {})
        failed = question not in records
        scores = {name: float(score_map.get(name, 0.0)) for name in EVALUATOR_NAMES}
        overall_cases.append({"question": question, "scores": scores, "failed": failed})
    means = {
        name: sum(case["scores"][name] for case in overall_cases) / len(overall_cases)
        if overall_cases
        else 0.0
        for name in EVALUATOR_NAMES
    }

    path_dataset = _latest_dataset(client, "convergence_questions-")
    path_questions = [example["input"]["question"] for example in path_dataset.examples]
    path_records: dict[str, dict[str, Any]] = {}

    def path_task(input: dict[str, Any]) -> dict[str, Any]:
        """Run the agent on a convergence question and cache the recorded path data."""
        question = str(input["question"])
        record = run_agent(question, version, provider=provider, root=root)
        path_records[question] = record
        return record

    path_run = client.experiments.run_experiment(
        dataset=path_dataset,
        task=path_task,
        experiment_name=f"Convergence Eval {version}",
        print_summary=False,
        retries=0,
    )
    lengths = [path_records[q]["path_length"] if q in path_records else None for q in path_questions]
    optimal, path_scores, path_mean = convergence_score(lengths)

    def path_eval(output: dict[str, Any]) -> float:
        """Convert a recovered path length into a convergence score relative to the optimal path."""
        length = output.get("path_length")
        return float(optimal / length) if optimal is not None and length else 0.0

    path_evaluation = client.experiments.evaluate_experiment(
        experiment=path_run,
        evaluators={"convergence": path_eval},
        print_summary=False,
        retries=0,
    )
    if not path_evaluation["evaluation_runs"]:
        raise RuntimeError(f"Phoenix did not store convergence scores for {version}")

    path_cases = [
        {
            "question": question,
            "path_length": lengths[index],
            "failed": lengths[index] is None,
            "score": path_scores[index],
        }
        for index, question in enumerate(path_questions)
    ]
    result = {
        "version": version,
        "evaluated_at": datetime.now().astimezone().isoformat(),
        "overall": {
            "experiment_name": f"Overall Experiment {version}",
            "experiment_id": overall_run["experiment_id"],
            "cases": overall_cases,
            "means": means,
        },
        "path": {
            "experiment_name": f"Convergence Eval {version}",
            "experiment_id": path_run["experiment_id"],
            "optimal_path_length": optimal,
            "cases": path_cases,
            "mean": path_mean,
        },
    }
    _write_result(root, version, result)
    print(f"Wrote {root / 'results' / f'{version}.json'}")
    return result


def print_comparison(root: Path) -> None:
    """Print a summary table comparing all saved evaluation results by version."""
    results_dir = root / "results"
    order_path = results_dir / "evaluation_order.json"
    order = json.loads(order_path.read_text(encoding="utf-8")) if order_path.exists() else []
    if not order:
        order = [path.stem for path in results_dir.glob("*.json") if path.stem != "evaluation_order"]
    columns = [
        "version",
        *EVALUATOR_NAMES,
        "convergence",
        "optimal path length",
        "failed runs",
    ]
    rows = []
    for version in order:
        path = results_dir / f"{version}.json"
        if not path.exists():
            continue
        result = json.loads(path.read_text(encoding="utf-8"))
        failed = sum(case["failed"] for case in result["overall"]["cases"])
        failed += sum(case["failed"] for case in result["path"]["cases"])
        rows.append(
            [
                version,
                *(f"{result['overall']['means'].get(name, 0):.2f}" for name in EVALUATOR_NAMES),
                f"{result['path']['mean']:.2f}",
                str(result["path"]["optimal_path_length"] or "-"),
                str(failed),
            ]
        )
    widths = [max([len(columns[index]), *(len(row[index]) for row in rows)]) for index in range(len(columns))]
    print(" | ".join(columns[index].ljust(widths[index]) for index in range(len(columns))))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(" | ".join(row[index].ljust(widths[index]) for index in range(len(columns))))
