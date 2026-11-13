# Proposed atomic pytest suite for T1–T21

This is a test-design document, not a claim that the proposed tests have been
implemented or run. It translates each T-row in
[`evaluating-ai-agents-spec-62ab422.md`](../evaluating-ai-agents-spec-62ab422.md)
into independently checkable assertions. Keep each numbered assertion as a
separate pytest test (or a parametrized case for the same behavior), so a
partial pass cannot hide a missed requirement.

## Test conventions

- Use the deterministic `ScriptedProvider` for offline cases. A test that
  requires OpenAI or network access belongs under the existing `live` marker.
- Use a fresh `tmp_path` for filesystem and result-file tests. Give `setup`
  an explicit root (or extract an equivalent helper that accepts `root`) so
  the test can start empty and cannot alter repository data.
- For Phoenix-backed cases, use the session-scoped `isolated_phoenix`
  fixture: a separate loopback port, SQLite database under pytest's temporary
  directory, and the spec-required `evaluating-agent` project name. The
  project name is safe to reuse because the server and database are isolated.
  The fixture starts and stops the server and removes the database and log
  afterward.
- Capture span IDs before a traced operation, flush the exporter, and inspect
  only newly exported spans. Do not rely on global project counts or
  timestamp-only windows.
- Use the fixture's client for dataset and experiment operations. Do not call
  the user's default Phoenix endpoint from tests.
- Assert individual case outcomes as well as aggregate means. A correct mean
  alone can conceal incorrect per-case behavior.
- Keep coverage separate from execution outcome: skipped tests are reported
  as skipped, not passed.

A compact pytest shape for a behavioral case is:

```python
def test_t04_executes_both_calls_in_reply_in_order():
    record = run_agent("Show data and analysis together", provider=ScriptedProvider())

    assert [call["name"] for call in record["tool_calls"]] == [
        "lookup_sales_data",
        "analyze_sales_data",
    ]
    assert [item["tool_name"] for item in record["tool_responses"]] == [
        "lookup_sales_data",
        "analyze_sales_data",
    ]
    assert record["final_output"] == "Done."
    assert record["path_length"] == len(record["unchanged_messages"]) == 6
```

The test names below are proposed names. Several behaviors are partly covered
in [`tests/test_core.py`](../tests/test_core.py); the list emphasizes the
assertions needed to establish the whole spec requirement without relying on
an aggregate-only check.

## T1–T5: setup, records, and tool-call protocol

### T1 — fresh setup and fixed files

- `test_t01_setup_from_empty_root_creates_sample_table`: start with an empty
  `tmp_path`; run setup; assert the parquet file has exactly the six specified
  columns, ten rows, and expected types.
- `test_t01_setup_creates_both_fixed_question_sets`: assert the overall and
  convergence JSON files contain seven and six cases respectively, and each
  case has the specified input/output keys.
- `test_t01_setup_creates_versions_and_results_directory`: assert
  `versions/v1.json`, `versions/v2.json`, and `results/` exist.
- `test_t01_setup_does_not_overwrite_question_sets`: save both dataset files
  as bytes, run setup again, and assert byte-for-byte equality.

### T2 — uploaded Phoenix datasets

- `test_t02_setup_creates_named_project_and_two_datasets`: assert the project
  on the isolated Phoenix server is `evaluating-agent` and both datasets
  exist.
- `test_t02_dataset_names_have_required_timestamp`: full-match each name
  against its prefix and `YYYY-MM-DD HH:MM:SS` timestamp format.
- `test_t02_overall_dataset_has_exact_schema_and_ground_truth`: assert the
  input keys are exactly `question`, output keys exactly
  `sql_result`/`sql_generated`, and O1 and O3 results contain respectively
  `6200700` plus `12`, and `2970` plus `64`.
- `test_t02_convergence_dataset_contains_six_question_inputs`: assert six
  examples with only the `question` input and no expected output fields.

### T3 — single-call sequence and run record

- `test_t03_records_exact_tool_names_and_arguments`: on O1, assert the
  lookup arguments are exactly `{"prompt": O1}` and the analysis arguments
  are exactly `{"prompt": O1, "data": <lookup response text>}`.
- `test_t03_records_tool_response_and_final_output`: assert response order,
  first response tool name/content, exact final answer, and exact message
  roles `user, system, assistant, tool, assistant, tool, assistant`.
- `test_t03_path_length_equals_message_count`: assert both values are seven.

### T4 — multiple tool calls in one assistant reply

- `test_t04_executes_all_calls_in_reply_order`: run P; assert the lookup then
  analysis call order and corresponding tool-response order.
- `test_t04_appends_tool_replies_before_next_router_call`: use a provider
  spy to assert both tool messages (with the matching call IDs) are present
  when the router is called a second time.
- `test_t04_finishes_after_multi_call_reply`: assert final output `Done.`
  and path length six.

### T5 — exactly one reply per tool-call ID

- `test_t05_every_tool_call_id_has_exactly_one_tool_reply`: collect all IDs
  from assistant messages and all `tool_call_id` values from tool messages;
  assert equal multisets, not merely set membership.
