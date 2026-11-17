# Phase 1: Automated Scoring Architecture
## Design Decision: Generic vs. T1-T21-Specific Implementation

**Date:** 16 November 2026  
**Context:** Planning Phase 1 implementation of automated metric scoring  
**Decision:** Build generic, reusable compliance scoring engine rather than T1-T21-specific solution

---

## The Coupling Problem

### Naive Approach (Avoid)
Hardcoding T-ID mapping directly in the codebase creates permanent coupling:

```python
# Anti-pattern: T1-T21 hardcoded into code
TEST_REQUIREMENTS = {
    'T1': {'markers': ['test_setup'], 'weight': 1.0},
    'T2': {'markers': ['test_upload'], 'weight': 1.0},
    # ... T3-T21 hardcoded
}

def calculate_spec_assurance(test_results):
    # Scoring logic knows about T1-T21 specifically
    # Problem: Cannot be reused with other requirement sets
```

**Consequences:**
- Tool becomes permanently coupled to T1-T21
- Cannot be extracted for reuse with other requirement sets
- Changes to requirements require code changes, not configuration
- Contradicts long-term goal of generic compliance measurement tool

---

## Recommended Approach: Generic Architecture First

**Philosophy:** Build the generic compliance scoring tool and apply it to T1-T21 as the first use case.

### Design Principles

1. **Requirements are Configuration, Not Code**
   - Define requirements in YAML/JSON spec files
   - Decouple requirement definitions from scoring logic
   - Support arbitrary requirement sets

2. **Generic Scoring Engine**
   - Input: requirements spec + test results (framework-agnostic)
   - Output: per-requirement scores + weighted aggregate + pass/fail/skip counts
   - No hardcoded knowledge of specific requirements

3. **Framework Agnostic**
   - Designed to work with pytest, but not coupled to it
   - Could accept test results from any test runner
   - Support multiple evidence sources (test outcomes, manual reviews)

---

## Proposed Architecture

```
agent_evals/
├── spec_assurance/              # New generic module
│   ├── __init__.py
│   ├── spec_loader.py           # Parse and validate requirement specs
│   ├── evidence_gatherer.py      # Collect evidence from tests/reviews
│   ├── scorer.py                # Generic scoring logic
│   └── validator.py             # Validate specs and results
│
├── requirements/                 # Requirement definitions
│   ├── t1-t21-spec.yaml         # T1-T21 expressed as config
│   └── schema.json              # JSON Schema for requirement specs
│
└── ...existing code...

tests/
├── test_assurance.py            # Include tests for scorer itself
└── test_spec_assurance/         # Tests for generic scoring engine
    ├── test_spec_loader.py
    ├── test_scorer.py
    └── fixtures/
        └── example_spec.yaml    # Test spec for validation
```

---

## Requirement Spec Format (Proposal)

```yaml
# requirements/t1-t21-spec.yaml
metadata:
  version: "1.0"
  description: "T1-T21 requirements from evaluating-ai-agents specification"
  created: "2026-11-16"

requirements:
  - id: T1
    description: "Setup creates specified project structure"
    test_markers: [T1_setup, T1_project_structure]
    weight: 1.0
    evidence_sources: [test_outcome]  # or [manual_review] or [test_outcome, manual_review]
    notes: "Related to setup initialization"
  
  - id: T2
    description: "Datasets are uploaded to Phoenix"
    test_markers: [T2_upload, T2_phoenix_integration]
    weight: 1.0
    evidence_sources: [test_outcome]
  
  # ... T3-T21 following same pattern
  
  - id: T10
    description: "Agent router call limit enforced at 10 calls"
    test_markers: [T10_call_limit, T10_experiment_failure]
    weight: 1.0
    evidence_sources: [test_outcome]
    notes: "Covers both agent-level and experiment-level accounting"

weight_constraints:
  min_ratio: 0.5  # min(weight) / max(weight) >= 0.5
```

---

## Generic Scoring Engine Pseudocode

