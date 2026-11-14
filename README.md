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

## Export a reviewed Spec Assurance snapshot

The `assurance` command exports a **manual review**, not test execution results
or an automated assessment of coverage. Prepare a UTF-8 JSON file with an
assessment for each of T1 through T21 exactly once:

```json
{
  "rubric_version": "qa-evidence-v1",
  "commit": "0123456789abcdef0123456789abcdef01234567",
  "assessed_at": "2026-01-01T12:00:00Z",
  "requirements": [
    {
      "requirement_id": "T1",
      "judgement": "mostly_covered",
      "weight": 1,
      "evidence_ref": "qa_information/QA_CHECK_2.md#t1",
      "explanation": "Example review rationale; replace with the actual evidence."
    }
  ]
}
```

This example is intentionally incomplete: add T2-T21 with their own reviewed
judgements, evidence references, explanations and positive finite weights.
Use weight `1` for every requirement to reproduce the equal-weight comparisons.
The commit must be a full 40-character lowercase Git SHA, and the timestamp
must include a timezone. Both are supplied by the reviewer; the exporter
checks their format, not whether they correspond to the review or checkout.
Use the actual assessment time, not the commit time unless they coincide.

The supported `qa-evidence-v1` judgements are `not_covered` (0.00),
`indirectly_covered` (0.25), `partially_covered` (0.50), `mostly_covered`
(0.75) and `covered_completely` (1.00). Scores are derived from these labels,
not supplied separately. See `qa_information/qa_refactor_plan.md` for the
rubric and `qa_information/score_comparison_2.md` for reviewed examples.

```powershell
.\.venv\Scripts\python.exe -m agent_evals assurance --snapshot .\path\to\review.json
```

The command validates the snapshot before connecting to local Phoenix, then
prints the dataset and experiment IDs and the weighted score on a 0-1 scale.
Each invocation creates a separate experiment in the shared
`spec-assurance-t1-t21-v1` dataset. Its task outputs retain the individual
weight, evidence reference and explanation; evaluations retain the score,
label and explanation. Experiment metadata retains the commit, assessment
time, rubric and **weighted** aggregate. Phoenix's ordinary mean of the
individual scores is not the weighted aggregate if weights differ.

The exporter verifies the persisted experiment and fails explicitly if it is
incomplete or the shared dataset is incompatible. A failed export can leave
a partial experiment in Phoenix; retrying creates a new experiment rather
than replacing it. Avoid concurrent first-time exports to the same server.
The data persists in the local Phoenix database; do not include sensitive
information in snapshots or evidence text. This first pass does not check
regressions, infer judgements, run tests, or record test outcomes.