- `test_t05_replies_exist_before_next_router_request`: retain the stand-in's
  missing-reply guard and assert O1 completes without triggering it.

## T6–T10: tool behavior and failure handling

### T6 — SQL cleanup and successful lookup

- `test_t06_removes_sql_fences_before_execution`: use a provider spy that
  returns fenced O1 SQL; assert the SQL passed to DuckDB equals the reference
  SQL exactly, with no fences or surrounding whitespace.
- `test_t06_lookup_returns_expected_result_without_error`: assert the
  lookup response does not start with `Error accessing data:` and contains
  `6200700` and `12`.

### T7 — lookup failure does not abort the agent run

- `test_t07_v2_sql_failure_is_returned_as_tool_response`: run O2 under v2;
  assert the lookup response starts with `Error accessing data:`.
- `test_t07_agent_produces_error_case_answer_after_lookup_failure`: assert
  the exact error-case final answer and path length seven.

### T8 — empty analysis fallback

- `test_t08_empty_analysis_reply_returns_fallback`: run E with the scripted
  empty analysis response and assert the analysis tool response is exactly
  `No analysis could be generated`.

### T9 — visualization config, returned code, and non-execution

- `test_t09_chart_code_fences_are_removed_and_code_is_returned`: run O4 and
  assert the visualization tool response is exactly
  `print(totals_by_store)`, without Markdown fences.
- `test_t09_agent_does_not_execute_generated_chart_code`: use code with a
  harmless observable side effect (for example writing a marker file);
  assert the run returns the code and the marker is not created by the
  agent.
- `test_t09_unreadable_config_uses_exact_fallback_fields`: for `odd chart`,
  inspect the config passed to the chart-code model and assert `line`,
  `date`, `value`, and title `odd chart`.
- `test_t09_generated_code_that_would_fail_does_not_fail_agent_run`: O4's
  undefined name is still returned and the agent run completes.

### T10 — router-call limit and failed run

- `test_t10_loop_stops_at_ten_router_calls`: run LOOP with the specified
  limit of ten; assert exactly ten router requests.
- `test_t10_limit_exhaustion_returns_no_run_record`: assert the run is
  reported as failed and no completed record is returned.
- `test_t10_failed_run_is_counted_in_results`: at the experiment boundary,
  assert the corresponding case has `failed=True` and its overall evaluator
  scores are zero.

## T11–T13: traces and judge behavior

### T11 — nested Phoenix trace

- `test_t11_trace_has_one_agent_run_and_three_router_calls`: query
  `isolated_phoenix.project_name` (asserted by T2 to be `evaluating-agent`)
  and only the trace created by this test; assert one `AgentRun` and three
  `router_call` spans.
- `test_t11_trace_has_tool_hierarchy_and_clean_sql_input`: assert one
  `lookup_sales_data` span with one child `execute_sql_query` span whose
  input is the fence-free O1 reference SQL, and one `analyze_sales_data`
  span. Assert parent/child relationships, not just span-name presence.
- `test_t11_trace_contains_at_least_five_model_calls`: assert at least three
  router, one SQL-generation, and one analysis model-call spans.

### T12 — judges do not pollute agent traces or records

- `test_t12_evaluation_judge_calls_are_not_exported_as_agent_spans`: run
  evaluation and inspect only its agent traces; assert no judge model-call
  span or judge prompt appears.
- `test_t12_judge_prompts_are_absent_from_run_records`: inspect returned
  records and assert neither clarity nor tool-call judge prompt is present.
- `test_t12_evaluation_does_not_change_agent_path_length`: assert O1 remains
  path length seven after evaluation.

### T13 — judge labels, normalization, prompts, and explanations

- `test_t13_normalizes_capitalized_punctuated_label`: `"Correct!"` becomes
  label `correct`, score `1`.
- `test_t13_unmatched_label_scores_zero`: `"maybe"` scores `0` and is
  normalized to an allowed fallback label.
- `test_t13_judge_prompt_requests_only_the_two_named_labels`: capture each
  judge prompt; assert it names both allowed labels, asks for one word, and
  asks for an explanation (not a numeric rating).
- `test_t13_stored_judgments_keep_label_and_explanation`: assert the two O2
  tool-call judgments normalize to `correct`, aggregate score is `1`, and
  each judgment carries `Scripted reason.`.

## T14–T18: evaluators and generated-code isolation

### T14 — router evaluator

- `test_t14_router_scores_each_planted_case`: assert O1 is `1`, O5 is `0.5`
  (one correct and one incorrect call), and HELLO/no-call is `0`.
- `test_t14_router_mean_is_expected`: separately assert the seven-case mean
  is `0.93` (unrounded value `6.5 / 7`).

### T15 — SQL-result evaluator

- `test_t15_sql_result_scores_each_planted_case`: assert O1, O4, and O5 are
  `1`, while O3 is `0`.
