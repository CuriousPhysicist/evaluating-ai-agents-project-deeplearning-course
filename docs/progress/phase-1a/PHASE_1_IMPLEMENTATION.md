---
title: "Phase 1a Implementation: Generic Compliance Scoring Engine"
parent: Phase 1a
grand_parent: Progress records
---

# Phase 1a Implementation: Generic Compliance Scoring Engine

**Date:** 16 November 2026  
**Status:** ✅ **COMPLETE**  
**Tests:** 30/30 passing (100%)

---

## Overview

Phase 1a successfully implements a generic, reusable compliance scoring framework that:

✅ **Decouples requirements from code** – Requirements are defined as YAML/JSON configuration  
✅ **Provides generic scoring** – Works with any requirement specification  
✅ **Supports pytest integration** – Maps pytest markers to test outcomes  
✅ **Enables future extraction** – Already structured for reuse as a standalone tool  
✅ **Has comprehensive tests** – 30 test cases covering all components  

---

## What Was Built

### 1. Core Module: `agent_evals/spec_assurance/`

A new Python package providing the compliance scoring framework:

#### `validator.py` – Specification and score validation
- Validates requirement spec format and structure
- Enforces weight ratio constraints (min/max >= 0.5)
- Provides clear error messages for malformed specs
- **8 validation test cases**

#### `spec_loader.py` – Load requirement specifications
- Load specs from YAML files
- Load specs from JSON files
- Load specs from Python dictionaries
- Automatic validation on load
- **4 loader test cases**

#### `evidence_gatherer.py` – Gather evidence from tests
- Map pytest markers to test outcomes
- Support for pass/fail/skip results
- Scoring logic based on test outcomes:
  - **All pass** → 1.0 (covered completely)
  - **Mix pass/fail** → 0.5 (partially covered)
  - **All fail** → 0.0 (not covered)
  - Skipped tests don't reduce score
- **8 evidence test cases**

#### `scorer.py` – Calculate compliance scores
- Generic compliance score calculator
- Per-requirement scoring with weights
- Aggregate statistics (total pass/fail/skip)
- Weighted average across requirements
- **10 scorer test cases**

### 2. Requirement Specification Format

#### Schema: `specifications/compliance/schema.json`
- JSON Schema defining valid requirement specs
- Enforces required fields: id, description, weight
- Optional fields: test_markers, evidence_sources, notes
- Validates weight constraints
- Validates evidence source types

#### T1-T21 Specification: `specifications/compliance/t1-t21-spec.yaml`
- All 21 requirements defined as YAML configuration
- Each requirement includes:
  - `id`: Unique identifier (T1–T21)
  - `description`: Human-readable description
  - `weight`: 1.0 (equal weights for all)
  - `test_markers`: Pytest markers for this requirement
  - `evidence_sources`: "test_outcome"
  - `notes`: Context about the requirement
- Weight constraints: min/max ratio ≥ 0.5

### 3. Comprehensive Test Suite: `tests/test_spec_assurance.py`

30 tests covering all components:
- **Validator tests (8)** – Format validation, weight constraints, error handling
- **Evidence gatherer tests (8)** – Test outcome mapping, scoring logic
- **Scorer tests (10)** – Score calculation, weighting, aggregation
- **Spec loader tests (4)** – YAML/JSON loading, file handling

**Test coverage highlights:**
- All-pass, all-fail, mixed results scenarios
- Edge cases: missing results, empty specs, weight violations
- Per-requirement and aggregate statistics
- Weighted scoring with different weight ratios

### 4. Example Usage: `examples/spec_assurance_example.py`

Demonstrates:
- Loading the T1-T21 specification
- Calculating compliance scores
- Generating compliance reports
- Detecting regressions (score drops)

---

## How to Use

### Basic Scoring

```python
from agent_evals.spec_assurance import (
    calculate_compliance_score,
    load_spec_from_yaml,
)

# Load specification
spec = load_spec_from_yaml("specifications/compliance/t1-t21-spec.yaml")

# Map pytest markers to test outcomes
test_results = {
    "T1_setup": "pass",
    "T1_project_structure": "pass",
    "T2_upload": "pass",
    "T2_phoenix_integration": "fail",
    # ... etc
}

# Calculate compliance
result = calculate_compliance_score(spec, test_results)

print(f"Overall Score: {result['overall_score']:.2%}")
print(f"Total Pass: {result['aggregate']['total_pass']}")
print(f"Total Fail: {result['aggregate']['total_fail']}")

# Per-requirement details
for req_id, req_result in result["per_requirement"].items():
    print(f"{req_id}: {req_result['score']:.2%}")
```

### Scoring Result Structure

```python
{
    "overall_score": 0.8894,          # Weighted average score
    "compliance_percentage": 88.94,   # As percentage
    "per_requirement": {
        "T1": {
            "requirement_id": "T1",
            "description": "Setup creates specified project structure",
            "score": 1.0,              # Per-requirement score
            "weight": 1.0,
            "weighted_score": 1.0,
            "test_outcomes": {"T1_setup": "pass", "T1_project_structure": "pass"},
            "test_counts": {"pass": 2, "fail": 0, "skip": 0},
            "evidence_source": "test_outcome"
        },
        # ... T2-T21
    },
    "aggregate": {
        "total_weight": 21.0,          # Sum of all weights
        "total_score": 18.68,          # Sum of weighted scores
        "total_pass": 65,              # Total passing tests
        "total_fail": 2,               # Total failing tests
        "total_skip": 0,               # Total skipped tests
        "compliance_percentage": 88.94
    },
    "metadata": {
        "version": "1.0",
        "description": "T1-T21 requirements from evaluating-ai-agents specification",
        "created": "2026-11-16"
    }
}
```

