---
title: "Phase 2 Part 2: Live Phoenix Integration & Dashboard/Regression Groundwork"
parent: Progress records
nav_order: 14
---

# Phase 2 Part 2: Enable Live Phoenix & Build Foundation

**Phase:** Issue #2 (Part 2) + Issues #3 & #4 (Foundation)
**Status:** 🚀 **STARTING NOW**
**Branch:** Create `feat/phoenix-live-integration` (or new feature branch)
**Timeline:** 1-2 weeks (5-7 days foundation + 3-4 days dashboard + 3-4 days regression detection)
**Date Started:** 20 November 2026

---

## Overview

Phase 2 Part 2 focuses on:

1. **Enable Live Phoenix Tests** (Priority 1: Foundation)
   - Set up Phoenix server in test environment
   - Run end-to-end integration tests
   - Verify automatic experiment creation
   - Validate data storage and retrieval

2. **Dashboard Foundation** (Priority 2: Setup)
   - Design data query layer
   - Create visualization templates
   - Build filtering/comparison logic
   - Prepare UI components

3. **Regression Detection Foundation** (Priority 3: Setup)
   - Design detection algorithm
   - Create notification templates
   - Build configuration system
   - Prepare alert integrations

---

## Phase 2 Part 2a: Enable Live Phoenix Tests

**Effort:** 1-2 days  
**Timeline:** Days 1-2  
**Blockers:** None  
**Team Size:** 1 person (can be done independently)

### Objectives

1. ✅ Set up Phoenix server for integration testing
2. ✅ Enable skipped live tests
3. ✅ Verify automatic experiment creation
4. ✅ Validate data flow end-to-end
5. ✅ Document setup and usage

### Work Items

#### 1. Phoenix Server Setup

**Task 1a: Local Phoenix Server**
```bash
# Option 1: Docker container
docker run -p 6006:6006 arize-ai/phoenix:latest

# Option 2: Python environment
pip install arize-phoenix
python -m phoenix.server.main
```

**Task 1b: CI/CD Integration**
- Add Phoenix to GitHub Actions test environment
- Set up service container or run locally
- Configure connection string for tests

**Task 1c: Test Configuration**
- Create pytest fixtures for Phoenix client
- Set up test database/project
- Configure authentication if needed

#### 2. Enable Live Integration Tests

**Current Status:**
- 2 tests are skipped: `test_check_and_store_end_to_end_with_real_phoenix`
- Located in: `tests/test_integration_historical_tracking.py`

**Task 2a: Review Skipped Tests**
```python
# In tests/test_integration_historical_tracking.py
class TestComplianceCheckerIntegrationLive:
    @pytest.mark.skip(reason="Requires running Phoenix server")
    def test_check_and_store_end_to_end_with_real_phoenix(self):
        # Test implementation exists, just needs Phoenix
    
    @pytest.mark.skip(reason="Requires running Phoenix server")
    def test_check_and_store_multiple_runs_with_real_phoenix(self):
        # Multiple run scenario
```

**Task 2b: Create Live Test Fixtures**
- Create `conftest.py` fixture for Phoenix client
- Set up test project/dataset
- Create cleanup fixtures

**Task 2c: Enable Tests**
- Remove `@pytest.mark.skip` decorator
- Replace with conditional skip (if Phoenix unavailable)
- Add documentation for running tests

#### 3. Verify Data Flow

**Test Scenarios:**

**Scenario A: Single Compliance Check**
```
1. Run compliance check with tracker
2. ComplianceChecker.check_and_store() called
3. HistoricalScoreTracker sends data to Phoenix
4. Query Phoenix to verify data
5. Assert scores match input data
```

**Scenario B: Multiple Runs (Trend Data)**
```
1. Run multiple compliance checks with different versions
2. Each stores scores in Phoenix
3. Query historical data
4. Verify trend data is correct
5. Assert per-requirement tracking working
```

**Scenario C: Version Comparison**
```
1. Store scores for version 1.0.0
2. Store scores for version 1.0.1 (with regression)
3. Query both versions
4. Compare scores
5. Assert regression is detectable
```

#### 4. Documentation

**Create:** `docs/progress/PHOENIX_LIVE_INTEGRATION.md`

Sections:
- Phoenix server setup (local and CI/CD)
- Running live integration tests
- Troubleshooting common issues
- Performance considerations
- Data verification examples

### Success Criteria

- ✅ Phoenix server runs successfully (local)
- ✅ All 2 live tests pass (or conditionally skip gracefully)
- ✅ Data flows from checker to Phoenix to queries
- ✅ Multiple run scenarios work correctly
- ✅ CI/CD integration working
- ✅ Documentation complete

### Deliverables

