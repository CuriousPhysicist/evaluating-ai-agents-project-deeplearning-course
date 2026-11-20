---
title: "Historical Score Tracking - Implementation Plan"
parent: Phase 1c
nav_order: 5
---

# Historical Score Tracking: Implementation Plan

**Issue:** #2 - Historical Score Tracking in Phoenix Database  
**Effort Estimate:** 4-6 days  
**Status:** Planning  
**Date:** 20 November 2026

---

## Overview

Implement automatic historical score tracking in Phoenix to enable:
- Automatic experiment creation after each test/evaluation run
- Per-requirement compliance score persistence
- Version-to-version comparison capability
- Baseline tracking and regression detection
- Dashboard visualization support

---

## Current State Analysis

### ✅ Already Exists

1. **Phoenix Integration**
   - `agent_evals/recording.py` - Phoenix client setup
   - `agent_evals/experiments.py` - Experiment evaluation pipeline
   - Local Phoenix server support
   - Project/dataset management

2. **Compliance Scoring**
   - `agent_evals/spec_assurance/scorer.py` - Score calculation
   - `ComplianceResult` dataclass with per-requirement scores
   - 5-level rubric scoring (0.0-1.0)
   - Weighted score aggregation

3. **CI/CD Integration**
   - `agent_evals/exit_codes.py` - Exit code contract
   - `agent_evals/cli/compliance_check.py` - Threshold configuration & checking
   - Configuration YAML support
   - Baseline management

### ⚠️ Gaps to Fill

1. **No automatic historical storage**
   - Scores calculated but not stored after runs
   - No automatic experiment creation trigger
   - Manual export only

2. **No query/retrieval API**
   - Can't retrieve historical scores by version
   - No date range filtering
   - No version comparison queries

3. **No metadata tracking**
   - Version info not stored with scores
   - Timestamp not captured automatically
   - Branch/environment not recorded

4. **No integration between systems**
   - CI/CD gating → Phoenix storage disconnected
   - Scoring → Experiment creation not linked
   - Test run completion → Tracking not triggered

---

## Architecture Design

### High-Level Flow

```
Test Run Completion
        ↓
[Exit Code Contract & Compliance Score Calculated]
        ↓
[Automatic Phoenix Integration - NEW]
        ├─ Create Experiment (name: version + timestamp)
        ├─ Store Per-Requirement Scores
        ├─ Attach Metadata (version, branch, timestamp)
        └─ Store Baseline Info
        ↓
[Historical Data Persisted]
        ↓
[Query API Available for Dashboard/Alerts]
```

### Data Structure in Phoenix

```
Experiment (one per evaluation run)
  ├─ Name: "v1.2.3-20261120-143000"
  ├─ Metadata:
  │  ├─ version: "1.2.3"
  │  ├─ timestamp: "2026-11-20T14:30:00Z"
  │  ├─ branch: "main"
  │  ├─ environment: "staging"
  │  └─ baseline: "v1.2.0" (optional)
  │
  └─ Results: Per-Requirement Scores
     ├─ T1: { score: 0.95, weight: 1.0, test_outcomes: {...} }
     ├─ T2: { score: 0.85, weight: 1.0, test_outcomes: {...} }
     ├─ T3: { score: 1.0, weight: 0.8, test_outcomes: {...} }
     └─ ... (21 requirements total)
```

---

## Implementation Components

### Component 1: Phoenix Historical Storage Module

**File:** `agent_evals/phoenix_history.py` (NEW)

**Responsibilities:**
- Create experiments in Phoenix
- Store compliance scores with metadata
- Manage baseline configurations
- Handle versioning

**Key Classes:**

