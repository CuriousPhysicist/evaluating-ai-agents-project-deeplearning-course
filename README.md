# Agent Evals

A command-line evaluation harness for a tool-using sales assistant. It records agent runs in local Phoenix, evaluates router and skill behavior separately, measures convergence across similar questions, and compares version results.

Project documentation (spec, QA reviews, design, progress records) lives in [docs/](docs/index.md) and is set up for GitHub Pages.
The [pre-refactor test harness snapshot](archive/pre-refactor-test-harness/README.md) is retained as historical QA evidence.

## Documentation preview

Install Ruby and Bundler separately from the Python environment, then run:

```powershell
cd docs
bundle install
bundle exec jekyll serve
```

Open `http://127.0.0.1:4000`. The remote theme requires internet access when building.
Pages load MathJax 3 from jsDelivr to render formulas; without CDN access,
the formulas remain as text.

### Documentation checks

The offline checks run with the normal pytest suite. To additionally check the
live CDN, rendered equations and page timings, install the documentation test
dependencies and a Playwright Chromium browser, then opt in:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[test,docs-test]"
.\.venv\Scripts\python.exe -m playwright install chromium
$env:DOCS_LIVE_TESTS = "1"
.\.venv\Scripts\python.exe -m pytest -o addopts="" -m docs_live tests\test_docs_math.py -s
Remove-Item Env:\DOCS_LIVE_TESTS
```

Run these commands from the repository root with Ruby and Bundler on `PATH`.
The live checks build the site and need access to GitHub and jsDelivr. The
timing check compares five cold browser loads of a maths page and a non-maths
page, through the browser load event and MathJax startup. It fails if the
maths-page median exceeds twice the non-maths median plus one second.
Different page content and network conditions also affect this comparison;
it is not an isolated MathJax benchmark or a comparison with an earlier build.

## Runtime inputs and migration

Runtime inputs live under `inputs/`: sample sales data in `data/`, question
sets in `datasets/`, and agent settings in `versions/`. Generated results
remain in `results/`.

When upgrading an existing workspace, manually reconcile any customised files
from the old root-level `data/`, `datasets/`, and `versions/` directories with
their matching locations under `inputs/`. Compare any existing destination
before replacing it, and move old copies to a backup outside those old
locations. No files are automatically copied, overwritten or deleted.

Setup reports an error if any of the five old default input files remain,
even when a new file already exists. Agent lookup, dataset upload and version
loading likewise report an error if the corresponding old input is still
present. Move or back it up after reconciling its contents before continuing.

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
      "evidence_ref": "docs/qa/QA_CHECK_2.md#t1",
      "explanation": "Example review rationale; replace with the actual evidence."
    }
  ]
}
```

This example is intentionally incomplete: add T2-T21 with their own reviewed
judgements, evidence references, explanations and positive finite weights.
For this inline format, supply the weights directly in the snapshot; the
separate-profile format is described below. The smallest must be at least
half the largest: no requirement can be weighted more than twice another.
For example, `0.5` and `1` are valid together, as are `1` and `2`; weights
are not restricted to an absolute 0-1 scale. Use weight `1` for every
requirement to reproduce the equal-weight comparisons.
The commit must be a full 40-character lowercase Git SHA, and the timestamp
must include a timezone. Both are supplied by the reviewer; the exporter
checks their format, not whether they correspond to the review or checkout.
Use the actual assessment time, not the commit time unless they coincide.

The supported `qa-evidence-v1` judgements are `not_covered` (0.00),
`indirectly_covered` (0.25), `partially_covered` (0.50), `mostly_covered`
(0.75) and `covered_completely` (1.00). Scores are derived from these labels,
not supplied separately. See `docs/qa/qa_refactor_plan.md` for the
rubric and `docs/qa/score_comparison_2.md` for reviewed examples.

```powershell
.\.venv\Scripts\python.exe -m agent_evals assurance --snapshot .\path\to\review.json
```

### Use a separate weight profile

Alternatively, remove `weight` from **every** requirement in the review
snapshot and supply a separate UTF-8 JSON object mapping each requirement ID
to its weight. For example, this complete profile gives T1 twice the weight
of each other requirement:

```json
{
  "T1": 2, "T2": 1, "T3": 1, "T4": 1, "T5": 1, "T6": 1, "T7": 1,
  "T8": 1, "T9": 1, "T10": 1, "T11": 1, "T12": 1, "T13": 1, "T14": 1,
  "T15": 1, "T16": 1, "T17": 1, "T18": 1, "T19": 1, "T20": 1, "T21": 1
}
```

```powershell
.\.venv\Scripts\python.exe -m agent_evals assurance --snapshot .\path\to\review-without-weights.json --weights .\path\to\weights.json
```

The profile must contain every T1-T21 ID exactly once, with no extras, and
satisfy the same positive, finite, 2:1 weight-ratio limit. Inline weights and
`--weights` cannot be combined, even when their values agree. Invalid or
conflicting inputs fail before Phoenix is contacted. The original review and
profile files are not changed.

The resolved weights are stored in the experiment, not a reference to the
profile file: editing the profile later does not change an existing result.
Keep or version the profile file separately if its name or provenance matters.
Different profiles can be applied to the same review for sensitivity analysis;
the comparison command still requires identical resolved weights.

### Export result

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
information in snapshots or evidence text.

## Compare reviewed snapshots

With the same local Phoenix server running, select an approved baseline and a
candidate experiment by the IDs returned when they were exported:

```powershell
.\.venv\Scripts\python.exe -m agent_evals assurance-compare --baseline <baseline-id> --candidate <candidate-id>
```

Replace the placeholders with actual IDs (without angle brackets). The
command reads existing experiments and prints a JSON report; it does not
start Phoenix, create an experiment, or add a dashboard panel. If Phoenix is
not running, or either experiment cannot be retrieved, the command fails.
It uses the same local endpoint configuration as the exporter, including
`PHOENIX_COLLECTOR_ENDPOINT` when set. Both IDs must refer to that server.

The report includes both commits and review times, weighted scores, the
aggregate change, and all 21 requirements with their individual changes,
weights, judgements, evidence references and explanations. Scores and deltas
use a 0-1 scale; multiply a delta by 100 for percentage points.
`decreased_requirements` identifies reviews that need attention even when
improvements elsewhere offset them in the aggregate. A decrease is a review
warning, not proof of a software regression, and does not by itself make the
command fail.

Both experiments must contain complete, consistent T1-T21 results from the
same assurance dataset, use the same supported rubric and identical
per-requirement weights. Both must also satisfy the current weight-ratio
limit, including experiments exported before the limit was introduced.
Previously exported experiments outside the limit remain stored in Phoenix
but cannot be compared by this command. Missing or inconsistent data, incompatible
experiments and connection errors are reported as errors. The comparison
does not verify that a commit matches the code reviewed, infer judgements,
run tests, or report test outcomes. Review snapshots against their respective
revisions and assess test passes, failures and skips separately.