## Updated score comparison: granular QA_CHECK_1 and QA_CHECK_2

This comparison uses one equally weighted score for each of T1–T21. Historical
scores come from [QA_CHECK_1_granular.md](./QA_CHECK_1_granular.md), based on
the archived 11-test harness at commit `77483a5`. The QA_CHECK_2 column
translates the descriptions in [QA_CHECK_2.md](./QA_CHECK_2.md) directly to
the agreed scale. The reassessed column applies that scale after inspecting
the current assertions; differences are explained below.

The scale is: not covered **0.00**, indirectly covered **0.25**, partially
covered **0.50**, mostly covered **0.75**, and covered completely **1.00**.
These are coverage-evidence judgements, not test results or probabilities of
correctness.

### Scores by requirement

| Requirement | Historical | QA_CHECK_2 as written | Current reassessment |
|---|---:|---:|---:|
| T1 — fresh setup | 0.50 | 1.00 | 1.00 |
| T2 — uploaded datasets | 0.50 | 1.00 | 1.00 |
| T3 — O1 record | 0.75 | 1.00 | 1.00 |
| T4 — multiple tool calls | 0.00 | 1.00 | 1.00 |
| T5 — call/reply IDs | 0.50 | 1.00 | 1.00 |
| T6 — SQL cleanup | 0.50 | 1.00 | 1.00 |
| T7 — v2 lookup failure | 0.25 | 1.00 | 1.00 |
| T8 — empty analysis fallback | 0.75 | 1.00 | 1.00 |
| T9 — visualization | 0.50 | 1.00 | 1.00 |
| T10 — router-call limit | 0.25 | 0.50 | 0.50 |
| T11 — nested trace | 0.50 | 1.00 | 1.00 |
| T12 — judge exclusion | 0.00 | 0.75 | 0.50 |
| T13 — judge labels | 0.50 | 0.75 | 0.75 |
| T14 — router evaluator | 0.50 | 1.00 | 1.00 |
| T15 — SQL evaluator | 0.50 | 1.00 | 1.00 |
| T16 — answer evaluators | 0.50 | 1.00 | 1.00 |
| T17 — chart evaluator | 0.50 | 1.00 | 1.00 |
| T18 — code isolation | 0.25 | 1.00 | 0.75 |
| T19 — convergence | 0.50 | 1.00 | 0.75 |
| T20 — version experiments | 0.50 | 1.00 | 0.75 |
| T21 — comparison output | 0.25 | 1.00 | 1.00 |
| **Sum** | **9.00** | **20.00** | **19.00** |

Using the proposed formula, $100 \times \sum score_i / 21$:

| Comparison | Historical | Current | Difference |
|---|---:|---:|---:|
| QA_CHECK_2 descriptors as written | 42.86% | 95.24% | +52.38 percentage points |
| Current assertions reassessed | 42.86% | 90.48% | +47.62 percentage points |

The differences are calculated before rounding. This supersedes the
preliminary figures in [score_comparison_1.md](./score_comparison_1.md)
for this comparison; that file remains a record of the earlier judgement.

### Reasons for reassessing current evidence

- **T10 — 0.50:** the ten-call LOOP limit is asserted, but its failure is
  not checked at the experiment boundary. The K6 failure in the comparison
  is a different case.
- **T12 — 0.50 rather than 0.75:** the instrumented mock client provides
  useful evidence that judge spans are suppressed, and O1's path length is
  checked. However, the record test compares raw multiline prompts against
  `json.dumps(record)`. JSON escapes newlines, so even a prompt present as
  a record string can evade the check. A local serialization example
  confirmed this; the test also does not inspect every Phoenix trace for
  prompt content. This is a test-evidence gap, not proof of actual leakage.
- **T13 — 0.75:** O2's aggregate router judgment and normalization are
  checked, but not every stored label and explanation for every judge.
- **T18 — 0.75 rather than 1.00:** timeout and post-timeout O7 execution are
  asserted. The containment test checks `tmp_path / "escape.txt"` without
  making `tmp_path` the calling working directory or demonstrating it is the
  project's directory. Consequently, a relative write in another directory
  could leave that checked path absent even if isolation regressed.
- **T19 — 0.75 rather than 1.00:** the returned summary's six path lengths,
  failure, scores, optimum and mean are checked, but the per-case
  convergence evaluations stored in Phoenix are not independently compared
  with those results.
- **T20 — 0.75 rather than 1.00:** the two returned summaries are compared
  for case questions and Phoenix task counts, and stored experiment names,
  prompt changes, and v2 SQL scores are checked. The test does not
  independently compare all saved result-file case details or the exact
  seven and six question identities against the specification.

These are conservative review choices. In particular, a test of a returned
summary may be sufficient for a narrower interpretation of T19 or T20;
reviewers may reasonably assign 1.00 if that is the agreed boundary. Changing
one requirement by a single 0.25 step changes the aggregate by approximately
**1.19 percentage points**.

### Interpretation and suitability

Both comparisons indicate a substantial improvement: the newer tests check
individual cases, use isolated project roots and a separate Phoenix backend,
and verify trace and comparison structure more directly. The reassessed
figures do not imply that the application meets 90.48% of its behavior, or
that any particular test passed: the numeric steps and equal weights are
chosen conventions, and T rows differ in scope and risk.

The historical harness was inspected rather than rerun. QA_CHECK_2 reports a
previous offline run of **65 passed, 2 live tests deselected**; this
documentation review did not rerun it. Live L1/L2 are excluded from both
T-only scores and should be reported separately as passed, failed, skipped,
or not run, as appropriate.

The metric is useful for tracking a *consistent, traceable review*, but is
not yet a fully objective measure. Further improvement would separate atomic
assertions and record directness, importance, isolation, and execution
outcome independently. Addressing the T12 and T18 assertion weaknesses and
the T10 experiment-level gap would improve the evidence before recalculating.
