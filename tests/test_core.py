from __future__ import annotations

import json
import os
import time
from types import SimpleNamespace

import pandas as pd
import pytest
from dotenv import load_dotenv
from opentelemetry import trace

from agent_evals.agent import (
    AgentSettings,
    OpenAIProvider,
    analyze_sales_data,
    generate_visualization,
    lookup_sales_data,
    run_agent,
)
from agent_evals.evaluators import (
    code_is_runnable,
    convergence_score,
    evaluate_sql_result,
    evaluate_final_answer_details,
    function_calling_evaluation,
)
from agent_evals.__main__ import setup
from agent_evals.experiments import evaluate_version, print_comparison
from agent_evals.recording import ensure_phoenix
from agent_evals.scripted import ScriptedProvider

# block: test providers
class SimpleO1Provider:
    def __init__(self) -> None:
        self.router_calls = 0
        self.tool_replies: list[dict] = []
        self.executed_sql = ""

    def complete(self, *, model, messages, tools=None, json_mode=False):
        if tools:
            self.router_calls += 1
            previous_calls = [message for message in messages if message.get("tool_calls")]
            for assistant in previous_calls:
                reply_ids = {
                    message.get("tool_call_id")
                    for message in messages
                    if message.get("role") == "tool"
                }
                assert all(call["id"] in reply_ids for call in assistant["tool_calls"])
            question = next(message["content"] for message in messages if message["role"] == "user")
            if self.router_calls == 1:
                tool_call = SimpleNamespace(
                    id="call_lookup",
                    function=SimpleNamespace(
                        name="lookup_sales_data",
                        arguments=json.dumps({"prompt": question}),
                    ),
                )
                return SimpleNamespace(content=None, tool_calls=[tool_call])
            if self.router_calls == 2:
                last_tool = next(message["content"] for message in reversed(messages) if message["role"] == "tool")
                tool_call = SimpleNamespace(
                    id="call_analyze",
                    function=SimpleNamespace(
                        name="analyze_sales_data",
                        arguments=json.dumps({"prompt": question, "data": last_tool}),
                    ),
                )
                return SimpleNamespace(content=None, tool_calls=[tool_call])
            return SimpleNamespace(content="SKU 6200700 sold the most units, 12 in total.", tool_calls=[])

        prompt = "\n".join(str(message.get("content", "")) for message in messages)
        if "Generate an SQL query" in prompt:
            self.executed_sql = "SELECT SKU_Coded, SUM(Qty_Sold) AS Total_Qty FROM sales GROUP BY SKU_Coded ORDER BY Total_Qty DESC LIMIT 1"
            return SimpleNamespace(content=f"```sql\n{self.executed_sql}\n```", tool_calls=[])
        return SimpleNamespace(content="Analysis: 6200700 12", tool_calls=[])


class JudgeProvider:
    def __init__(self, content: str) -> None:
        self.content = content

    def complete(self, *, model, messages, tools=None, json_mode=False):
        return SimpleNamespace(content=self.content, tool_calls=[])


class ErrorProvider:
    def complete(self, *, model, messages, tools=None, json_mode=False):
        raise RuntimeError("scripted provider error")


class EmptyProvider:
    def complete(self, *, model, messages, tools=None, json_mode=False):
        return SimpleNamespace(content="", tool_calls=[])


class ChartFallbackProvider:
    def __init__(self) -> None:
        self.code_prompt = ""

    def complete(self, *, model, messages, tools=None, json_mode=False):
        if json_mode:
            return SimpleNamespace(content="unreadable config", tool_calls=[])
        self.code_prompt = messages[-1]["content"]
        return SimpleNamespace(content="```python\nprint('chart')\n```", tool_calls=[])


class LoopProvider:
    def __init__(self) -> None:
        self.router_calls = 0

    def complete(self, *, model, messages, tools=None, json_mode=False):
        if tools:
            self.router_calls += 1
            call = SimpleNamespace(
                id=f"call_{self.router_calls}",
                function=SimpleNamespace(
                    name="lookup_sales_data",
                    arguments=json.dumps({"prompt": "Keep looking up sales"}),
                ),
            )
            return SimpleNamespace(content=None, tool_calls=[call])
        return SimpleNamespace(content="SELECT 1", tool_calls=[])


