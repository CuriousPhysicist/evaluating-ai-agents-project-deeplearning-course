# Agent Evals

A command-line evaluation harness for a tool-using sales assistant. It records agent runs in local Phoenix, evaluates router and skill behavior separately, measures convergence across similar questions, and compares version results.

## Install

From PowerShell in this folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m agent_evals setup
```

Setup writes the sample Parquet table, fixed test sets, version files, and results directory if they are missing. It starts Phoenix locally when needed and uploads both datasets. The Phoenix page is available at `http://127.0.0.1:6006`; its persistent database is stored in the user's Phoenix data directory.

## Run

Set `OPENAI_API_KEY` in the environment or an ignored `.env` file before making live model calls. The agent uses `gpt-4o-mini`; judges use `gpt-4o`.

```powershell
.\.venv\Scripts\python.exe -m agent_evals ask "Which store had the highest total sales value?"
.\.venv\Scripts\python.exe -m agent_evals evaluate --version v1
.\.venv\Scripts\python.exe -m agent_evals evaluate --version v2
.\.venv\Scripts\python.exe -m agent_evals compare
.\.venv\Scripts\python.exe -m pytest -m "not live"
```

Each evaluation writes `results/<version>.json`. Generated chart code is checked in a temporary working directory with a time limit; the agent itself never executes generated code.