```python
def calculate_compliance_score(requirements_spec, test_results, manual_reviews=None):
    """
    Generic compliance score calculator.
    
    Args:
        requirements_spec: Loaded YAML spec with requirement definitions
        test_results: Dict mapping test markers to outcomes (pass/fail/skip)
        manual_reviews: Optional dict of manually assigned evidence scores
    
    Returns:
        {
            'overall_score': 0.8894,  # Weighted average
            'per_requirement': {
                'T1': {'score': 1.0, 'evidence': 'test_outcome', 'weight': 1.0, 'tests_passed': 2, 'tests_failed': 0},
                'T2': {'score': 0.75, 'evidence': 'mixed', 'weight': 1.0, 'tests_passed': 1, 'tests_failed': 0},
                # ...
            },
            'aggregate': {
                'total_weight': 21.0,
                'tests_passed': 65,
                'tests_failed': 2,
                'tests_skipped': 0
            },
            'metadata': {
                'spec_version': '1.0',
                'timestamp': '2026-11-16T21:30:00Z'
            }
        }
    """
    # Validate spec format and weights
    validate_spec(requirements_spec)
    
    total_score = 0
    total_weight = 0
    results = {'per_requirement': {}, 'aggregate': {}}
    
    for requirement in requirements_spec['requirements']:
        req_id = requirement['id']
        weight = requirement['weight']
        
        # Gather evidence from test results
        evidence = gather_evidence(
            req_id,
            requirement['test_markers'],
            test_results,
            manual_reviews
        )
        
        # Score based on evidence
        score = compute_evidence_score(evidence)
        
        results['per_requirement'][req_id] = {
            'score': score,
            'evidence': evidence,
            'weight': weight
        }
        
        total_score += score * weight
        total_weight += weight
    
    results['overall_score'] = total_score / total_weight if total_weight > 0 else 0
    return results
```

---

## Implementation Phases

### Phase 1a: Generic Scoring Engine (This iteration)
- [ ] Define requirement spec JSON Schema
- [ ] Implement `spec_loader.py` with validation
- [ ] Implement `evidence_gatherer.py` to map pytest markers to test outcomes
- [ ] Implement `scorer.py` with generic scoring logic
- [ ] Add comprehensive tests for the scorer itself
- [ ] Create `requirements/t1-t21-spec.yaml` defining all 21 requirements

### Phase 1b: Integration & CI/CD
- [ ] Integrate with pytest (custom plugin or post-test hook)
- [ ] Add CI gate: fail if score drops below threshold
- [ ] Generate automated score reports
- [ ] Store scores in Phoenix for historical tracking

### Phase 2: Extraction
- [ ] Package as reusable module or CLI tool
- [ ] Support multiple requirement spec formats
- [ ] Document spec format for external use

---

## Benefits

### Short-term (T1-T21)
✅ Automated scoring from test results  
✅ Separates test outcomes from reviewer judgements  
✅ CI/CD regression gate  
✅ No manual snapshot creation needed  
✅ Same business value as naive approach  

### Long-term (Generic Tool)
✅ Already decoupled; extraction is packaging, not refactoring  
✅ Requirements are version-controllable configuration  
✅ Other teams/projects can reuse immediately  
✅ Supports arbitrary requirement sets  
✅ Future audits can track requirement specs over time  

### Maintainability
✅ Changes to requirements = edit YAML, not code  
✅ New requirements = add one line to spec  
✅ Scorer tests are spec-agnostic  
✅ Easier to validate spec itself with schema  

---

## Trade-offs & Concerns

### Additional Upfront Effort
**Investment:** ~1-2 hours more than naive hardcoding to:
- Define spec format and JSON Schema
- Build validation and loader
- Test scorer with multiple example specs

**Payoff:** Reusability eliminates refactoring later

### Spec Format Design Risk
**Risk:** Poorly designed format becomes hard to change.  
**Mitigation:**
- Write JSON Schema upfront
- Test scorer with multiple example specs (not just T1-T21)
- Review schema before full implementation
- Plan for versioning (allow multiple spec versions)

### Complexity vs. Benefit
**Concern:** Is generic architecture overkill for one requirement set?  
**Answer:** No, because:
- Not more complex—it's separating concerns (code vs. config)
- Supports stated long-term goal
- Makes test maintenance easier (config changes, not code changes)
- Enables future audits and comparisons

---

## Decision Record

**Decision:** Implement Phase 1 as generic compliance scoring architecture, not T1-T21-specific.

**Rationale:**
1. Aligns with long-term goal of extractable compliance measurement tool
2. Not more complex than naive approach; actually simpler (concerns separated)
3. Provides short-term automation while enabling long-term reusability
4. Requirements as configuration supports future audits and changes
5. Generic scorer can be tested independently and reused

**Next Step:** Design requirement spec format and JSON Schema, then proceed with Phase 1a implementation.

---

## References
- `qa_refactor_plan.md` — Overall QA metric development plan
- Phase 1 discussion notes — Architecture decision context
