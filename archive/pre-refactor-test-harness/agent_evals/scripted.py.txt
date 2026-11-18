"""Scripted stand-in provider used for offline evaluation tests."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from .__main__ import OVERALL_CASES, SQL_PROMPT

FINAL_ANSWERS = {
    "Which product SKU sold the most units?": "SKU 6200700 sold the most units, 12 in total.",
    "What was the total sales value across all stores?": "Total sales value across all stores was 122.50.",
    "Which store had the highest total sales value?": "Store 2970 had the highest total sales value.",
    "Make a bar chart of total sales value by store": "Here is the code for a bar chart of total sales value by store:",
    "What share of transactions had a promotion?": "30% of transactions had a promotion.",
    "What was the average value of a transaction?": "The average transaction value was 12.25, at store 6200700.",
    "Draw a line chart of monthly sales value in 2021": "Sales went up and down, see chart.",
}
SIMILAR_QUESTIONS = [
    "What was the mean number of units per transaction?",
    "On average, how many units are in one transaction?",
    "How many items does one sale contain on average?",
    "Work out the usual quantity in a transaction",
    "How many units does a customer buy per transaction on average?",
    "What's the average basket size in units?",
]
REFERENCE_SQL = dict(OVERALL_CASES)
REFERENCE_SQL.update({question: "SELECT AVG(Qty_Sold) AS Average_Qty FROM sales" for question in SIMILAR_QUESTIONS})


def _call(name: str, arguments: dict[str, Any], call_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


class ScriptedProvider:
    """Deterministic model stand-in that reproduces the spec's planted outcomes."""

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        json_mode: bool = False,
    ) -> Any:
        prompt = "\n".join(str(message.get("content", "")) for message in messages)
        user_question = next(
            (str(message.get("content", "")) for message in messages if message.get("role") == "user"),
            "",
        )

        if tools:
            router_step = sum(bool(message.get("tool_calls")) for message in messages) + 1
            previous_tools = [message for message in messages if message.get("role") == "tool"]
            if user_question.startswith("Keep looking up sales"):
                return SimpleNamespace(
                    content=None,
                    tool_calls=[_call("lookup_sales_data", {"prompt": user_question}, "loop-call")],
                )
            if user_question == "What's the average basket size in units?":
                raise RuntimeError("Scripted provider error")
            if user_question == "Hello":
                return SimpleNamespace(content="Hi! Ask me about store sales.", tool_calls=[])
            if user_question == "Show data and analysis together":
                if router_step == 1:
                    return SimpleNamespace(
                        content=None,
                        tool_calls=[
                            _call("lookup_sales_data", {"prompt": user_question}, "p-lookup"),
                            _call("analyze_sales_data", {"prompt": user_question, "data": ""}, "p-analysis"),
                        ],
                    )
                return SimpleNamespace(content="Done.", tool_calls=[])
            if user_question == "Analyze nothing":
                if router_step == 1:
                    return SimpleNamespace(
                        content=None,
                        tool_calls=[_call("analyze_sales_data", {"prompt": user_question, "data": "x"}, "e-analysis")],
                    )
                return SimpleNamespace(content="Nothing to report.", tool_calls=[])
            if user_question in SIMILAR_QUESTIONS:
                if router_step == 1 or (user_question == SIMILAR_QUESTIONS[4] and router_step == 2):
                    return SimpleNamespace(
                        content=None,
                        tool_calls=[_call("lookup_sales_data", {"prompt": user_question}, f"k-{router_step}")],
                    )
                return SimpleNamespace(content="The average is 1.9 units per transaction.", tool_calls=[])
            if user_question == "What share of transactions had a promotion?" and router_step == 1:
                return SimpleNamespace(
                    content=None,
                    tool_calls=[
                        _call("analyze_sales_data", {"prompt": user_question, "data": ""}, "o5-wrong-tool")
                    ],
                )
            if router_step == 1:
                return SimpleNamespace(
                    content=None,
                    tool_calls=[_call("lookup_sales_data", {"prompt": user_question}, "lookup")],
                )
            if router_step == 2:
                if user_question in {
                    "Make a bar chart of total sales value by store",
                    "Draw a line chart of monthly sales value in 2021",
                }:
                    return SimpleNamespace(
                        content=None,
                        tool_calls=[
                            _call(
                                "generate_visualization",
                                {"data": previous_tools[-1]["content"], "visualization_goal": user_question},
                                "visualize",
                            )
                        ],
                    )
                return SimpleNamespace(
                    content=None,
                    tool_calls=[
                        _call(
                            "analyze_sales_data",
                            {"prompt": user_question, "data": previous_tools[-1]["content"]},
                            "analyze",
                        )
                    ],
                )
            final = FINAL_ANSWERS.get(user_question, "Done.")
            if user_question == "What was the total sales value across all stores?" and any(
                message.get("content", "").startswith("Error accessing data:") for message in previous_tools
            ):
                final = "I could not retrieve the total sales value because the query failed."
            if user_question == "Make a bar chart of total sales value by store" and previous_tools:
                final += "\n" + previous_tools[-1]["content"]
            return SimpleNamespace(content=final, tool_calls=[])

        if prompt.startswith("Judge whether this tool call"):
            if "analyze_sales_data" in prompt and "'data': ''" in prompt:
                    return SimpleNamespace(content="incorrect\nScripted reason.", tool_calls=[])
            if "What was the total sales value across all stores?" in prompt:
                return SimpleNamespace(content="Correct!\nScripted reason.", tool_calls=[])
            return SimpleNamespace(content="correct\nScripted reason.", tool_calls=[])
        if prompt.startswith("Is the answer"):
            label = "unclear" if "Sales went up and down, see chart." in prompt else "clear"
            return SimpleNamespace(content=f"{label}\nScripted reason.", tool_calls=[])
        if prompt.startswith("Are all entities"):
            label = "incorrect" if "at store 6200700" in prompt else "correct"
            return SimpleNamespace(content=f"{label}\nScripted reason.", tool_calls=[])
        if json_mode:
            if "bar chart of total sales value by store" in prompt:
                config = {"chart_type": "bar", "x_axis": "Store_Number", "y_axis": "Total_Sales", "title": "Total sales value by store"}
            elif "line chart of monthly sales value in 2021" in prompt:
                config = {"chart_type": "line", "x_axis": "Month", "y_axis": "Total_Sales", "title": "Monthly sales value in 2021"}
            elif "odd chart" in prompt:
                return SimpleNamespace(content="unreadable config", tool_calls=[])
            else:
                config = {"chart_type": "line", "x_axis": "date", "y_axis": "value", "title": "chart"}
            return SimpleNamespace(content=json.dumps(config), tool_calls=[])
        if "Generate an SQL query" in prompt:
            question = next((question for question in REFERENCE_SQL if question in prompt), "")
            sql = REFERENCE_SQL.get(question, "SELECT SUM(Total_Sale_Value) FROM sales")
            if question == "Which product SKU sold the most units?":
                sql = f"```sql\n{sql}\n```"
            elif question == "Which store had the highest total sales value?":
                sql = "SELECT Store_Number, SUM(Qty_Sold) AS Total_Qty FROM sales GROUP BY Store_Number ORDER BY Total_Qty DESC LIMIT 1"
            elif question == "What was the total sales value across all stores?" and "Think before you respond." in prompt:
                sql = "Let me think step by step. " + sql
            return SimpleNamespace(content=sql, tool_calls=[])
        if "Write Python code that draws a chart" in prompt:
            if "Total sales value by store" in prompt:
                code = "print(totals_by_store)"
                return SimpleNamespace(content=f"```python\n{code}\n```", tool_calls=[])
            if "Monthly sales value in 2021" in prompt:
                return SimpleNamespace(content="months = [11, 12]\nvalues = [78.5, 44.0]\nprint(list(zip(months, values)))", tool_calls=[])
            return SimpleNamespace(content='print("chart")', tool_calls=[])
        if messages and messages[0].get("content", "").startswith("Analyze the given data"):
            if "Analyze nothing" in prompt:
                return SimpleNamespace(content="", tool_calls=[])
            data = next((str(message.get("content", "")) for message in messages if message.get("role") == "user"), "")
            if "Data:\n\n" in data:
                return SimpleNamespace(content="No data was provided to analyze.", tool_calls=[])
            return SimpleNamespace(content="Analysis: " + data[:40], tool_calls=[])
        return SimpleNamespace(content="", tool_calls=[])