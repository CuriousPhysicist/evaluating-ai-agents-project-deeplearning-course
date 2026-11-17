# QA Check 1, revised: Individual T Requirements vs. Historical Test Harness

## Scope and method

This is a more granular reassessment of [QA_CHECK_1](./QA_CHECK_1.md), not a
replacement for that historical document. It examines the archived harness
from commit `77483a50e596b0dc30cdb598627fb625691db7f6` against each T row
of the [specification](../evaluating-ai-agents-spec-62ab422.md). The archive
contains 11 offline tests and two live tests. The historical tests were
**inspected, not rerun**, for this review.

Scores use the rubric in [qa_refactor_plan.md](./qa_refactor_plan.md):
not covered = 0, indirectly covered = 0.25, partially covered = 0.5,
mostly covered = 0.75, and covered completely = 1. A direct assertion of
only one specified aspect can support a partial score; exercising a case or
returning a scripted value alone is not an assertion. Scores describe
coverage evidence, not test outcomes or the probability of correctness.

In the table, test names refer to the
[archived test harness](../old_test_files/tests/test_core.py.txt).
The [historical stand-in](../old_test_files/agent_evals/scripted.py.txt) and
[setup definitions](../old_test_files/agent_evals/__main__.py.txt) provide
context; their existence is not itself test coverage.

## Coverage by spec condition

| Condition | Closest test(s) | Assessment |
|---|---|---|
| **T1: Fresh setup** | `test_setup_creates_fixed_files_and_uploads_both_datasets` | **Partially covered — 0.50.** Directly checks ten rows, six columns, case counts, and unchanged dataset bytes after setup. It relies on files already at the project root rather than an empty folder, and does not assert version files or the results directory. |
| **T2: Uploaded datasets** | `test_setup_creates_fixed_files_and_uploads_both_datasets` | **Partially covered — 0.50.** Checks the configured Phoenix project, dataset prefixes and counts, overall input/output keys, and O1 values. It does not assert the timestamp format, fixed project name independently, or O3 ground truth. |
| **T3: O1 record and messages** | `test_agent_records_tool_call_order_and_replies` | **Mostly covered — 0.75.** Checks tool-name order, first lookup response, final output, message roles, and length seven. It does not assert the exact lookup and analysis arguments or the analysis input. |
| **T4: Multiple calls in one reply** | None | **Not covered — 0.00.** The stand-in can produce the P scenario, but no test runs P and asserts both calls, replies, final output, and path length. |
| **T5: Tool-call/reply IDs** | `test_agent_records_tool_call_order_and_replies` and its `SimpleO1Provider` guard | **Partially covered — 0.50.** Before subsequent router replies, the guard checks that each preceding call ID appears among tool reply IDs. It does not assert exactly one reply per ID. |
| **T6: Clean SQL and successful lookup** | `test_agent_records_tool_call_order_and_replies` | **Partially covered — 0.50.** The provider supplies fenced O1 SQL and the test checks a lookup response containing `6200700`. It does not inspect the SQL passed to DuckDB or assert that it exactly matches the cleaned reference SQL. |
| **T7: v2 O2 lookup failure** | `test_lookup_error_and_empty_analysis_are_returned_as_tool_results`; `test_scripted_v1_and_v2_experiments_match_expected_scores` | **Indirectly covered — 0.25.** A standalone lookup error produces the expected prefix, and v2 is evaluated, but the test does not assert O2's v2 error response, continued final answer, or path length. |
| **T8: Empty analysis fallback** | `test_lookup_error_and_empty_analysis_are_returned_as_tool_results` | **Mostly covered — 0.75.** Directly checks the exact fallback from the analysis function with an empty provider reply. It does not run E through the agent and inspect the resulting tool response. |
| **T9: Visualization behavior** | `test_visualization_uses_fallback_config_for_unreadable_reply` | **Partially covered — 0.50.** Directly checks the odd-chart fallback fields and returned code. It does not assert O4's specific fence-free response or demonstrate agent non-execution. |
| **T10: Ten-call limit and failed run** | `test_agent_stops_after_configured_router_call_limit` | **Indirectly covered — 0.25.** Demonstrates limit exhaustion and an exception at three calls, but not the specified ten-call scenario or its failed-run reporting. |
| **T11: Nested O1 trace** | `test_agent_run_is_exported_as_nested_phoenix_spans` | **Partially covered — 0.50.** Checks the presence of agent, router, tool-handling, lookup, SQL, and model span names. It does not isolate a new trace or assert counts, hierarchy, SQL input, analysis span, or five model calls. |
| **T12: Judge traces and records** | `test_agent_records_tool_call_order_and_replies` | **Not covered — 0.00.** Although the O1 test asserts a length of seven, it does not evaluate that record or check judge prompts/spans after evaluation. No test checks judge exclusion. |
| **T13: Judge labels and explanations** | `test_router_judge_normalizes_labels_and_keeps_explanation` | **Partially covered — 0.50.** Directly checks `Correct!` normalization, its explanation, and the zero-score `maybe` reply. It does not inspect both stored O2 judgments, every stored label/explanation, or the judge prompts. |
| **T14: Router evaluator** | `test_scripted_v1_and_v2_experiments_match_expected_scores` | **Partially covered — 0.50.** Directly checks the specified rounded v1 mean of 0.93, but not the individual O1, O5, or HELLO scores. |
| **T15: SQL-result evaluator** | `test_lookup_evaluator_compares_digits_and_handles_skipped_tool`; `test_scripted_v1_and_v2_experiments_match_expected_scores` | **Partially covered — 0.50.** Directly checks a no-response record scores one and the v1 mean rounds to 0.86. It does not assert O1/O3/O4/O5 individually. |
| **T16: Clarity and entity scores** | `test_scripted_v1_and_v2_experiments_match_expected_scores` | **Partially covered — 0.50.** Directly checks both specified rounded v1 means, 0.86. It does not assert O7's clarity, O6's entity score, or the other individual scores. |
| **T17: Chart-code scores** | `test_scripted_v1_and_v2_experiments_match_expected_scores`; `test_chart_code_runs_in_temporary_directory_and_times_out` | **Partially covered — 0.50.** Directly checks the v1 chart mean rounds to 0.86 and tests generic runnable/failing code. It does not assert O4, O7, O1, or the missing-record score. |
| **T18: Chart-code timeout and isolation** | `test_chart_code_runs_in_temporary_directory_and_times_out` | **Indirectly covered — 0.25.** Checks an infinite loop scores zero with a one-second timeout and a child process lacks the API key. It does not measure the specified two-second case's elapsed time, test `escape.txt` containment, or run O7 after the timeout. |
| **T19: Convergence evaluation** | `test_convergence_score_excludes_failed_run_from_optimum`; `test_scripted_v1_and_v2_experiments_match_expected_scores` | **Partially covered — 0.50.** Directly checks v1 optimum 5 and rounded mean 0.79; a unit test also checks a failed path scores zero. It does not assert the specified K1–K6 lengths and scores individually. |
| **T20: Version experiments** | `test_scripted_v1_and_v2_experiments_match_expected_scores` | **Partially covered — 0.50.** Runs both versions and directly checks v2's rounded SQL mean of 0.71. It does not assert identical cases/repetitions, experiment names, the v2 prompt phrase, or O2/O3 scores individually. |
| **T21: Comparison table** | `test_scripted_v1_and_v2_experiments_match_expected_scores` | **Indirectly covered — 0.25.** Checks that output contains both version names, selected values, and ends in `1`; it does not establish exact columns, row order, or the values and failed counts in each row. |

