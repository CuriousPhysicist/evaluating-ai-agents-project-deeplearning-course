from __future__ import annotations

import json
import re
from datetime import date, datetime

import pandas as pd
import pytest

from agent_evals.__main__ import setup


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


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_t01_setup_from_empty_root_creates_sample_table(tmp_path):
    assert list(tmp_path.iterdir()) == []

    setup(root=tmp_path, client=SetupClient())

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
    for column in ("Store_Number", "SKU_Coded", "Qty_Sold", "On_Promo"):
        assert pd.api.types.is_integer_dtype(sales[column])
    assert all(type(value) is date for value in sales["Sold_Date"])
    assert pd.api.types.is_float_dtype(sales["Total_Sale_Value"])
    assert set(sales["On_Promo"]) == {0, 1}


def test_t01_setup_creates_both_fixed_question_sets(tmp_path):
    setup(root=tmp_path, client=SetupClient())

    overall = _read_json(tmp_path / "datasets" / "overall_questions.json")
    convergence = _read_json(tmp_path / "datasets" / "convergence_questions.json")

    assert len(overall) == 7
    assert all(set(case) == {"question", "sql_generated", "sql_result"} for case in overall)
    assert all(
        all(isinstance(case[key], str) and case[key] for key in ("question", "sql_generated", "sql_result"))
        for case in overall
    )
    assert len(convergence) == 6
    assert all(set(case) == {"question"} for case in convergence)
    assert all(isinstance(case["question"], str) and case["question"] for case in convergence)


def test_t01_setup_creates_version_files_and_results_directory(tmp_path):
    setup(root=tmp_path, client=SetupClient())

    assert (tmp_path / "versions" / "v1.json").is_file()
    assert (tmp_path / "versions" / "v2.json").is_file()
    assert (tmp_path / "results").is_dir()


def test_t01_setup_does_not_overwrite_question_sets(tmp_path):
    client = SetupClient()
    setup(root=tmp_path, client=client)
    overall_path = tmp_path / "datasets" / "overall_questions.json"
    convergence_path = tmp_path / "datasets" / "convergence_questions.json"
    original_overall = overall_path.read_bytes()
    original_convergence = convergence_path.read_bytes()

    setup(root=tmp_path, client=client)

    assert overall_path.read_bytes() == original_overall
    assert convergence_path.read_bytes() == original_convergence


@pytest.fixture(scope="module")
def uploaded_test_sets(isolated_phoenix, tmp_path_factory):
    setup(
        root=tmp_path_factory.mktemp("t02-setup"),
        client=isolated_phoenix.client,
    )
    return isolated_phoenix


def _datasets_with_prefix(client, prefix: str) -> list[dict]:
    return [dataset for dataset in client.datasets.list() if dataset["name"].startswith(prefix)]


def _latest_dataset(client, prefix: str) -> dict:
    matches = _datasets_with_prefix(client, prefix)
    assert matches, f"No uploaded dataset found with prefix {prefix!r}"
    return max(matches, key=lambda dataset: str(dataset.get("created_at", "")))


def test_t02_setup_creates_named_project_and_two_datasets(uploaded_test_sets):
    client = uploaded_test_sets.client

    assert uploaded_test_sets.project_name == "evaluating-agent"
    assert client.projects.get(project_name="evaluating-agent")["name"] == "evaluating-agent"
    assert _datasets_with_prefix(client, "overall_experiment_inputs-")
    assert _datasets_with_prefix(client, "convergence_questions-")


def test_t02_dataset_names_have_required_timestamp(uploaded_test_sets):
    client = uploaded_test_sets.client
    named_sets = (
        ("overall_experiment_inputs-", _datasets_with_prefix(client, "overall_experiment_inputs-")),
        ("convergence_questions-", _datasets_with_prefix(client, "convergence_questions-")),
    )

    for prefix, datasets in named_sets:
        assert datasets
        for dataset in datasets:
            timestamp = dataset["name"][len(prefix) :]
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", timestamp)
            assert datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime(
                "%Y-%m-%d %H:%M:%S"
            ) == timestamp


def test_t02_overall_dataset_has_exact_schema_and_ground_truth(uploaded_test_sets):
    client = uploaded_test_sets.client
    dataset_info = _latest_dataset(client, "overall_experiment_inputs-")
    examples = client.datasets.get_dataset(dataset=dataset_info["id"]).examples

    assert len(examples) == 7
    assert all(set(example["input"]) == {"question"} for example in examples)
    assert all(set(example["output"]) == {"sql_result", "sql_generated"} for example in examples)
    by_question = {example["input"]["question"]: example for example in examples}
    o1 = by_question["Which product SKU sold the most units?"]["output"]["sql_result"]
    o3 = by_question["Which store had the highest total sales value?"]["output"]["sql_result"]
    assert "6200700" in o1 and "12" in o1
    assert "2970" in o3 and "64" in o3


def test_t02_convergence_dataset_contains_six_question_inputs(uploaded_test_sets):
    client = uploaded_test_sets.client
    dataset_info = _latest_dataset(client, "convergence_questions-")
    examples = client.datasets.get_dataset(dataset=dataset_info["id"]).examples

    assert len(examples) == 6
    assert all(set(example["input"]) == {"question"} for example in examples)
    assert all(example["output"] == {} for example in examples)
