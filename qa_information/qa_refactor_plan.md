## Plan for the branch development.

### WHY: Reason for branch development.

A comparison of the test harness for this project in `core_tests.py` against the stated requirements in the original seed specification file `evaluating-ai-agents-spec-62ab422.md` has highlighted gaps of coverage.

This branch seeks to address this deficiency, in the process developing a suitable metric and evaluation loop which can be used to evasluate the level of specification alignment, and can help guid code refactoring and guard agains regression from this new position in future iterations of the code.

### Desired Outcomes

-  _A metric has been developed which adequately measures the degree of alignment between the stated requirements from the spec file and the observed consequences of the test suite._ **☐**
-  _The evaluation of the metric is automated to a sufficient degree to enable reliable and repeatable measurement of the performance level._ **☐**
-  _The test suite has been refactored and extended to capture the metric and the resultant code changes to meet the original requiements._ **☐**


### Action List:
- Develop Metric
- Set metric stardards
- Refactor test suite  

#### Metric development

Key considerations in developing the metrics for assessing Spec Assurance:

- Qualitative statements about the evidence of specification coverage should be limited to a small set. For example `Not Verified, Partially Verified, Indirectly verified, Directly Verified`
- Evidence scores can be asigned to these judgements to convert into a numeric value for evaluation asa a metric.
- A weighted sum of the evidence values can be used to provide either a fractional or % based measure of the level of assurance that specication requirements have been met.

$$
SpecAssurance (\%) =100\times\frac{\Sigma(Weight_i\times EvidenceScore_i)}{\Sigma Weight_i}
$$
- Test coverage metrics and test outcome metrics must be kept seperate.

_other considerations:_
- Report skipped live tests separately to stop the coverage score looking strong while actually hiding failing or unexecuted tests.

#### Root-path injection for isolated tests

To keep setup and agent tests from reading or writing repository data, use one
shared `DEFAULT_ROOT` with an optional `root` argument at filesystem
boundaries. `setup`, `AgentSettings.load`, `run_agent`,
`lookup_sales_data`, and `evaluate_version` accept and pass through this root;
omitting it preserves the normal CLI behavior. A shared resolver selects the
provided path or the repository default.

Tests can pass a pytest temporary directory to `setup` and `run_agent`. The
setup function also accepts an optional recording client, so filesystem tests
can use a small fake client rather than start Phoenix. A `TemporaryDirectory`
fixture can remove the test root after each test. Phoenix server state is
external to this directory and should be tested separately or via an injected
client.

The root seam is implemented in `agent_evals/paths.py` and is exercised by
`test_setup_and_agent_use_injected_temporary_root`. The default-root path
remains available to the CLI.

#### Isolated Phoenix test backend

Phoenix-backed tests use a session-scoped fixture that starts a local server
on an available loopback port, stores its SQLite database and log in pytest's
temporary directory, and creates the spec-required `evaluating-agent` project.
The project name can be fixed because each pytest process uses its own server
and database. The fixture passes its client and tracing destination
explicitly, waits for the server to become ready, flushes tracing, stops the
exact server process, and removes the temporary directory during teardown.
External resources and unrelated API credentials are not passed to the test
server.

Tracing registration is now associated with its endpoint/project pair. It is
performed once per process; a later request to silently switch destinations
raises an error. Phoenix tests inspect only spans created after their own
snapshot and use the isolated client for dataset and experiment operations.
This keeps persisted traces and datasets out of the user's normal Phoenix
instance. After implementing the first four test batches, the offline suite
passes 35 tests with two live tests deselected.

#### Focused T1–T21 test batches

Implement the proposed tests in batches that share test seams and behavior:

1. **T1–T2 — setup and uploaded datasets — implemented:** covered by eight
   focused tests in `tests/test_setup_spec.py`, using temporary project roots
   and the isolated Phoenix backend.
2. **T3–T5 — agent protocol and run records — implemented:** eight focused
   tests cover exact tool arguments, run records, multi-call ordering, and
   exactly one reply per tool-call ID.
3. **T6–T9 — tool behavior — implemented:** nine focused tests cover SQL
   fence removal and lookup errors, analysis fallback, chart configuration,
   returned code, and non-execution.
4. **T10 — router-call limit — agent-level check implemented:** verify the
   agent stops at ten calls and returns no completed record; experiment-level
   failure accounting is covered with T19–T21.
5. **T11–T13 — traces and judges — implemented and accepted:** trace
   structure and SQL input, judge-trace exclusion, and stored judge labels
   and explanations.
6. **T14–T17 — evaluator scoring — implemented and accepted:** planted
   per-case scores, missing-tool semantics, and aggregate means.
7. **T18 — generated-code isolation — implemented and accepted:**
   subprocess timeout, working-directory containment, and recovery after a
   timed-out run.
8. **T19–T21 — experiments and comparison — implemented and accepted:**
   convergence, versioned runs, result ordering, and exact comparison output.

This sequence keeps related setup, fixtures, and behavioral assertions
together while leaving slower or cross-cutting checks in distinct batches.
Keep T identifiers in test names or markers for spec traceability, but make
each test establish its own preconditions; tests must not rely on execution
order. In particular, T10's loop-limit behavior is distinct from its
experiment-level failure accounting, and T18 exercises a subprocess boundary
unlike the in-process evaluator checks.

Batch 5 removes the duplicate inner `lookup_sales_data` span and annotates
`execute_sql_query` with its fence-free SQL input. Its Phoenix tests assert
exact counts and parent/child relationships. A full v1 experiment uses an
instrumented OpenAI client with a mock HTTP transport and an in-memory span
exporter to prove judge calls are suppressed without making network requests;
the same experiment verifies prompt/record separation, unchanged O1 path
length, and the persisted O2 judgment label and explanation.

Batch 6 reuses the full scripted v1 experiment to assert evaluator results
for the planted O1/O3/O4/O5/O6/O7 cases and exact aggregate means. It also
checks the HELLO no-call router score, the specified missing-lookup behavior,
and the missing-record chart score without adding another experiment run.

Batch 7 separates the timeout, filesystem-containment, and post-timeout
recovery checks. It confirms the O7 chart code still runs after an infinite
loop is terminated and retains a separate check that generated code does not
inherit the project API key.

Batch 8 checks convergence cases and scores, then reuses the v1 run and
executes v2 once to verify task counts, stored experiment names, SQL prompt
differences, and planted SQL regressions. Comparison output is parsed to
assert columns, row order, values, and two-decimal formatting. The complete
offline suite now passes 65 tests; the two live tests remain deselected
because no API key is configured.

&nbsp;
---
###### _v1.8 Date: 13th Nov. 2026_