class SetupDatasets:
    def __init__(self) -> None:
        self.created: list[dict] = []

    def list(self) -> list[dict]:
        return [{"name": item["name"]} for item in self.created]

    def create_dataset(self, *, name: str, examples: list[dict]) -> None:
        self.created.append({"name": name, "examples": examples})


class SetupClient:
    def __init__(self) -> None:
        self.datasets = SetupDatasets()


# block: core tests
def test_agent_records_tool_call_order_and_replies():
    provider = SimpleO1Provider()
    record = run_agent("Which product SKU sold the most units?", provider=provider)

    assert [call["name"] for call in record["tool_calls"]] == [
        "lookup_sales_data",
        "analyze_sales_data",
    ]
    assert record["tool_responses"][0]["tool_name"] == "lookup_sales_data"
    assert "6200700" in record["tool_responses"][0]["tool_response"]
    assert record["final_output"] == "SKU 6200700 sold the most units, 12 in total."
    assert [message["role"] for message in record["unchanged_messages"]] == [
        "user",
        "system",
        "assistant",
        "tool",
        "assistant",
        "tool",
        "assistant",
    ]
    assert record["path_length"] == 7
    assert provider.executed_sql.startswith("SELECT")


def test_lookup_evaluator_compares_digits_and_handles_skipped_tool():
    record = {"tool_responses": [{"tool_name": "lookup_sales_data", "tool_response": "6200700 12"}]}
    assert evaluate_sql_result(record, "6200700, 12") == 1
    assert evaluate_sql_result(record, "6200700, 10") == 0
    assert evaluate_sql_result({"tool_responses": []}, "12") == 1
    assert evaluate_sql_result(None, "12") == 0


def test_router_judge_normalizes_labels_and_keeps_explanation():
    record = {
        "question": "Look up total sales",
        "tool_calls": [{"name": "lookup_sales_data", "arguments": {"prompt": "Look up total sales"}}],
    }
    tools = [{"function": {"name": "lookup_sales_data"}}]
    correct = function_calling_evaluation(record, JudgeProvider("Correct!\nScripted reason."), "judge", tools)
    unmatched = function_calling_evaluation(record, JudgeProvider("maybe"), "judge", tools)

    assert correct == {"score": 1.0, "label": "correct", "explanation": "Scripted reason."}
    assert unmatched == {"score": 0.0, "label": "incorrect", "explanation": ""}


def test_lookup_error_and_empty_analysis_are_returned_as_tool_results():
    settings = AgentSettings.load("v1")
    assert lookup_sales_data("Look up sales", settings, ErrorProvider()).startswith("Error accessing data:")
    assert analyze_sales_data("", "Analyze nothing", settings, EmptyProvider()) == "No analysis could be generated"


def test_visualization_uses_fallback_config_for_unreadable_reply():
    provider = ChartFallbackProvider()
    code = generate_visualization("data", "odd chart", AgentSettings.load("v1"), provider)

    assert code == "print('chart')"
    assert '"chart_type": "line"' in provider.code_prompt
    assert '"x_axis": "date"' in provider.code_prompt
    assert '"y_axis": "value"' in provider.code_prompt
    assert '"title": "odd chart"' in provider.code_prompt


def test_agent_stops_after_configured_router_call_limit():
    provider = LoopProvider()
    with pytest.raises(RuntimeError, match="max_router_calls=3"):
        run_agent("Keep looking up sales", provider=provider, max_router_calls=3)
    assert provider.router_calls == 3


def test_convergence_score_excludes_failed_run_from_optimum():
    optimal, scores, mean = convergence_score([5, 5, 7, None])
    assert optimal == 5
    assert scores == [1, 1, 5 / 7, 0]
    assert round(mean, 2) == 0.68