1. ✅ Phoenix server setup guide
2. ✅ Enabled live integration tests
3. ✅ Test fixtures and configuration
4. ✅ Verification of end-to-end data flow
5. ✅ Documentation with examples
6. ✅ CI/CD integration (GitHub Actions)

---

## Phase 2 Part 2b: Dashboard Foundation (Starting Day 3)

**Effort:** 5-7 days (can run parallel with live tests)
**Timeline:** Days 3-9
**Depends On:** Phase 2 Part 2a (Phoenix tests working)
**Team Size:** 1-2 people

### Objectives

1. ✅ Design data query layer for historical data
2. ✅ Create Phoenix dashboard templates
3. ✅ Build visualization components
4. ✅ Implement filtering and comparison logic
5. ✅ Document configuration and usage

### Work Items

#### 1. Data Query Layer

**Task 1a: Create Query Functions**
```python
# File: agent_evals/phoenix_query.py (new)

def get_scores_by_version(version: str, project: str) -> Dict:
    """Query historical scores for a specific version."""

def get_scores_by_date_range(start: datetime, end: datetime) -> List[Dict]:
    """Query scores within a date range."""

def get_score_trends(requirement_id: str, limit: int = 100) -> List[Dict]:
    """Get trend data for a specific requirement."""

def compare_versions(version1: str, version2: str) -> Dict:
    """Compare scores between two versions."""

def get_regression_candidates(baseline_version: str) -> List[Dict]:
    """Identify potential regressions vs baseline."""
```

**Task 1b: Create Query Tests**
- Unit tests for each query function
- Mock Phoenix responses
- Test edge cases (no data, single record, large datasets)

#### 2. Phoenix Dashboard Templates

**Task 2a: Dashboard Configuration**
```python
# File: agent_evals/dashboard_config.py (new)

DASHBOARD_TEMPLATES = {
    "compliance_trends": {
        "title": "Compliance Score Trends",
        "charts": [
            {
                "type": "line",
                "query": "get_scores_by_date_range",
                "axes": {"x": "date", "y": "score"}
            }
        ]
    },
    "per_requirement_heatmap": {
        "title": "Requirements Heatmap",
        "charts": [
            {
                "type": "heatmap",
                "query": "get_requirement_history",
                "axes": {"x": "version", "y": "requirement_id"}
            }
        ]
    },
    "version_comparison": {
        "title": "Version Comparison",
        "charts": [
            {
                "type": "bar",
                "query": "compare_versions",
                "axes": {"x": "requirement_id", "y": "score_diff"}
            }
        ]
    }
}
```

**Task 2b: Integration with Phoenix**
- Use Phoenix's built-in visualization
- Or create custom visualization layer
- Support multiple chart types (line, heatmap, bar, table)

#### 3. Visualization Components

**Task 3a: Chart Components**
- Line chart for overall trends
- Heatmap for per-requirement changes
- Bar chart for version comparisons
- Table for detailed data view

**Task 3b: Interactive Features**
- Date range picker
- Requirement filtering
- Version comparison selector
- Export functionality (CSV, PNG)

#### 4. Filtering & Comparison Logic

**Task 4a: Filter Engine**
```python
# File: agent_evals/filters.py (new)

class ScoreFilter:
    """Filter historical scores by various criteria."""
    
    def by_version(self, version: str):
        """Filter by version."""
    
    def by_date_range(self, start: datetime, end: datetime):
        """Filter by date range."""
    
    def by_requirement(self, requirement_id: str):
        """Filter by requirement ID."""
    
    def by_score_range(self, min_score: float, max_score: float):
        """Filter by score range."""
```

**Task 4b: Comparison Logic**
- Side-by-side version comparison
- Diff calculation (score changes)
- Trend analysis (improvement/regression)

#### 5. Documentation

**Create:** `docs/progress/DASHBOARD_IMPLEMENTATION.md`

Sections:
- Architecture overview
- Query layer design
- Dashboard configuration
- Usage guide with examples
- Customization and extension points

### Success Criteria

- ✅ Query functions implemented and tested
- ✅ Dashboard templates created
- ✅ Visualization components working
- ✅ Filtering/comparison logic implemented
- ✅ 10+ integration tests passing
- ✅ Documentation complete with examples

### Deliverables

1. ✅ Query layer (5-10 functions)
2. ✅ Dashboard templates
3. ✅ Visualization components
4. ✅ Filtering and comparison logic
5. ✅ 10+ integration tests
6. ✅ Documentation with examples

---

## Phase 2 Part 2c: Regression Detection Foundation (Starting Day 7)

**Effort:** 3-4 days (can run parallel with dashboard)
**Timeline:** Days 7-10
**Depends On:** Phase 2 Part 2a (Phoenix tests working)
**Team Size:** 1 person

### Objectives

