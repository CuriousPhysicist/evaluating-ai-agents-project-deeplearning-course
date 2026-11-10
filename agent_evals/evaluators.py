from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from typing import Any

from openinference.instrumentation import suppress_tracing

from .agent import ChatProvider


def _label(text: str, labels: tuple[str, str]) -> str | None:
    cleaned = re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", text.strip()).casefold()
    return next((label for label in labels if cleaned == label.casefold()), None)


def _judge(provider: ChatProvider, model: str, prompt: str, labels: tuple[str, str]) -> dict[str, Any]:
    with suppress_tracing():
        reply = provider.complete(model=model, messages=[{"role": "user", "content": prompt}])
    text = reply.content or ""
    label = _label(text.splitlines()[0] if text else "", labels)
    score = 1.0 if label == labels[0] else 0.0
    return {"score": score, "label": label or labels[1], "explanation": text.partition("\n")[2].strip()}


def function_calling_eval(record: dict[str, Any], provider: ChatProvider, judge_model: str, tools: list[dict[str, Any]]) -> float:
    return function_calling_evaluation(record, provider, judge_model, tools)["score"]


def function_calling_evaluation(
    record: dict[str, Any], provider: ChatProvider, judge_model: str, tools: list[dict[str, Any]]
) -> dict[str, Any]:
    calls = record.get("tool_calls", [])
    if not calls:
        return {"score": 0.0, "label": "incorrect", "explanation": "The run made no tool calls."}
    judgments = []
    for call in calls:
        prompt = (
            "Judge whether this tool call is correct for the question. A call is incorrect if its tool "
            "cannot answer the question, uses information not provided, or its arguments violate the tool definition. "
            "On the first line reply with exactly correct or incorrect. Explain on the second line.\n"
            f"Question: {record['question']}\nTool call: {call}\nTool definitions: {tools}"
        )
        judgments.append(_judge(provider, judge_model, prompt, ("correct", "incorrect")))
    score = sum(item["score"] for item in judgments) / len(judgments)
    explanations = [item["explanation"] for item in judgments if item["explanation"]]
    return {
        "score": score,
        "label": "correct" if score == 1 else "incorrect",
        "explanation": " ".join(explanations),
    }


def evaluate_sql_result(record: dict[str, Any] | None, expected: str) -> float:
    if record is None or not record.get("tool_responses"):
        return 1.0 if record is not None else 0.0
    response = next(
        (item["tool_response"] for item in record["tool_responses"] if item["tool_name"] == "lookup_sales_data"),
        None,
    )
    if response is None:
        return 1.0
    return float(re.sub(r"\D", "", response) == re.sub(r"\D", "", expected))


def evaluate_final_answer(record: dict[str, Any] | None, provider: ChatProvider, judge_model: str) -> dict[str, Any]:
    return {
        name: judgment["score"]
        for name, judgment in evaluate_final_answer_details(record, provider, judge_model).items()
    }


def evaluate_final_answer_details(
    record: dict[str, Any] | None, provider: ChatProvider, judge_model: str
) -> dict[str, dict[str, Any]]:
    if record is None:
        return {
            "evaluate_clarity": {"score": 0.0, "label": "unclear", "explanation": "The run failed."},
            "evaluate_entity_correctness": {
                "score": 0.0,
                "label": "incorrect",
                "explanation": "The run failed.",
            },
        }
    question = record["question"]
    answer = record["final_output"]
    clarity_prompt = (
        "Is the answer precise, coherent, and directly responsive, or is it ambiguous, poorly organized, "
        "or not effectively communicated? On the first line reply with exactly clear or unclear. Explain on the second line.\n"
        f"Question: {question}\nAnswer: {answer}"
    )
    entity_prompt = (
        "Are all entities (store, product, date, name) in the answer correctly named and appropriate to the "
        "question? On the first line reply with exactly correct or incorrect. Explain on the second line.\n"
        f"Question: {question}\nAnswer: {answer}"
    )
    return {
        "evaluate_clarity": _judge(provider, judge_model, clarity_prompt, ("clear", "unclear")),
        "evaluate_entity_correctness": _judge(provider, judge_model, entity_prompt, ("correct", "incorrect")),
    }


def code_is_runnable(record: dict[str, Any] | None, timeout_seconds: int = 30) -> float:
    if record is None:
        return 0.0
    response = next(
        (item["tool_response"] for item in record["tool_responses"] if item["tool_name"] == "generate_visualization"),
        None,
    )
    if response is None:
        return 1.0
    code = re.sub(r"^```(?:python)?\s*|\s*```$", "", response.strip(), flags=re.IGNORECASE)
    with tempfile.TemporaryDirectory(prefix="agent-evals-") as working_directory:
        environment = {
            key: value
            for key, value in os.environ.items()
            if key in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
        }
        environment["MPLBACKEND"] = "Agg"
        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-c", code],
                cwd=working_directory,
                env=environment,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return 0.0
    return float(completed.returncode == 0)


def convergence_score(path_lengths: list[int | None]) -> tuple[int | None, list[float], float]:
    completed = [length for length in path_lengths if length is not None]
    optimal = min(completed) if completed else None
    scores = [optimal / length if length is not None and optimal is not None else 0.0 for length in path_lengths]
    return optimal, scores, sum(scores) / len(scores) if scores else 0.0