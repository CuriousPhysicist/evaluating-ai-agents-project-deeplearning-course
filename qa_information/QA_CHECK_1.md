# QA Check 1: Spec Requirements vs. Test Harness

## Summary

The spec defines 21 offline conditions (T1–T21) and two live conditions (L1–L2). The current `tests/test_core.py` file contains 11 offline tests and two live tests. The counts differ because some tests cover multiple conditions, often only partially.

## Coverage by Spec Condition

| Condition | Closest test(s) | Assessment |
|---|---|---|
| **T1–T2: Setup and uploaded datasets** | `test_setup_creates_fixed_files_and_uploads_both_datasets` | **Partial.** Checks sample table shape, question counts, test-set stability across two setup calls, Phoenix project, dataset prefixes/counts, and some O1 fields. Does not start from an empty temporary folder, assert version files or results directory, validate dataset-name timestamps, or check O3’s expected result. |
| **T3: Agent record and message sequence** | `test_agent_records_tool_call_order_and_replies` | **Mostly covered.** Checks tool order, lookup response, final answer, message roles, and path length. Does not assert exact tool arguments or that the analysis call received the lookup text. |
| **T4: Multiple tool calls in one reply** | None | **Not covered.** No test verifies that both calls run in order and get tool messages. |
| **T5: Tool-call/reply ID matching** | `test_agent_records_tool_call_order_and_replies` | **Partial.** The stand-in checks that prior call IDs have replies before the next router call, but checks membership rather than exactly one reply per ID. |
| **T6–T7: SQL cleanup and lookup failure** | `test_agent_records_tool_call_order_and_replies`; `test_lookup_error_and_empty_analysis_are_returned_as_tool_results` | **Partial.** T6 sends fenced SQL and confirms SQL execution starts, but does not assert the cleaned query or successful lookup result exactly. The second test checks a lookup error is returned, but not the v2 O2 end-to-end behavior required by T7. |
| **T8: Empty analysis response** | `test_lookup_error_and_empty_analysis_are_returned_as_tool_results` | **Covered** for the expected fallback string. |
| **T9: Visualization behavior** | `test_visualization_uses_fallback_config_for_unreadable_reply` | **Partial.** Checks fallback config fields for an unreadable chart-config reply. Does not test O4’s generated code, fence removal, or that the agent leaves the code unexecuted. |
| **T10: Router-call limit and failed run** | `test_agent_stops_after_configured_router_call_limit` | **Partial.** Verifies the configured limit works with a limit of 3; does not verify the spec’s limit of 10 or that the experiment records the run as failed with no record. |
| **T11: Nested Phoenix trace** | `test_agent_run_is_exported_as_nested_phoenix_spans` | **Partial.** Checks for key span names, but not expected counts, hierarchy, SQL input, or minimum model-call count. |
| **T12: Judge calls excluded from agent traces** | None | **Not covered.** |
| **T13: Judge labels, prompts, and explanations** | `test_router_judge_normalizes_labels_and_keeps_explanation`; `test_live_judges_return_allowed_labels_and_explanations` | **Partial.** Checks case/punctuation normalization and a non-matching reply’s zero score. The live test checks allowed labels and non-empty explanations. Neither checks judge prompt requirements or stored O2 evaluations in detail. |
| **T14: Router evaluator scores** | `test_scripted_v1_and_v2_experiments_match_expected_scores` | **Partial.** Asserts the aggregate v1 mean (0.93), not the specified O5/O1/HELLO per-case scores. |
| **T15: SQL-result evaluator** | `test_lookup_evaluator_compares_digits_and_handles_skipped_tool`; `test_scripted_v1_and_v2_experiments_match_expected_scores` | **Partial.** Unit test covers digit comparison and missing responses; integration asserts the aggregate mean. Does not assert the specified individual O1/O3/O4/O5 scores. |
| **T16: Clarity and entity scores** | `test_scripted_v1_and_v2_experiments_match_expected_scores` | **Partial.** Checks each aggregate mean, but not O7’s clarity and O6’s entity score individually. |
| **T17–T18: Chart-code evaluator and isolation** | `test_chart_code_runs_in_temporary_directory_and_times_out`; `test_scripted_v1_and_v2_experiments_match_expected_scores` | **Partial.** Checks runnable code, a timeout, and that the API key is absent from the child process; integration checks the aggregate. Does not test the spec’s `escape.txt` containment case, missing-record score, or O7’s score explicitly. |
| **T19: Convergence evaluation** | `test_convergence_score_excludes_failed_run_from_optimum`; `test_scripted_v1_and_v2_experiments_match_expected_scores` | **Partial.** Unit test checks optimum handling for one failed run; integration checks final mean and optimum. Does not assert the specified K1–K6 lengths and scores individually. |
| **T20: Version experiments** | `test_scripted_v1_and_v2_experiments_match_expected_scores` | **Partial.** Runs both versions and checks selected means. Does not assert test-case counts, experiment names, or that v2’s SQL prompts include the added phrase. |
| **T21: Comparison output** | `test_scripted_v1_and_v2_experiments_match_expected_scores` | **Partial.** Checks both versions and some output values, but not the complete columns, exact row order, or all expected values. |
| **L1: Live agent lookup** | `test_live_agent_can_answer_store_lookup` | **Covered** at the stated level: requires a lookup call and `2970` in the answer. Skipped if no API key is configured. |
| **L2: Live judges** | `test_live_judges_return_allowed_labels_and_explanations` | **Mostly covered.** Checks label sets and non-empty explanations for router, clarity, and entity judges. Skipped without an API key. |

## Overall Assessment

The tests map to many spec requirements, especially through the scripted end-to-end test, but aggregate score checks do not prove the individual cases and behaviors listed in the spec. The clearest uncovered areas are **T4, T7, and T12**; several other conditions have only partial assertions.

The spec says tests should use a temporary working directory, whereas the setup test operates on the repository root. As a result, that test is not isolated as specified.

## References

- Test harness: [`tests/test_core.py`](./tests/test_core.py)
- Spec test table: [`evaluating-ai-agents-spec-62ab422.md`](./evaluating-ai-agents-spec-62ab422.md)
