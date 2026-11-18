# Import block:
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import pandas as pd

# Definition of constants and global variables:
ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROWS = [
    (1320, 6200700, "2021-11-01", 2, 10.00, 1),
    (1320, 6200800, "2021-11-01", 1, 4.50, 0),
    (2970, 6200700, "2021-11-02", 3, 15.00, 1),
    (2970, 6201000, "2021-11-02", 1, 20.00, 0),
    (880, 6200800, "2021-11-15", 2, 9.00, 0),
    (2970, 6200700, "2021-11-20", 4, 20.00, 0),
    (1320, 6201000, "2021-12-01", 1, 20.00, 1),
    (880, 6200700, "2021-12-05", 1, 5.00, 0),
    (2970, 6200800, "2021-12-10", 2, 9.00, 0),
    (1320, 6200700, "2021-12-20", 2, 10.00, 0),
]
OVERALL_CASES = [
    ("Which product SKU sold the most units?", "SELECT SKU_Coded, SUM(Qty_Sold) AS Total_Qty FROM sales GROUP BY SKU_Coded ORDER BY Total_Qty DESC LIMIT 1"),
    ("What was the total sales value across all stores?", "SELECT SUM(Total_Sale_Value) AS Total_Sales FROM sales"),
    ("Which store had the highest total sales value?", "SELECT Store_Number, SUM(Total_Sale_Value) AS Total_Sales FROM sales GROUP BY Store_Number ORDER BY Total_Sales DESC LIMIT 1"),
    ("Make a bar chart of total sales value by store", "SELECT Store_Number, SUM(Total_Sale_Value) AS Total_Sales FROM sales GROUP BY Store_Number ORDER BY Store_Number"),
    ("What share of transactions had a promotion?", "SELECT 100.0 * SUM(On_Promo) / COUNT(*) AS Promotion_Percentage FROM sales"),
    ("What was the average value of a transaction?", "SELECT AVG(Total_Sale_Value) AS Average_Sale FROM sales"),
    ("Draw a line chart of monthly sales value in 2021", "SELECT MONTH(Sold_Date) AS Month, SUM(Total_Sale_Value) AS Total_Sales FROM sales WHERE YEAR(Sold_Date) = 2021 GROUP BY Month ORDER BY Month"),
]
SIMILAR_QUESTIONS = [
    "What was the mean number of units per transaction?",
    "On average, how many units are in one transaction?",
    "How many items does one sale contain on average?",
    "Work out the usual quantity in a transaction",
    "How many units does a customer buy per transaction on average?",
    "What's the average basket size in units?",
]
SQL_PROMPT = "Generate an SQL query based on a prompt. Do not reply with anything besides the SQL query."


def _write_json_if_missing(path: Path, value: object) -> None:
    """Create parent directories and write indented JSON if the file is absent."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def setup() -> None:
    """Create the sample data, datasets, and version files, then upload test sets to Phoenix."""
    data_path = ROOT / "data" / "sample_sales.parquet"
    if not data_path.exists():
        data_path.parent.mkdir(parents=True, exist_ok=True)
        frame = pd.DataFrame(
            SAMPLE_ROWS,
            columns=["Store_Number", "SKU_Coded", "Sold_Date", "Qty_Sold", "Total_Sale_Value", "On_Promo"],
        )
        frame["Sold_Date"] = pd.to_datetime(frame["Sold_Date"]).dt.date
        frame.to_parquet(data_path, index=False)

    overall_path = ROOT / "datasets" / "overall_questions.json"
    if not overall_path.exists():
        frame = pd.read_parquet(data_path)
        with duckdb.connect() as connection:
            connection.register("sample_sales", frame)
            connection.execute("CREATE TABLE sales AS SELECT * FROM sample_sales")
            cases = [
                {
                    "question": question,
                    "sql_generated": sql,
                    "sql_result": connection.execute(sql).df().to_string(index=False),
                }
                for question, sql in OVERALL_CASES
            ]
        _write_json_if_missing(overall_path, cases)

    _write_json_if_missing(
        ROOT / "datasets" / "convergence_questions.json",
        [{"question": question} for question in SIMILAR_QUESTIONS],
    )
    _write_json_if_missing(ROOT / "versions" / "v1.json", {"name": "v1"})
    _write_json_if_missing(
        ROOT / "versions" / "v2.json",
        {"name": "v2", "overrides": {"sql_generation_prompt": SQL_PROMPT + "\nThink before you respond."}},
    )
    (ROOT / "results").mkdir(exist_ok=True)
    from .recording import ensure_phoenix, upload_testsets

    client = ensure_phoenix()
    names = upload_testsets(client, ROOT)
    print(f"Uploaded Phoenix datasets: {names[0]}, {names[1]}")


def main() -> None:
    """Parse CLI arguments and dispatch to the requested command."""
    parser = argparse.ArgumentParser(prog="python -m agent_evals")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("setup")
    ask_parser = subparsers.add_parser("ask")
    ask_parser.add_argument("question")
    ask_parser.add_argument("--version", default="v1")
    evaluate_parser = subparsers.add_parser("evaluate")
    evaluate_parser.add_argument("--version", required=True)
    subparsers.add_parser("compare")
    args = parser.parse_args()
    if args.command == "setup":
        setup()
    elif args.command == "ask":
        from .agent import run_agent
        from .recording import ensure_phoenix

        ensure_phoenix()
        record = run_agent(args.question, args.version)
        print(record["final_output"])
    elif args.command == "evaluate":
        from .experiments import evaluate_version
        from .recording import ensure_phoenix

        client = ensure_phoenix()
        evaluate_version(args.version, client)
    elif args.command == "compare":
        from .experiments import print_comparison

        print_comparison(ROOT)

# Entry point for the script: guard to ensure that the main function is called when the script is executed directly.
if __name__ == "__main__":
    main()