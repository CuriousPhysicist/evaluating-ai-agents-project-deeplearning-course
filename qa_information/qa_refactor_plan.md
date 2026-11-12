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
&nbsp;
---
###### _v1.1 Date: 12th Nov. 2026_