## Evidence score and interpretation

With one equal weight per T requirement:

| Judgement | Requirements | Count | Contribution |
|---|---|---:|---:|
| Not covered | T4, T12 | 2 | 0.00 |
| Indirectly covered | T7, T10, T18, T21 | 4 | 1.00 |
| Partially covered | T1, T2, T5, T6, T9, T11, T13–T17, T19, T20 | 13 | 6.50 |
| Mostly covered | T3, T8 | 2 | 1.50 |
| Covered completely | None | 0 | 0.00 |

The resulting illustrative score is **9.00 / 21 × 100 = 42.86%**. The
judgements are review decisions, not measurements of the fraction of each
requirement satisfied; equal weighting also does not account for differences
in importance or the number of assertions within each T row.

This differs from the preliminary **45.24%** in
[score_comparison_1.md](./score_comparison_1.md). The reassessment applies
the distinction between indirect evidence and direct assertion separately
to every T row. Notably, T10, T18 and T21 are now indirect; T14 and T16 are
partial because their specified aggregate means are directly asserted; and
T8 is mostly covered because the exact function fallback is checked but
the E agent run is not. Those classifications are open to review; the
earlier comparison remains a historical preliminary calculation.

The historical setup test uses the real project root and Phoenix rather than
a fresh isolated test environment. This reduces confidence in its
repeatability and isolation; it does not by itself prove a test failed.

## Live checks

The historical harness also defines L1 and L2, excluded from the T-only
score. `test_live_agent_can_answer_store_lookup` asserts the required lookup
call and `2970` answer; `test_live_judges_return_allowed_labels_and_explanations`
checks allowed labels and non-empty explanations. They require an API key;
their execution status was not established by this static review.
