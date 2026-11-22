---
title: Data Model Architecture
nav_order: 3
parent: Design
---

# Data Model Architecture

**Last Updated:** November 22, 2026

## Overview

This document outlines the layered data model pattern used in the codebase, specifically the distinction between **Domain Models** and **Output Schemas**. This pattern appears in modules like `assurance.py` and provides clarity, maintainability, and architectural flexibility.

---

## Two-Layer Data Model Pattern

### Layer 1: Domain Models (BaseModel)

**Location:** Top of module (e.g., `assurance.py` lines 39+)

**Characteristics:**
- Implemented using **Pydantic BaseModel**
- Contain **validation logic** (via `@model_validator`)
- Include **business rules and computed properties**
- Represent the **internal domain concepts**
- Example: `RequirementAssessment`, `AssuranceSnapshot`

**Validation Features:**
```python
class AssuranceSnapshot(BaseModel):
    # Field-level validation
    commit: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]
    
    # Cross-field validation
    @model_validator(mode="after")
    def require_all_requirements_once(self) -> AssuranceSnapshot:
        # Ensure all T1-T21 requirements present
        # Validate weight ratios
        return self
    
    # Computed properties
    @property
    def score(self) -> float:
        # Calculate weighted score
        return ...
```

**Responsibilities:**
- Load and validate input data (from JSON/API)
- Enforce business rules and constraints
- Compute derived values
- Maintain internal consistency

---

### Layer 2: Output Schemas (TypedDict)

**Location:** Middle of module (e.g., `assurance.py` lines 242+)

**Characteristics:**
- Implemented using **TypedDict**
- **No validation logic** (structural only)
- **No methods or business logic**
- Represent **export contracts** for external consumption
- Example: `ReviewResult`, `AssuranceComparison`

**Structure Example:**
```python
class ReviewResult(TypedDict):
    judgement: Judgement
    score: float
    evidence_ref: str
    explanation: str

class AssuranceComparison(TypedDict):
    baseline: ComparisonReview
    candidate: ComparisonReview
    aggregate_delta: float
    # ... etc
```

**Responsibilities:**
- Define shape of exported data
- Provide type hints for JSON/API responses
- Enable static type checking for callers
- Document external API contract

---

## Data Flow Architecture

```
Input JSON
    ↓
AssuranceSnapshot (Domain Model)
├─ Validate all fields
├─ Check business rules
└─ Compute properties (e.g., score)
    ↓
Extract fields
    ↓
ReviewResult → AssuranceComparison (Output Schemas)
└─ Wrap in TypedDict for export
    ↓
Return as dict/JSON to caller
```

---

## Why This Separation Matters

### 1. **Flexible Internal Changes**

Adding new validation rules doesn't break external callers:

```python
# Adding this internal rule...
@model_validator(mode="after")
def new_business_rule(self) -> AssuranceSnapshot:
    # Check some internal constraint
    if not self._is_valid_combination():
        raise ValueError("Invalid combination")
    return self
```

The TypedDict contract (output schema) remains unchanged—external consumers still receive the same dict structure.

### 2. **Clear API Boundaries**

TypedDicts are **the public contract**:
- Developers know exactly what data is exported
- Changes to internal validation don't cascade to callers
- Easier to deprecate/evolve APIs cleanly

### 3. **Type Safety at Both Layers**

**Domain Model** (internal):
```python
snapshot: AssuranceSnapshot  # Static type checking on internal logic
```

**Output Schema** (external):
```python
result: AssuranceComparison  # Type hints for exported data
```

Both provide static type checking for different concerns.

### 4. **JSON Compatibility**

TypedDicts map directly to JSON:
```python
# BaseModel → dict → JSON
comparison: AssuranceComparison = {
    "baseline": {...},
    "candidate": {...},
    "aggregate_delta": 0.05
}
json.dumps(comparison)  # Works seamlessly
```

---

## Pattern Usage in Codebase

### `assurance.py`

**Domain Models (lines 39+):**
- `RequirementAssessment` – individual requirement review with validation
- `AssuranceSnapshot` – complete snapshot with business rule validation and computed properties

**Output Schemas (lines 242+):**
- `ReviewResult` – single review result for export
- `RequirementComparison` – comparison of baseline vs candidate
- `ComparisonReview` – experiment metadata for export
- `AssuranceComparison` – complete comparison for API response

**Data Flow:**
```
JSON input
  ↓
AssuranceSnapshot.model_validate(input)
  ↓
Compare baseline & candidate snapshots
  ↓
Build AssuranceComparison (TypedDict)
  ↓
Return as JSON response
```

---

## Decision Log

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2026-11-22 | Distinguish section comments | "Domain Models" vs "Output Schemas" clarifies purpose | ✅ Approved |
| 2026-11-22 | Document this pattern | Clear architecture guidance for contributors | ✅ Approved |

---

## Guidance for Contributors

### When Adding a New Domain Model

✅ **Should be a BaseModel if:**
- It needs validation logic
- It has business rules (constraints, cross-field validation)
- It has computed properties
- It's loaded from external input (JSON, API, file)

**Example:**
```python
class SpecificationRequirement(BaseModel):
    id: str
    description: str
    
    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not v.startswith('T'):
            raise ValueError("Requirement ID must start with T")
        return v
```

### When Adding an Output Schema

✅ **Should be a TypedDict if:**
- It's returned from a function (exported/serialized)
- It has no methods (purely structural)
- It's intended for external callers
- It maps to a JSON response

**Example:**
```python
class AnalysisResult(TypedDict):
    requirement_id: str
    score: float
    details: dict[str, Any]
    timestamp: str
```

### Anti-Patterns to Avoid

❌ **Don't use BaseModel for export-only data** – TypedDict is lighter and signals intent

❌ **Don't use TypedDict for data that needs validation** – Use BaseModel instead

❌ **Don't put business logic in TypedDict** – It has no methods; move logic to BaseModel

---

## Related Patterns

- **Pydantic Documentation:** [BaseModel Validation](https://docs.pydantic.dev/latest/concepts/models/)
- **TypedDict Documentation:** [Typing Module - TypedDict](https://docs.python.org/3/library/typing.html#typing.TypedDict)
- **API Design:** [Separating Domain from API Contracts](https://martinfowler.com/bliki/PresentationModel.html)

---

## Checklist for Code Review

When reviewing changes to data models:

- [ ] BaseModel classes have validation logic (not just fields)
- [ ] TypedDict classes are used for export/API responses only
- [ ] Section comments distinguish Domain Models from Output Schemas
- [ ] No TypedDict classes contain methods
- [ ] No BaseModel used only for passing data without validation
- [ ] Validation rules are tested alongside model definitions