```python
class HistoricalScoreTracker:
    """Manage historical score storage in Phoenix."""
    
    def __init__(self, client: Client, project_name: str):
        """Initialize with Phoenix client."""
    
    def store_evaluation_results(
        self,
        compliance_result: ComplianceResult,
        version: str,
        metadata: dict[str, Any],
    ) -> str:
        """Store compliance scores after evaluation.
        
        Args:
            compliance_result: Output from calculate_compliance_score()
            version: Version string (e.g., "1.2.3")
            metadata: Additional context (branch, timestamp, baseline, etc.)
        
        Returns:
            experiment_id: ID of created Phoenix experiment
        """
    
    def get_scores_for_version(
        self,
        version: str,
    ) -> dict[str, Any]:
        """Retrieve stored scores for a specific version."""
    
    def compare_versions(
        self,
        version1: str,
        version2: str,
    ) -> dict[str, Any]:
        """Compare scores between two versions."""
    
    def get_scores_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        requirement_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve scores within date range."""
```

**Key Methods:**

1. **`store_evaluation_results()`**
   - Create Phoenix experiment with timestamp
   - Transform ComplianceResult → Phoenix format
   - Store per-requirement scores
   - Store metadata (version, branch, baseline)
   - Return experiment ID

2. **`get_scores_for_version()`**
   - Query Phoenix for specific version
   - Return structured score data
   - Handle version not found gracefully

3. **`compare_versions()`**
   - Fetch both version scores
   - Calculate deltas per requirement
   - Identify regressions (score decreased)
   - Return comparison report

4. **`get_scores_by_date_range()`**
   - Query by timestamp range
   - Optional requirement filtering
   - Support pagination
   - Return time-series data

---

### Component 2: Integration Hook

**File:** `agent_evals/cli/compliance_check.py` (MODIFY)

**Current:** Performs compliance check and exits  
**Enhance:** Add hook to store results in Phoenix

```python
def perform_compliance_check(
    test_results: dict[str, str],
    version: str,
    config_path: str,
    store_history: bool = True,  # NEW PARAMETER
    phoenix_client: Client | None = None,  # NEW PARAMETER
) -> ComplianceCheckResult:
    """Enhanced version that stores historical data.
    
    Args:
        test_results: Test outcomes
        version: Version string
        config_path: Path to threshold config
        store_history: Whether to store in Phoenix
        phoenix_client: Phoenix client (creates if None)
    
    Returns:
        ComplianceCheckResult with exit code
    """
    # Existing logic...
    
    # NEW: Store in Phoenix if enabled
    if store_history and compliance_result:
        tracker = HistoricalScoreTracker(phoenix_client, project_name)
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "branch": get_git_branch(),
            "baseline": get_baseline_version(),
        }
        tracker.store_evaluation_results(
            compliance_result,
            version,
            metadata,
        )
```

---

### Component 3: Query API

**File:** `agent_evals/phoenix_history.py` (continuing)

**Public Query Interface:**

```python
def get_historical_scores(
    version: str | None = None,
    date_range: tuple[datetime, datetime] | None = None,
    requirement_id: str | None = None,
) -> ScoreTimeSeries:
    """Public API for querying historical scores.
    
    Supports three query patterns:
    1. Single version: get_historical_scores(version="1.2.3")
    2. Date range: get_historical_scores(
         date_range=(start, end)
       )
    3. Specific requirement: get_historical_scores(
         requirement_id="T1"
       )
    """
```

---

### Component 4: Integration Tests

**File:** `tests/test_phoenix_history.py` (NEW)

**Test Coverage:**

1. **Storage Tests**
   - ✅ Store compliance result
   - ✅ Verify metadata attached
   - ✅ Verify per-requirement scores stored
   - ✅ Verify baseline info captured