1. ✅ Design regression detection algorithm
2. ✅ Create alert notification templates
3. ✅ Build configuration system
4. ✅ Prepare alert integrations (Slack, email, GitHub)
5. ✅ Document setup and usage

### Work Items

#### 1. Regression Detection Algorithm

**Task 1a: Detection Logic**
```python
# File: agent_evals/regression_detection.py (new)

class RegressionDetector:
    """Detect regressions in compliance scores."""
    
    def __init__(self, baseline_version: str, threshold: float = 0.05):
        """Initialize with baseline version and threshold."""
    
    def detect_regressions(self, current_scores: Dict) -> List[Regression]:
        """
        Compare current scores against baseline.
        Return list of detected regressions.
        """
    
    def calculate_impact(self, regression: Regression) -> Dict:
        """Calculate severity and impact of regression."""
    
    def classify_severity(self, impact: Dict) -> str:
        """Classify as warning, critical, or none."""
```

**Task 1b: Comparison Strategies**
- Exact threshold: score < baseline - 0.05
- Percentage-based: score < baseline * 0.95
- Statistical: z-score analysis
- Trend-based: multi-run comparison

#### 2. Alert Notification Templates

**Task 2a: Alert Format**
```python
# File: agent_evals/alert_templates.py (new)

ALERT_TEMPLATES = {
    "slack": {
        "warning": "⚠️ Score decreased by {impact}%",
        "critical": "🚨 CRITICAL: Score decreased by {impact}%"
    },
    "email": {
        "warning": "Compliance Score Warning",
        "critical": "CRITICAL: Compliance Score Regression"
    },
    "github": {
        "warning": "Regression detected: {requirement}",
        "critical": "CRITICAL REGRESSION: {requirement}"
    }
}
```

**Task 2b: Template Rendering**
- Format alerts with actual data
- Include links to dashboard
- Include version comparison details

#### 3. Configuration System

**Task 3a: Configuration Schema**
```yaml
# example-regression-config.yaml
regression_detection:
  enabled: true
  baseline_version: "1.0.0"
  detection_strategy: "threshold"  # or "percentage", "statistical"
  
  thresholds:
    overall_score: 0.05  # 5% decrease
    per_requirement: 0.10  # 10% decrease
  
  severity_levels:
    warning: 0.05
    critical: 0.15
  
  alerts:
    enabled: true
    channels:
      slack:
        enabled: true
        webhook_url: "${SLACK_WEBHOOK_URL}"
      email:
        enabled: false
        recipients: ["team@example.com"]
      github:
        enabled: true
        pr_comment: true
```

**Task 3b: Configuration Loading**
- Load from YAML or environment variables
- Validate configuration
- Support profile system (dev, staging, production)

#### 4. Alert Integrations

**Task 4a: Slack Integration**
```python
class SlackAlerter:
    """Send alerts to Slack."""
    
    def send_alert(self, regression: Regression, severity: str):
        """Send alert to Slack webhook."""
```

**Task 4b: Email Integration**
```python
class EmailAlerter:
    """Send alerts via email."""
    
    def send_alert(self, regression: Regression, recipients: List[str]):
        """Send alert to email recipients."""
```

**Task 4c: GitHub Integration**
```python
class GitHubAlerter:
    """Post alerts as GitHub PR comments."""
    
    def send_alert(self, regression: Regression, pr_number: int):
        """Post alert as comment on GitHub PR."""
```

#### 5. Documentation

**Create:** `docs/progress/REGRESSION_DETECTION_IMPLEMENTATION.md`

Sections:
- Detection algorithm overview
- Configuration guide
- Alert channel setup
- Usage examples
- Troubleshooting

### Success Criteria

- ✅ Detection algorithm implemented and tested
- ✅ Alert templates created
- ✅ Configuration system working
- ✅ Slack integration working
- ✅ Email integration stubbed out
- ✅ GitHub integration stubbed out
- ✅ 10+ integration tests passing
- ✅ Documentation complete

### Deliverables

1. ✅ Regression detection algorithm
2. ✅ Alert notification system
3. ✅ Configuration system
4. ✅ Slack integration (working)
5. ✅ Email/GitHub integrations (templates)
6. ✅ 10+ integration tests
7. ✅ Documentation with examples

---

## Branch Strategy

### Create Feature Branch
```bash
git checkout main
git pull origin main
git checkout -b feat/phoenix-live-integration
```

### Commits During Phase 2 Part 2

**After Live Tests (Day 2):**
```bash
git commit -m "feat(Issue #2 Part 2): Enable live Phoenix integration tests

- Set up Phoenix server test fixture
- Remove skip decorator from live tests
- Add end-to-end data flow verification
- Create CI/CD integration configuration
- Document Phoenix setup and usage

Tests: 2 live tests now passing"
```

