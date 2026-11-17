## Score comparison between QA_CHECK_1 and QA_CHECK_2

Using the agreed scale, equal weights and **T1–T21 only**:

| Evidence judgement | Score | QA_CHECK_1 | QA_CHECK_2 |
|---|---:|---|---|
| Not covered | 0.00 | T4, T12 | — |
| Indirectly covered | 0.25 | T7, T14, T16 | — |
| Partially covered | 0.50 | T1, T2, T5, T6, T9–T11, T13, T15, T17–T21 | T10 |
| Mostly covered | 0.75 | T3 | T12, T13 |
| Covered completely | 1.00 | T8 | T1–T9, T11, T14–T21 |

Thus:

- **QA_CHECK_1:** $(100 \times 9.5 / 21 = \mathbf{45.24\%})$
- **QA_CHECK_2:** $(100 \times 20 / 21 = \mathbf{95.24\%})$
- **Difference:** **+50.00 percentage points**

### Confidence and interpretation

These are **coverage-evidence scores, not probabilities of correctness**. Confidence in the calculation is higher than confidence in the individual judgements: the score depends on interpreting the descriptions and on the chosen numeric scale.

In particular, `QA_CHECK_1` labels grouped T6–T7 as partial but calls T7 uncovered in its summary. I scored T7 **0.25** for the related lookup-error test. I also scored T14 and T16 **0.25** because aggregate checks do not directly establish the specified individual-case scores. Applying the original row labels literally instead would give **48.81%**, illustrating the judgement’s sensitivity.

`QA_CHECK_2` provides stronger evidence through focused assertions and records **65 passing offline tests**, but T10’s experiment-level failure accounting remains a gap. The two live tests are excluded from both calculations and should be reported separately as deselected, not passed.

Finally, equal weighting treats every T requirement as equally important; it does not reflect differences in risk or the number of atomic assertions within each requirement.