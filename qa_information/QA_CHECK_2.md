# QA Check 2: Spec Requirements vs. Test Harness

## Summary

The earlier [QA Check 1](./QA_CHECK_1.md) compared the spec with a harness
containing 11 offline tests. The current suite has 65 offline tests, all
passing; the two live tests are deselected when no API key is configured.
Test count is not the same as requirement count: several tests exercise more
than one assertion, while some specification rows still need a more direct
check.

## Coverage by Spec Condition

| Condition | Closest test(s) | Assessment |
|---|---|---|
| **T1: Fresh setup and fixed files** | `test_t01_setup_from_empty_root_creates_sample_table`; `test_t01_setup_creates_both_fixed_question_sets`; `test_t01_setup_creates_versions_and_results_directory`; `test_t01_setup_does_not_overwrite_question_sets` | **Covered.** Starts from an empty `tmp_path`; checks the parquet schema/data types, seven and six case schemas, version files, results directory, and non-overwrite behavior. |
| **T2: Uploaded datasets** | `test_t02_setup_creates_named_project_and_two_datasets`; `test_t02_dataset_names_have_required_timestamp`; `test_t02_overall_dataset_has_exact_schema_and_ground_truth`; `test_t02_convergence_dataset_contains_six_question_inputs` | **Covered.** Checks the isolated `evaluating-agent` project, timestamped dataset names, exact schemas and O1/O3 ground truth, and six convergence inputs. |
| **T3: Agent record and message sequence** | `test_t03_records_exact_tool_names_and_arguments`; `test_t03_records_tool_response_and_final_output`; `test_t03_path_length_equals_message_count` | **Covered.** Verifies O1's exact tool arguments, lookup result passed to analysis, response/final output, message roles, and path length. |
| **T4: Multiple calls in one reply** | `test_t04_executes_all_calls_in_reply_order`; `test_t04_appends_tool_replies_before_next_router_call`; `test_t04_finishes_after_multi_call_reply` | **Covered.** Checks lookup-then-analysis order, both replies before the next router request, completion, and path length. |
| **T5: Tool-call/reply IDs** | `test_t05_every_tool_call_id_has_exactly_one_tool_reply`; `test_t05_replies_exist_before_next_router_request` | **Covered.** Compares ID multisets and retains a stand-in guard against requesting another router response before replies exist. |
| **T6: SQL cleanup and lookup** | `test_t06_removes_sql_fences_before_execution`; `test_t06_lookup_returns_expected_result_without_error` | **Covered.** Confirms DuckDB receives the exact fence-free reference SQL and the successful lookup returns O1's values. |
| **T7: Lookup failure handling** | `test_t07_v2_sql_failure_is_returned_as_tool_response`; `test_t07_agent_produces_error_case_answer_after_lookup_failure` | **Covered.** Checks the v2 O2 error response, continued run, exact final answer, and path length. |
| **T8: Empty analysis reply** | `test_t08_empty_analysis_reply_returns_fallback` | **Covered.** Asserts the exact fallback tool response. |
| **T9: Visualization behavior** | `test_t09_chart_code_fences_are_removed_and_code_is_returned`; `test_t09_agent_does_not_execute_generated_chart_code`; `test_t09_unreadable_config_uses_exact_fallback_fields`; `test_t09_generated_code_that_would_fail_does_not_fail_agent_run` | **Covered.** Checks fence removal, returned code, non-execution, fallback config, and that bad generated code does not abort the agent run. |
| **T10: Router-call limit and failed run** | `test_t10_loop_stops_at_ten_router_calls` | **Partial.** Confirms the LOOP provider is called exactly ten times and the run raises instead of returning a record. There is no experiment-boundary test showing this specific limit failure is stored as failed with zero overall evaluator scores. The failed K6 path and comparison count do not establish that behavior for LOOP. |
| **T11: Nested Phoenix trace** | `test_t11_trace_has_one_agent_run_and_three_router_calls`; `test_t11_trace_has_tool_hierarchy_and_clean_sql_input`; `test_t11_trace_contains_at_least_five_model_calls` | **Covered.** Checks a single new trace, exact router/tool counts and parent relationships, cleaned SQL input, and model-call placement/counts. |
| **T12: Judge calls excluded from traces/records** | `test_t12_evaluation_judge_calls_are_not_exported_as_agent_spans`; `test_t12_judge_prompts_are_absent_from_run_records`; `test_t12_evaluation_does_not_change_agent_path_length` | **Mostly covered.** Runs a full evaluation with an instrumented mock OpenAI client and checks that judge calls add no spans after an unsuppressed control call; also checks prompt absence in task records and O1 path length. Span suppression is observed through an in-memory exporter rather than by querying prompt attributes in every Phoenix agent trace. |
| **T13: Judge labels, prompts, and explanations** | `test_t13_normalizes_capitalized_punctuated_label`; `test_t13_unmatched_label_scores_zero`; `test_t13_judge_prompt_requests_only_the_two_named_labels`; `test_t13_stored_judgments_keep_label_and_explanation`; `test_live_judges_return_allowed_labels_and_explanations` | **Mostly covered.** Tests normalization, non-matching replies, allowed prompt labels and explanations, and O2's stored aggregate judgment. The offline stored-result assertion is focused on O2's router evaluation rather than enumerating every stored label/explanation for every evaluator. The live test is conditional on an API key. |
| **T14: Router evaluator** | `test_t14_router_scores_each_planted_case`; `test_t14_router_mean_is_expected` | **Covered.** Checks O1 = 1, O5 = 0.5, HELLO = 0, and the 6.5/7 mean. |
| **T15: SQL-result evaluator** | `test_t15_sql_result_scores_each_planted_case`; `test_t15_missing_lookup_response_scores_one`; `test_t15_sql_result_mean_is_expected` | **Covered.** Checks O1/O4/O5 = 1, O3 = 0, both missing-lookup forms = 1, and the 6/7 mean. |
| **T16: Clarity and entity evaluators** | `test_t16_clarity_scores_only_o7_zero`; `test_t16_entity_scores_only_o6_zero` | **Covered.** Checks O7 is the only unclear case, O6 the only incorrect-entity case, and each 6/7 mean. |
| **T17: Chart-code evaluator** | `test_t17_chart_evaluator_scores_o4_o7_and_non_chart_case`; `test_t17_missing_record_scores_zero`; `test_t17_chart_code_mean_is_expected` | **Covered.** Checks O4 = 0, O7 and non-chart O1 = 1, missing record = 0, and the 6/7 mean. |
| **T18: Timeout and process isolation** | `test_t18_infinite_chart_code_times_out`; `test_t18_chart_code_cannot_write_into_project_directory`; `test_t18_valid_o7_chart_code_runs_after_timeout_case`; `test_chart_code_runs_without_project_api_key` | **Covered.** Checks the two-second timeout bound, project-folder containment, O7 after timeout, and that generated code does not inherit the API key. |
| **T19: Convergence evaluation** | `test_t19_path_lengths_match_k1_to_k6`; `test_t19_failed_path_is_excluded_from_optimum_but_scores_zero`; `test_t19_each_convergence_score_and_mean_is_exact` | **Covered.** Verifies K1–K6 lengths, the failed K6 score/exclusion, optimum 5, each score, and the mean. |
| **T20: Fixed cases and version experiments** | `test_t20_both_versions_run_identical_cases_once`; `test_t20_experiment_names_include_version`; `test_t20_v2_sql_prompt_contains_added_phrase`; `test_t20_v2_sql_scores_show_both_regressions` | **Covered.** Checks the same unique 7/6 cases and one run per example, persisted experiment names, v2-only SQL prompt phrase, and O2/O3 SQL regressions. |
| **T21: Comparison output** | `test_t21_comparison_has_exact_columns_and_version_order`; `test_t21_comparison_values_match_case_results`; `test_t21_scores_use_two_decimal_places` | **Covered.** Checks the full column list, v1/v2 row order, all expected values, failed counts, and two-decimal score formatting. |
| **L1: Live agent lookup** | `test_live_agent_can_answer_store_lookup` | **Covered when run.** Requires a lookup call and `2970` in the answer; deselected without an API key. |
| **L2: Live judges** | `test_live_judges_return_allowed_labels_and_explanations` | **Covered when run.** Checks allowed labels and non-empty explanations for router, clarity, and entity judges; deselected without an API key. |

## Overall Assessment

Coverage has expanded substantially from the earlier 11-test snapshot. The
current 65 passing offline tests provide direct checks for T1–T9 and T11,
T14–T21. T12 and T13 have meaningful integration coverage, with the
limitations described above. The clearest remaining gap is **T10's
experiment-level accounting of the ten-call LOOP failure**; the current
comparison's failed-run count is driven by the planted K6 convergence failure,
not the LOOP case.

The 65-test result is an execution outcome, not a coverage percentage. The two
live tests are separate from that offline count and were deselected because
no API key was configured.

## References

- Test harness: [`tests/test_core.py`](../tests/test_core.py),
  [`tests/test_setup_spec.py`](../tests/test_setup_spec.py)
- Spec test table: [`evaluating-ai-agents-spec-62ab422.md`](../evaluating-ai-agents-spec-62ab422.md)
- Atomic test mapping: [`spec_test_suite_proposal.md`](./spec_test_suite_proposal.md)