- `test_t15_missing_lookup_response_scores_one`: separately test a record
  with no tool responses and one with responses but no lookup; both score
  `1`, as specified.
- `test_t15_sql_result_mean_is_expected`: assert the overall mean is `0.86`
  (unrounded value `6 / 7`).

### T16 — clarity and entity evaluators

- `test_t16_clarity_scores_only_o7_zero`: assert O7 is `0`, all other
  overall cases are `1`, and mean is `0.86`.
- `test_t16_entity_scores_only_o6_zero`: assert O6 is `0`, all other
  overall cases are `1`, and mean is `0.86`.

### T17 — chart-code evaluator

- `test_t17_chart_evaluator_scores_o4_o7_and_non_chart_case`: assert O4 is
  `0`, O7 is `1`, and O1 (no visualization call) is `1`.
- `test_t17_missing_record_scores_zero`: pass a failed/missing record and
  assert `0`.
- `test_t17_chart_code_mean_is_expected`: assert the overall mean is `0.86`
  (unrounded value `6 / 7`).

### T18 — timeout and process isolation

- `test_t18_infinite_chart_code_times_out`: score an infinite loop with a
  two-second timeout; assert score `0` and elapsed time under ten seconds.
- `test_t18_chart_code_cannot_write_into_project_directory`: have generated
  code write `escape.txt` relative to its working directory; assert no such
  file appears in the project directory.
- `test_t18_valid_chart_code_still_runs_after_timeout_case`: assert O7 code
  scores `1` after the timeout case.

## T19–T21: convergence, versioned experiments, and comparison

### T19 — convergence evaluation

- `test_t19_path_lengths_match_k1_to_k6`: assert K1–K4 lengths are `5`, K5
  is `7`, and K6 is failed with no path length.
- `test_t19_failed_path_is_excluded_from_optimum_but_scores_zero`: assert
  optimal length is `5`, K6 score is `0`, and it does not affect the
  optimum.
- `test_t19_each_convergence_score_and_mean_is_exact`: assert scores
  `[1, 1, 1, 1, 5/7, 0]` and mean `4.714/6` (approximately `0.79`).

### T20 — fixed cases and version experiments

- `test_t20_both_versions_run_identical_cases_once`: assert both versions
  contain the same seven overall questions and six convergence questions,
  each appearing once.
- `test_t20_experiment_names_include_version`: assert exact names
  `Overall Experiment v1`, `Overall Experiment v2`,
  `Convergence Eval v1`, and `Convergence Eval v2`.
- `test_t20_v2_sql_prompt_contains_added_phrase`: capture SQL-generation
  requests under v2 and assert they include `Think before you respond.`;
  assert v1 prompts do not include it.
- `test_t20_v2_sql_scores_show_both_regressions`: assert O2 and O3 score
  `0`, the other five cases score `1`, and mean is `5/7` (approximately
  `0.71`).

### T21 — comparison output

- `test_t21_comparison_has_exact_columns_and_version_order`: assert the
  complete specified column sequence and exactly two rows ordered v1 then
  v2.
- `test_t21_comparison_values_match_case_results`: assert every displayed
  score, optimal path length, and failed-run count against the expected
  table: router `0.93/0.93`, SQL `0.86/0.71`, clarity `0.86/0.86`,
  entity `0.86/0.86`, chart `0.86/0.86`, convergence `0.79/0.79`,
  optimum `5/5`, failed runs `1/1`.
- `test_t21_scores_use_two_decimal_places`: assert the score strings use
  exactly two decimal places without relying only on substring matches.

## Current gaps and test status

[`tests/test_core.py`](../tests/test_core.py) already exercises parts of T1,
T3, T5–T10, T11, and T13–T21. Its most important gaps relative to these
atomic checks are: T1's empty-root isolation and created versions/results,
T2's timestamp and O3 ground truth, T4, exact call/reply multiplicity in T5,
end-to-end T7, T9's no-execution guarantee, T10's ten-call failed-run
reporting, T11's span hierarchy/counts, T12, judge prompt content in T13,
per-case evaluator results in T14–T17, T18's containment case, and the
per-case/version/table details in T19–T21.

The filesystem-root seam is available: setup and agent operations accept an
injected root, and setup accepts an injected client. The root is exercised by
`test_setup_and_agent_use_injected_temporary_root` in
[`tests/test_core.py`](../tests/test_core.py).

Phoenix-backed tests now share an isolated session fixture in
[`tests/conftest.py`](../tests/conftest.py). Each pytest process gets a
separate loopback server and temporary SQLite database, with the
spec-required `evaluating-agent` project name.
Tracing registration is bound to that endpoint/project for the process;
attempting to register a different target fails explicitly. The setup,
trace-export, and version-evaluation integration tests use this fixture and
temporary project roots. The remaining proposed atomic assertions still need
to be implemented. The current offline suite passes 13 tests; the two live
tests are deselected without a configured API key.

Until these tests exist and run, they contribute proposed coverage only. A
test's existence establishes coverage evidence; its pass/fail/skip status is
a separate result.