def test_chart_code_runs_in_temporary_directory_and_times_out(monkeypatch):
    record = {"tool_responses": [{"tool_name": "generate_visualization", "tool_response": "print('ok')"}]}
    assert code_is_runnable(record, timeout_seconds=2) == 1
    looping = {"tool_responses": [{"tool_name": "generate_visualization", "tool_response": "while True: pass"}]}
    assert code_is_runnable(looping, timeout_seconds=1) == 0
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-key")
    no_secret = {
        "tool_responses": [
            {
                "tool_name": "generate_visualization",
                "tool_response": "import os; assert 'OPENAI_API_KEY' not in os.environ",
            }
        ]
    }
    assert code_is_runnable(no_secret, timeout_seconds=2) == 1


def test_setup_creates_fixed_files_and_uploads_both_datasets(tmp_path, isolated_phoenix):
    overall_path = tmp_path / "datasets" / "overall_questions.json"
    convergence_path = tmp_path / "datasets" / "convergence_questions.json"

    setup(root=tmp_path, client=isolated_phoenix.client)
    original_overall = overall_path.read_bytes()
    original_convergence = convergence_path.read_bytes()
    setup(root=tmp_path, client=isolated_phoenix.client)

    sales = pd.read_parquet(tmp_path / "data" / "sample_sales.parquet")
    assert len(sales) == 10
    assert list(sales.columns) == [
        "Store_Number",
        "SKU_Coded",
        "Sold_Date",
        "Qty_Sold",
        "Total_Sale_Value",
        "On_Promo",
    ]
    assert len(json.loads(overall_path.read_text(encoding="utf-8"))) == 7
    assert len(json.loads(convergence_path.read_text(encoding="utf-8"))) == 6
    assert overall_path.read_bytes() == original_overall
    assert convergence_path.read_bytes() == original_convergence

    client = isolated_phoenix.client
    assert isolated_phoenix.project_name == "evaluating-agent"
    assert client.projects.get(project_name="evaluating-agent")["name"] == "evaluating-agent"
    datasets = client.datasets.list()
    overall_sets = [item for item in datasets if item["name"].startswith("overall_experiment_inputs-")]
    convergence_sets = [item for item in datasets if item["name"].startswith("convergence_questions-")]
    assert overall_sets and overall_sets[-1]["example_count"] == 7
    assert convergence_sets and convergence_sets[-1]["example_count"] == 6

    uploaded_overall = client.datasets.get_dataset(dataset=overall_sets[-1]["id"])
    first = uploaded_overall.examples[0]
    assert set(first["input"]) == {"question"}
    assert set(first["output"]) == {"sql_result", "sql_generated"}
    assert "6200700" in first["output"]["sql_result"]
    assert "12" in first["output"]["sql_result"]


def test_setup_and_agent_use_injected_temporary_root(tmp_path):
    client = SetupClient()
    setup(root=tmp_path, client=client)

    assert (tmp_path / "data" / "sample_sales.parquet").exists()
    assert (tmp_path / "datasets" / "overall_questions.json").exists()
    assert (tmp_path / "datasets" / "convergence_questions.json").exists()
    assert (tmp_path / "versions" / "v1.json").exists()
    assert (tmp_path / "versions" / "v2.json").exists()
    assert (tmp_path / "results").is_dir()
    assert len(client.datasets.created) == 2

    record = run_agent(
        "Which product SKU sold the most units?",
        provider=ScriptedProvider(),
        root=tmp_path,
    )
    assert record["tool_responses"][0]["tool_name"] == "lookup_sales_data"
    assert "6200700" in record["tool_responses"][0]["tool_response"]


def _span_ids(spans):
    assert "context.span_id" in spans.columns, f"Unexpected span columns: {list(spans.columns)}"
    return set(spans["context.span_id"].astype(str))


def _spans_created_since(
    client,
    project_name,
    previous_span_ids,
    expected_names,
    minimum_model_calls=0,
):
    deadline = time.monotonic() + 15
    latest = None
    while time.monotonic() < deadline:
        spans = client.spans.get_spans_dataframe(project_name=project_name, limit=500)
        if not spans.empty:
            new_spans = spans.loc[~spans["context.span_id"].astype(str).isin(previous_span_ids)]
            latest = new_spans
            names = new_spans["name"].astype(str)
            if expected_names <= set(names) and (names == "model_call").sum() >= minimum_model_calls:
                return new_spans
        time.sleep(0.1)
    observed = set() if latest is None else set(latest["name"].astype(str))
    model_calls = 0 if latest is None else int((latest["name"].astype(str) == "model_call").sum())
    raise AssertionError(
        f"Phoenix did not export all expected spans; missing: {expected_names - observed}; "
        f"model calls: {model_calls}/{minimum_model_calls}"
    )