**After Dashboard Foundation (Day 9):**
```bash
git commit -m "feat(Issue #3): Dashboard foundation - query layer & templates

- Create data query functions (5 core queries)
- Build Phoenix dashboard templates (3 templates)
- Implement visualization components
- Create filtering and comparison logic
- Add 10+ integration tests for dashboard layer

Ready for dashboard UI implementation"
```

**After Regression Detection Foundation (Day 10):**
```bash
git commit -m "feat(Issue #4): Regression detection foundation - algorithm & alerts

- Implement regression detection algorithm
- Create alert notification templates
- Build configuration system (YAML)
- Integrate Slack notifications
- Stub out email and GitHub integrations
- Add 10+ integration tests

Ready for full integration and production setup"
```

### Create Pull Request

After all three parts are complete:
```bash
git push origin feat/phoenix-live-integration
# Then create PR with:
# - Title: "Phase 2 Part 2: Live Phoenix Integration & Foundation for Dashboard/Regression"
# - Description: Detailed summary of all three parts
# - Link to Issues #2 (Part 2), #3, #4
```

---

## Testing Strategy

### Live Integration Tests
- Use pytest with Phoenix fixtures
- Mock where appropriate, real where needed
- Test three scenarios (single run, multiple runs, version comparison)

### Unit Tests
- Query functions (mocked Phoenix)
- Alert rendering (mocked notifications)
- Configuration loading (fixture files)

### Integration Tests
- Full flow: check → store → query → alert
- Multiple versions and time periods
- Performance with large datasets

### Target Coverage
- Dashboard layer: 15+ tests
- Regression detection: 15+ tests
- Live integration: 2 live tests (now enabled)
- **Total:** 30+ new tests

---

## Risk Mitigation

### Risk 1: Phoenix Server Unavailable
**Mitigation:** 
- Graceful skip if Phoenix unavailable
- Local testing option
- Docker container provided

### Risk 2: Performance with Large Datasets
**Mitigation:**
- Query optimization from day 1
- Use Phoenix's built-in indexing
- Implement pagination for large results

### Risk 3: Notification Delivery Issues
**Mitigation:**
- Stub integrations initially
- Full integration after validation
- Fallback to logging

### Risk 4: Configuration Complexity
**Mitigation:**
- Start with simple YAML schema
- Provide example configurations
- Document all options

---

## Success Checklist

**Phase 2 Part 2a: Live Phoenix (Days 1-2)**
- ✅ Phoenix server set up
- ✅ 2 live tests enabled and passing
- ✅ CI/CD integration working
- ✅ Documentation complete

**Phase 2 Part 2b: Dashboard Foundation (Days 3-9)**
- ✅ Query layer implemented (5+ functions)
- ✅ Dashboard templates created (3+ templates)
- ✅ Visualization components ready
- ✅ Filtering/comparison logic working
- ✅ 10+ tests passing
- ✅ Documentation complete

**Phase 2 Part 2c: Regression Detection Foundation (Days 7-10)**
- ✅ Detection algorithm implemented
- ✅ Alert templates created
- ✅ Configuration system working
- ✅ Slack integration working
- ✅ Email/GitHub stubs ready
- ✅ 10+ tests passing
- ✅ Documentation complete

**Overall Phase 2 Part 2**
- ✅ All 30+ tests passing
- ✅ No regressions in existing code
- ✅ Full documentation
- ✅ Ready for dashboard UI and production integration

---

## Timeline Summary

| Phase | Days | Effort | Status |
|-------|------|--------|--------|
| **Part 2a: Live Phoenix** | 1-2 | 1-2 days | 🚀 Ready to start |
| **Part 2b: Dashboard Foundation** | 3-9 | 5-7 days | ⏳ Can run parallel |
| **Part 2c: Regression Foundation** | 7-10 | 3-4 days | ⏳ Can run parallel |
| **Testing & Docs** | Throughout | Included | ✅ Comprehensive |
| **Total Phase 2 Part 2** | **1-10 days** | **5-7 days** | 🎯 Goal |

---

## Next Immediate Actions

1. **Today:** Start Phase 2 Part 2a (Live Phoenix)
   - Set up Phoenix server
   - Review skipped tests
   - Create test fixtures

2. **Tomorrow:** Enable live tests & verify data flow
   - Remove skip decorators
   - Run tests with Phoenix
   - Document setup

3. **Day 3:** Kick off Dashboard & Regression foundation
   - Create query layer
   - Design templates
   - Outline algorithm

---

**Prepared By:** Copilot  
**Date:** 20 November 2026, 21:09 UTC  
**Status:** 🚀 **READY TO START PHASE 2 PART 2**  
**Branch:** feat/phoenix-live-integration (to be created)