### Error Handling

```python
from agent_evals.spec_assurance import ValidationError

try:
    spec = load_spec_from_yaml("my_spec.yaml")
except FileNotFoundError:
    print("Spec file not found")
except ValidationError as e:
    print(f"Invalid spec: {e}")
```

---

## Running Tests

```bash
# Run all spec_assurance tests
pytest tests/test_spec_assurance.py -v

# Run specific test class
pytest tests/test_spec_assurance.py::TestScorer -v

# Run with coverage
pytest tests/test_spec_assurance.py --cov=agent_evals.spec_assurance

# Run all tests including existing suite
pytest --cov
```

**Current Status:**
- ✅ 155 total tests passing (30 new + 125 existing)
- ✅ All spec_assurance tests: 30/30 ✅
- ✅ Existing test suite: 125/125 ✅
- ✅ No regressions introduced

---

## Architecture Highlights

### Generic Design

The implementation is **not** hardcoded to T1-T21:

```python
# Requirements are configuration
spec = load_spec_from_dict({
    "requirements": [
        {"id": "REQ_001", "description": "...", "weight": 1.0, "test_markers": [...]},
        {"id": "REQ_002", "description": "...", "weight": 2.0, "test_markers": [...]},
        # ... any requirements
    ]
})

# Same scorer works for any spec
result = calculate_compliance_score(spec, test_results)
```

### Separation of Concerns

| Component | Responsibility |
|-----------|-----------------|
| `spec_loader` | Parse and validate specs (YAML/JSON) |
| `evidence_gatherer` | Map markers to test outcomes |
| `scorer` | Calculate weighted compliance scores |
| `validator` | Enforce spec format and constraints |

Each component is independently testable and reusable.

### Weight Constraints

Prevents extreme weight ratios that could skew scores:

```yaml
weight_constraints:
  min_ratio: 0.5  # min(weight) / max(weight) >= 0.5
```

This ensures no single requirement dominates if it's accidentally weighted too high.

---

## Next Steps (Phase 1b)

Phase 1b (not yet implemented) will integrate this engine with CI/CD:

1. **Pytest plugin/hook** – Automatically collect test outcomes during test runs
2. **Score threshold** – Fail CI if compliance drops below minimum
3. **Historical tracking** – Store scores in Phoenix for regression detection
4. **Automated reporting** – Generate compliance reports per commit

---

## File Structure

```
agent_evals/
├── spec_assurance/
│   ├── __init__.py              # Public API exports
│   ├── validator.py             # Spec validation
│   ├── spec_loader.py           # Load YAML/JSON specs
│   ├── evidence_gatherer.py      # Gather test evidence
│   └── scorer.py                # Calculate scores
│
specifications/compliance/
├── schema.json                  # JSON Schema for specs
└── t1-t21-spec.yaml             # T1-T21 specification
│
tests/
├── test_spec_assurance.py       # 30 test cases
│
examples/
└── spec_assurance_example.py    # Usage examples
│
qa_information/
├── Phase_1_Scoring_Architecture.md   # Architecture decision
└── PHASE_1_IMPLEMENTATION.md         # This file
```

---

## Key Design Decisions

### 1. Requirements as Configuration
**Decision:** Define requirements in YAML/JSON instead of Python code.  
**Benefit:** Changes don't require code recompilation; supports versioning and auditing.

### 2. Test Outcome Scoring Rules
**Decision:** Simple pass/fail/skip scoring (1.0/0.5/0.0).  
**Benefit:** Transparent, easy to understand; can be customized later.

### 3. Equal Default Weights
**Decision:** All T1-T21 requirements get weight 1.0.  
**Benefit:** Each requirement equally important unless explicitly weighted differently.

### 4. Generic Scorer (No T-ID Hardcoding)
**Decision:** Scorer works with any requirement spec.  
**Benefit:** Enables extraction and reuse; not tied to this project.

---

## Verification Checklist

- ✅ Generic scoring engine built
- ✅ Specification format defined (JSON Schema)
- ✅ T1-T21 requirements expressed as YAML config
- ✅ 30 comprehensive tests (100% passing)
- ✅ No regressions in existing test suite
- ✅ Pytest markers in T1-T21 spec defined
- ✅ Example usage code provided
- ✅ Error handling and validation complete
- ✅ Code well-documented with docstrings

---

## Known Limitations & Future Work

### Current Limitations
1. **Manual test marker mapping** – T1-T21 pytest markers must be added to test files manually
2. **No CI integration yet** – Phase 1b will add this
3. **No historical tracking** – Scores not yet persisted to Phoenix
4. **Simple scoring rules** – Could be enhanced with configurable scoring functions

### Future Enhancements (Phase 1b+)
1. Pytest plugin to automatically collect marked test results
2. CI gate that fails if compliance drops
3. Historical score tracking in Phoenix
4. Custom scoring functions per requirement
5. Support for manual review scores alongside test outcomes
6. JSON output for CI/CD integration

---

## References

- [Phase 1 Architecture Decision](../../design/Phase_1_Scoring_Architecture.md)
- [QA Refactor Plan](../../qa/qa_refactor_plan.md)
- [T1-T21 Specification YAML](https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course/blob/main/specifications/compliance/t1-t21-spec.yaml)
- [Requirement Spec JSON Schema](https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course/blob/main/specifications/compliance/schema.json)
- [Example Usage](https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course/blob/main/examples/spec_assurance_example.py)