def test_agent_run_is_exported_as_nested_phoenix_spans(tmp_path, isolated_phoenix):
    setup(root=tmp_path, client=isolated_phoenix.client)
    client = isolated_phoenix.client
    previous_span_ids = _span_ids(
        client.spans.get_spans_dataframe(project_name=isolated_phoenix.project_name, limit=500)
    )
    run_agent(
        "Which product SKU sold the most units?",
        provider=SimpleO1Provider(),
        root=tmp_path,
    )
    trace.get_tracer_provider().force_flush(timeout_millis=10_000)
    expected = {"AgentRun", "router_call", "handle_tool_calls", "lookup_sales_data", "execute_sql_query"}
    spans = _spans_created_since(
        client,
        isolated_phoenix.project_name,
        previous_span_ids,
        expected,
        minimum_model_calls=5,
    )
    names = set(spans["name"].astype(str))
    assert expected <= names, f"Missing spans: {expected - names}; observed: {names}"
    assert (spans["name"].astype(str) == "model_call").sum() >= 5


def test_phoenix_rejects_tracing_destination_changes(isolated_phoenix):
    with pytest.raises(RuntimeError, match="different endpoint or project"):
        ensure_phoenix(
            base_url=isolated_phoenix.base_url,
            project_name="different-test-project",
        )


def test_scripted_v1_and_v2_experiments_match_expected_scores(capsys, tmp_path, isolated_phoenix):
    setup(root=tmp_path, client=isolated_phoenix.client)
    v1 = evaluate_version("v1", isolated_phoenix.client, root=tmp_path, provider=ScriptedProvider())
    v2 = evaluate_version("v2", isolated_phoenix.client, root=tmp_path, provider=ScriptedProvider())

    assert round(v1["overall"]["means"]["function_calling_eval"], 2) == 0.93
    assert round(v1["overall"]["means"]["evaluate_sql_result"], 2) == 0.86
    assert round(v1["overall"]["means"]["evaluate_clarity"], 2) == 0.86
    assert round(v1["overall"]["means"]["evaluate_entity_correctness"], 2) == 0.86
    assert round(v1["overall"]["means"]["code_is_runnable"], 2) == 0.86
    assert round(v1["path"]["mean"], 2) == 0.79
    assert v1["path"]["optimal_path_length"] == 5
    assert round(v2["overall"]["means"]["evaluate_sql_result"], 2) == 0.71
    assert round(v2["path"]["mean"], 2) == 0.79

    print_comparison(tmp_path)
    table = capsys.readouterr().out
    assert "v1" in table and "v2" in table
    assert "0.86" in table and "0.71" in table
    assert table.rstrip().endswith("1")

# block: live tests
load_dotenv()


@pytest.mark.live
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY is not configured")
def test_live_agent_can_answer_store_lookup():
    record = run_agent("Which store had the highest total sales value?")
    assert any(call["name"] == "lookup_sales_data" for call in record["tool_calls"])
    assert "2970" in record["final_output"]


@pytest.mark.live
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY is not configured")
def test_live_judges_return_allowed_labels_and_explanations():
    provider = OpenAIProvider()
    record = run_agent("Which product SKU sold the most units?")
    router = function_calling_evaluation(record, provider, "gpt-4o", [])
    answers = evaluate_final_answer_details(record, provider, "gpt-4o")

    assert router["label"] in {"correct", "incorrect"}
    assert router["explanation"]
    assert answers["evaluate_clarity"]["label"] in {"clear", "unclear"}
    assert answers["evaluate_clarity"]["explanation"]
    assert answers["evaluate_entity_correctness"]["label"] in {"correct", "incorrect"}
    assert answers["evaluate_entity_correctness"]["explanation"]