2. **Retrieval Tests**
   - ✅ Retrieve by version
   - ✅ Retrieve by date range
   - ✅ Retrieve specific requirement
   - ✅ Handle not found (version doesn't exist)

3. **Comparison Tests**
   - ✅ Compare two versions
   - ✅ Identify regressions correctly
   - ✅ Calculate deltas accurately
   - ✅ Handle new vs existing requirements

4. **Integration Tests**
   - ✅ End-to-end: compliance check → storage
   - ✅ Automatic experiment creation
   - ✅ Metadata captured correctly
   - ✅ Query retrieves stored data

5. **Edge Cases**
   - ✅ Duplicate version storage
   - ✅ Floating-point precision in scores
   - ✅ Missing optional metadata
   - ✅ Large date ranges

---

## Implementation Phases

### Phase 1: Core Storage (Days 1-2)

**Deliverables:**
- ✅ `phoenix_history.py` created
- ✅ `HistoricalScoreTracker` class implemented
- ✅ Basic storage and retrieval working
- ✅ Unit tests for storage

**Tasks:**
1. Design Phoenix data schema
2. Implement experiment creation
3. Implement score storage
4. Implement version retrieval
5. Write unit tests (minimum 5)

**Success Criteria:**
- Scores persist in Phoenix after storing
- Can retrieve stored scores by version
- Metadata attached correctly

---

### Phase 2: Integration (Days 2-3)

**Deliverables:**
- ✅ Hook into compliance_check.py
- ✅ Automatic storage on evaluation complete
- ✅ Integration tests passing
- ✅ Metadata capture working

**Tasks:**
1. Add storage hook to compliance_check
2. Capture version/branch/baseline automatically
3. Write integration tests (minimum 5)
4. Test end-to-end: check → storage → retrieve
5. Handle errors gracefully

**Success Criteria:**
- Automatic storage triggered on test completion
- Version info captured from git
- Integration tests pass (100%)

---

### Phase 3: Query API & Comparison (Days 3-4)

**Deliverables:**
- ✅ Comparison functions working
- ✅ Date range queries working
- ✅ Regression detection logic
- ✅ Query tests passing

**Tasks:**
1. Implement version comparison
2. Implement date range queries
3. Implement requirement-specific queries
4. Write comparison tests (minimum 5)
5. Test accuracy of delta calculations

**Success Criteria:**
- Compare two versions with accuracy
- Date range queries work correctly
- Regression detection works as expected

---

### Phase 4: Documentation & Optimization (Days 4-6)

**Deliverables:**
- ✅ Usage guide with examples
- ✅ API documentation
- ✅ Performance tested
- ✅ All tests passing (100%)

**Tasks:**
1. Write comprehensive usage guide
2. Create API documentation
3. Add code examples
4. Performance test with realistic data
5. Optimize slow queries
6. Final integration testing

**Success Criteria:**
- Documentation complete and clear
- All tests passing
- Performance acceptable (queries < 1 second)

---

## Technical Decisions

### 1. Phoenix Data Format

**Decision:** Store scores as individual Phoenix dataset records

**Rationale:**
- Each score is an observation with metadata
- Easier to query across time
- Supports aggregations (average, min, max)
- Works with Phoenix visualization

**Alternative Rejected:** Store as single experiment output
- Less queryable
- Harder to track time-series

---

### 2. Versioning Strategy

**Decision:** Use semantic versioning + timestamp for uniqueness

**Example:** `v1.2.3-20261120-143000`

**Rationale:**
- Human-readable
- Sortable chronologically
- Guarantees uniqueness
- Works with git tags

---

### 3. Baseline Tracking

**Decision:** Store baseline version with each result

**How:**
- Read from git tags or config
- Store with metadata
- Used for regression detection
- Optional but recommended

---

### 4. Error Handling

**Decision:** Fail gracefully - storage errors don't block evaluation

**How:**
- Try/except around storage operations
- Log errors but don't raise
- Evaluation completes with or without history
- Warn user if history storage failed

**Rationale:**
- History is nice-to-have, not critical
- Shouldn't block CI/CD pipeline
- User can retry manually if needed

---

## Testing Strategy

### Unit Tests (15+ cases)

```python
class TestHistoricalScoreTracker:
    def test_store_evaluation_results()
    def test_store_with_all_metadata()
    def test_store_with_missing_optional_metadata()
    def test_get_scores_for_version()
    def test_get_scores_version_not_found()
    def test_compare_versions()
    def test_compare_versions_with_regressions()
    def test_compare_versions_new_requirements()
    def test_get_scores_by_date_range()
    def test_get_scores_by_date_range_empty()
    def test_get_scores_by_requirement()
    def test_floating_point_precision()
    def test_duplicate_version_handling()
    def test_metadata_persistence()
    def test_Phoenix_connection_error()
```

### Integration Tests (8+ cases)

```python
class TestHistoricalTrackerIntegration:
    def test_end_to_end_compliance_check_to_storage()
    def test_automatic_experiment_creation()
    def test_version_capture_from_git()
    def test_retrieve_stored_data()
    def test_multiple_runs_same_version()
    def test_comparison_across_multiple_versions()
    def test_time_series_data_retrieval()
    def test_Phoenix_query_performance()
```

### Success Criteria

- ✅ All 23+ tests passing
- ✅ 100% pass rate on new module
- ✅ Coverage > 85%
- ✅ No regressions in existing tests

---

## Development Workflow

### Step 1: Create Feature Branch

```bash
git checkout -b feat/historical-tracking
```

### Step 2: Implement in Order

1. Create `phoenix_history.py` with `HistoricalScoreTracker`
2. Implement `store_evaluation_results()`
3. Implement `get_scores_for_version()`
4. Implement `compare_versions()`
5. Implement `get_scores_by_date_range()`
6. Add unit tests as you go
7. Integrate with `compliance_check.py`
8. Add integration tests
9. Write documentation
10. Performance optimization

### Step 3: Testing

```bash
# Run new tests
pytest tests/test_phoenix_history.py -v

# Run integration tests
pytest tests/test_compliance_check.py -v

# Run full suite
pytest -v

# Check coverage
pytest --cov=agent_evals tests/
```

### Step 4: Documentation

Create in `docs/progress/phase-1c/HISTORICAL_TRACKING_USAGE.md`:
- Setup instructions
- Usage examples
- API reference
- Troubleshooting

### Step 5: Merge

```bash
git add agent_evals/phoenix_history.py tests/test_phoenix_history.py docs/...
git commit -m "feat: Add historical score tracking in Phoenix

Implements automatic experiment creation and score storage for compliance
tracking across versions. Enables time-series analysis and regression detection.

**Features:**
- Automatic score storage after test runs
- Version comparison with delta calculation
- Date range queries for time-series analysis
- Metadata tracking (version, branch, timestamp, baseline)

**Components:**
- HistoricalScoreTracker: Main tracking class
- Integration hook in compliance_check.py
- 23+ unit and integration tests
- Comprehensive documentation

**Effort:** 4-6 days
**Tests:** 23+ passing
**Coverage:** 85%+

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"

git push origin feat/historical-tracking
```

---

## Success Criteria

### Functional Requirements
- ✅ Scores automatically stored after test runs
- ✅ Per-requirement results persisted
- ✅ Version comparison possible
- ✅ Date range queries work
- ✅ Baseline tracking working

### Non-Functional Requirements
- ✅ All tests passing (100%)
- ✅ Code coverage > 85%
- ✅ No regressions in existing code
- ✅ Query performance < 1 second
- ✅ Documentation complete

### Integration Requirements
- ✅ Works with existing compliance checking
- ✅ Works with existing Phoenix setup
- ✅ CI/CD pipeline unaffected
- ✅ Graceful error handling

---

## Blockers & Dependencies

### Dependencies (All ✅ Available)
- ✅ Phoenix integration (already exists)
- ✅ Compliance scoring (already exists)
- ✅ CI/CD gating (already merged)
- ✅ Exit code contract (already defined)

### No Blockers
✅ All required systems already in place

---

## Next Steps (For Review)

1. ✅ Review this implementation plan
2. ⏳ Approve technical decisions
3. ⏳ Create feature branch
4. ⏳ Begin Phase 1 implementation
5. ⏳ Update project board as work progresses
6. ⏳ Open PR when ready for review

---

## References

- **GitHub Issue:** #2 - Historical Score Tracking
- **Issue Plan:** `docs/progress/GITHUB_ISSUES_PLAN.md`
- **Existing Phoenix Integration:** `agent_evals/recording.py`, `agent_evals/experiments.py`
- **Compliance Scoring:** `agent_evals/spec_assurance/scorer.py`
- **CI/CD Gating:** `agent_evals/cli/compliance_check.py`

---

**Prepared By:** Copilot  
**Date:** 20 November 2026  
**Status:** Ready for Implementation  
**Next Review:** After Phase 1 completion
