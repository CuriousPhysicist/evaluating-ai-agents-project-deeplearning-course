from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import duckdb
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from opentelemetry import trace

ROOT = Path(__file__).resolve().parents[1]
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_sales_data",
            "description": "Look up data from the store sales dataset",
            "parameters": {
                "type": "object",
                "properties": {"prompt": {"type": "string", "description": "The unchanged prompt that the user provided."}},
                "required": ["prompt"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_sales_data",
            "description": "Analyze sales data to extract insights",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "The lookup_sales_data tool's output."},
                    "prompt": {"type": "string", "description": "The unchanged prompt that the user provided."},
                },
                "required": ["data", "prompt"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_visualization",
            "description": "Generate Python code to create data visualizations",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "The lookup_sales_data tool's output."},
                    "visualization_goal": {"type": "string", "description": "The goal of the visualization."},
                },
                "required": ["data", "visualization_goal"],
                "additionalProperties": False,
            },
        },
    },
]


class ChatProvider(Protocol):
    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        json_mode: bool = False,
    ) -> Any: ...


class OpenAIProvider:
    def __init__(self) -> None:
        load_dotenv()
        from openai import OpenAI

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        json_mode: bool = False,
    ) -> Any:
        kwargs: dict[str, Any] = {"model": model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        return self.client.chat.completions.create(**kwargs).choices[0].message


def _complete(provider: ChatProvider, **kwargs: Any) -> Any:
    with trace.get_tracer("agent_evals").start_as_current_span("model_call"):
        return provider.complete(**kwargs)


@dataclass
class AgentSettings:
    name: str
    agent_model: str = "gpt-4o-mini"
    system_prompt: str = "You are a helpful assistant that can answer questions about the store sales dataset."
    sql_generation_prompt: str = "Generate an SQL query based on a prompt. Do not reply with anything besides the SQL query."
    tool_descriptions: dict[str, str] | None = None

    @classmethod
    def load(cls, name: str) -> AgentSettings:
        path = ROOT / "versions" / f"{name}.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("name") != name or not re.fullmatch(r"[A-Za-z0-9_-]+", name):
            raise ValueError(f"Invalid version file: {path}")
        overrides = raw.get("overrides", {})
        result = cls(name=name)
        for key, value in overrides.items():
            if key == "tool_descriptions":
                result.tool_descriptions = value
            elif hasattr(result, key):
                setattr(result, key, value)
        return result


class ChartConfig(BaseModel):
    chart_type: str
    x_axis: str
    y_axis: str
    title: str


def _clean_fences(text: str, language: str) -> str:
    text = text.strip()
    return re.sub(rf"^```(?:{language})?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()


def get_tool_definitions(settings: AgentSettings) -> list[dict[str, Any]]:
    tools = json.loads(json.dumps(TOOL_DEFINITIONS))
    if settings.tool_descriptions:
        for tool in tools:
            name = tool["function"]["name"]
            if name in settings.tool_descriptions:
                tool["function"]["description"] = settings.tool_descriptions[name]
    return tools


# Skills / Tools block: these are the functions that the agent can call to perform specific tasks. Each function takes in a prompt and returns a string result. The agent will use these functions to look up data, analyze it, and generate visualizations based on user queries.
def lookup_sales_data(prompt: str, settings: AgentSettings, provider: ChatProvider) -> str:
    tracer = trace.get_tracer("agent_evals")
    with tracer.start_as_current_span("lookup_sales_data"):
        try:
            columns = ", ".join(pd.read_parquet(ROOT / "data" / "sample_sales.parquet").columns)
            sql_prompt = f"{settings.sql_generation_prompt}\n{prompt}\nAvailable columns: {columns}\nTable: sales"
            response = _complete(
                provider,
                model=settings.agent_model,
                messages=[{"role": "user", "content": sql_prompt}],
            )
            sql = _clean_fences(response.content or "", "sql")
            with tracer.start_as_current_span("execute_sql_query"):
                frame = pd.read_parquet(ROOT / "data" / "sample_sales.parquet")
                with duckdb.connect() as connection:
                    connection.register("sample_sales", frame)
                    connection.execute("CREATE TABLE sales AS SELECT * FROM sample_sales")
                    return connection.execute(sql).df().to_string(index=False)
        except Exception as error:
            return f"Error accessing data: {error}"


def analyze_sales_data(data: str, prompt: str, settings: AgentSettings, provider: ChatProvider) -> str:
    response = _complete(
        provider,
        model=settings.agent_model,
        messages=[
            {"role": "system", "content": "Analyze the given data and answer the given question."},
            {"role": "user", "content": f"Data:\n{data}\nQuestion:\n{prompt}"},
        ],
    )
    return response.content or "No analysis could be generated"


def generate_visualization(
    data: str, visualization_goal: str, settings: AgentSettings, provider: ChatProvider
) -> str:
    fallback = ChartConfig(chart_type="line", x_axis="date", y_axis="value", title=visualization_goal)
    config_response = _complete(
        provider,
        model=settings.agent_model,
        messages=[
            {"role": "user", "content": f"Return chart_type, x_axis, y_axis, and title for: {visualization_goal}\nData:\n{data}"}
        ],
        json_mode=True,
    )
    try:
        config = ChartConfig.model_validate_json(config_response.content or "")
    except (ValidationError, ValueError):
        config = fallback
    code_response = _complete(
        provider,
        model=settings.agent_model,
        messages=[
            {
                "role": "user",
                "content": "Write Python code that draws a chart from this config. Only return the code, no other text.\n"
                + json.dumps(config.model_dump())
                + f"\nData:\n{data}",
            }
        ],
    )
    return _clean_fences(code_response.content or "", "python")

# Main function to run the agent with a given question and version.
def run_agent(
    question: str,
    version: str = "v1",
    *,
    provider: ChatProvider | None = None,
    max_router_calls: int = 10,
) -> dict[str, Any]:
    settings = AgentSettings.load(version)
    provider = provider or OpenAIProvider()
    tools = get_tool_definitions(settings)
    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
    messages.append({"role": "system", "content": settings.system_prompt})
    calls: list[dict[str, Any]] = []
    responses: list[dict[str, str]] = []
    tracer = trace.get_tracer("agent_evals")
    with tracer.start_as_current_span("AgentRun"):
        for _ in range(max_router_calls):
            with tracer.start_as_current_span("router_call"):
                reply = _complete(provider, model=settings.agent_model, messages=messages, tools=tools)
            raw_calls = list(reply.tool_calls or [])
            assistant_message: dict[str, Any] = {"role": "assistant", "content": reply.content}
            if raw_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": item.id,
                        "type": "function",
                        "function": {"name": item.function.name, "arguments": item.function.arguments},
                    }
                    for item in raw_calls
                ]
            messages.append(assistant_message)
            if not raw_calls:
                final_output = reply.content or ""
                record = {
                    "question": question,
                    "tool_calls": calls,
                    "tool_responses": responses,
                    "final_output": final_output,
                    "unchanged_messages": messages,
                    "path_length": len(messages),
                }
                return record
            with tracer.start_as_current_span("handle_tool_calls"):
                for item in raw_calls:
                    name = item.function.name
                    arguments = json.loads(item.function.arguments or "{}")
                    calls.append({"name": name, "arguments": arguments})
                    with tracer.start_as_current_span(name):
                        if name == "lookup_sales_data":
                            result = lookup_sales_data(arguments["prompt"], settings, provider)
                        elif name == "analyze_sales_data":
                            result = analyze_sales_data(arguments["data"], arguments["prompt"], settings, provider)
                        elif name == "generate_visualization":
                            result = generate_visualization(
                                arguments["data"], arguments["visualization_goal"], settings, provider
                            )
                        else:
                            result = f"Error: unknown tool {name}"
                    responses.append({"tool_name": name, "tool_response": result})
                    messages.append({"role": "tool", "tool_call_id": item.id, "name": name, "content": result})
    raise RuntimeError(f"Agent exceeded max_router_calls={max_router_calls}")
