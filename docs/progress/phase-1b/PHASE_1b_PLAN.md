---
title: "Phase 1b: Pytest Integration & Automation"
parent: Phase 1b
grand_parent: Progress records
---

# Phase 1b: Pytest Integration & Automation

**Date:** 16 November 2026  
**Status:** Planning  
**Goal:** Automate test marker collection and integrate with existing test suite

---

## Overview

Phase 1b builds on Phase 1a's generic compliance scoring engine by:
1. Adding pytest markers to existing test files
2. Creating a pytest plugin to automatically collect marked test results
3. Generating automated compliance reports post-test-run
4. Integrating with CI/CD workflows

---

## Scope: What Phase 1b Delivers

### 1. Pytest Marker Integration
- Add T-ID markers to existing test files (T1-T21 mapping)
- Ensure all 65 existing offline tests are properly marked
- Document marker usage patterns

### 2. Pytest Plugin
- Create `agent_evals/pytest_plugin.py` - pytest plugin to collect marked test results
- Hook into pytest's test collection and execution phases
- Build result mapping (marker → pass/fail/skip)
- Output structured results for scorer input

### 3. CLI Integration
- Add `--assurance-report` flag to pytest execution
- Generate compliance score report after test run
- Output HTML report (optional) for visualization
- Save structured JSON output for CI/CD integration

### 4. Automated Scoring Hook
- Post-test-run hook to calculate compliance score
- Fail CI gate if compliance drops below threshold (configurable)
- Display compliance metrics in test output summary

### 5. Documentation
- Pytest plugin usage guide
- Marker application patterns
- CI/CD integration examples
- Troubleshooting guide

---

## Proposed Commit Structure (6 commits)

### Commit 1: Add pytest markers to existing test files
**Files:** `tests/*.py` (selective marker additions)
**Description:** 
- Tag existing tests with T-ID markers
- Apply to core_tests.py, offline tests, integration tests
- Match markers to T1-T21 requirements from spec

**Rationale:**
- Makes existing tests discoverable by compliance engine
- Minimal changes to existing code (decorator only)
- Clear traceability to requirements

### Commit 2: Create pytest plugin core
**Files:** 
- `agent_evals/pytest_plugin.py` - Main plugin implementation
- `agent_evals/pytest_plugin_config.py` - Configuration schema
- `pyproject.toml` - Register plugin entry point

**Description:**
- Plugin class with pytest hooks
- Test result collector
- Marker → outcome mapping
- Configuration handling

**Rationale:**
- Separates plugin concerns from scoring engine
- Clean integration point for pytest
- Reusable for other projects

### Commit 3: Implement compliance report generation
**Files:**
- `agent_evals/compliance_reporter.py` - Report generation logic
- `agent_evals/reporters/` - Reporter implementations
  - `agent_evals/reporters/json_reporter.py` - JSON output
  - `agent_evals/reporters/html_reporter.py` - HTML output
  - `agent_evals/reporters/console_reporter.py` - Terminal output

**Description:**
- Load spec and test results
- Calculate compliance scores
- Format reports (JSON, HTML, console)
- Save output files

**Rationale:**
- Multiple output formats for different use cases
- Modular reporter design
- Easy to extend with new formats

### Commit 4: Add comprehensive tests for pytest integration
**Files:**
- `tests/test_pytest_plugin.py` - Plugin unit tests
- `tests/test_compliance_reporter.py` - Reporter tests
- `tests/fixtures/sample_marked_tests.py` - Test fixtures

**Description:**
- Test marker collection
- Test result mapping
- Test report generation
- Edge cases (missing markers, failed runs, etc.)

**Rationale:**
- Ensures plugin works correctly
- Validates report accuracy
- Prevents regressions

### Commit 5: Document pytest integration & CI/CD usage
**Files:**
- `docs/progress/phase-1b/PHASE_1b_PYTEST_INTEGRATION.md` - Technical guide
- `docs/progress/phase-1b/PHASE_1b_CI_CD_SETUP.md` - CI/CD examples
- `README_COMPLIANCE.md` - User-facing compliance guide

**Description:**
- How to add markers to tests
- How to run compliance checks
- CI/CD integration examples (GitHub Actions, GitLab CI, etc.)
- Troubleshooting common issues

**Rationale:**
- Enables adoption by team
- Provides reference implementations
- Clear usage patterns

### Commit 6: Add CLI commands for compliance reporting
**Files:**
- `agent_evals/cli_compliance.py` - CLI commands
- Updates to `main_cli.py` or existing CLI module

**Description:**
- `compliance-report` command - Generate report from test results
- `compliance-check` command - Run compliance gate
- `compliance-compare` command - Compare compliance across runs

**Rationale:**
- Makes compliance scoring accessible from command line
- Integrates with existing CLI workflows
- Enables CI/CD integration

---

## Key Features by Commit

### Commit 1: Pytest Markers
```python
# Example test marking
@pytest.mark.T1_setup
@pytest.mark.T1_project_structure
def test_setup_creates_project_structure():
    # Test implementation
    pass
```

### Commit 2: Pytest Plugin
```python
# Example plugin usage
$ pytest tests/ --assurance-report

# Automatically:
# 1. Collects all marked tests
# 2. Maps markers to outcomes (pass/fail/skip)
# 3. Saves results to .compliance_results.json
```

### Commit 3: Compliance Reporting
```python
# Example output
$ pytest tests/ --assurance-report
# ... test output ...
# ======= Compliance Report =======
# Overall Score: 85.71%
# Tests Passed: 60
# Tests Failed: 2
# Tests Skipped: 3
# Report saved: .compliance_report.html
```

### Commit 4: Tests
```python
def test_plugin_collects_marked_tests():
    """Verify plugin finds all marked tests."""
    pass

def test_reporter_generates_valid_json():
    """Verify reporter creates valid JSON output."""
    pass
```

### Commit 5: Documentation
- Marker patterns for different test types
- Expected output formats
- Troubleshooting guide

### Commit 6: CLI Integration
```bash
# Check compliance
$ compliance-report tests/

# Generate HTML report
$ compliance-report tests/ --format html --output report.html

# Check if compliance meets threshold
$ compliance-check tests/ --threshold 80% --fail-if-below
```

---

## Testing Strategy

### Unit Tests
- Marker collection logic
- Result mapping
- Report generation
- Error handling

### Integration Tests
- Full test run with markers
- Report generation workflow
- CLI commands
- Multiple report formats

### Edge Cases
- Tests without markers
- Failed test runs
- Missing spec files
- Invalid marker names

---

## Success Criteria

- ✅ All existing tests properly marked with T-IDs
- ✅ Pytest plugin correctly collects marked tests
- ✅ Compliance score calculated from test results
- ✅ Multiple report formats (JSON, HTML, console)
- ✅ CI/CD integration working
- ✅ 100% test pass rate for new code
- ✅ Zero regressions in existing tests
- ✅ Documentation complete and clear

---

## Estimated Implementation Time

| Phase | Effort | Duration |
|-------|--------|----------|
| Commit 1 | Moderate | ~20 min |
| Commit 2 | High | ~45 min |
| Commit 3 | High | ~45 min |
| Commit 4 | Moderate | ~30 min |
| Commit 5 | Moderate | ~30 min |
| Commit 6 | Moderate | ~30 min |
| **Total** | | **~3 hours** |

---

## Implementation Order

1. Add pytest markers (Commit 1) - Prerequisite for all others
2. Create pytest plugin (Commit 2) - Core functionality
3. Implement reporting (Commit 3) - Display results
4. Add tests (Commit 4) - Validate implementation
5. Document integration (Commit 5) - Enable adoption
6. Add CLI commands (Commit 6) - User interface

---

## Rollback Strategy

Each commit can be independently reverted if issues arise:
- Commit 1: Remove markers (non-breaking)
- Commit 2: Remove plugin registration
- Commit 3: Remove reporter code
- Commit 4: Remove tests
- Commit 5: Remove documentation
- Commit 6: Remove CLI commands

---

## Next Phase: Phase 1c (Future)

After Phase 1b is complete:
- Historical score tracking
- Phoenix integration for snapshots
- Regression detection
- Custom scoring functions
- Dashboard/visualization

---

## Questions for Clarification

Before implementing, consider:

1. **Marker Coverage**: Should ALL existing tests be marked, or start with critical ones?
   - Recommendation: Start with core_tests.py and offline tests (65 tests)

2. **Fail Threshold**: What compliance score should fail CI?
   - Recommendation: Configurable, default 80%

3. **Report Location**: Where should reports be saved?
   - Recommendation: `.compliance/` directory with timestamp

4. **HTML Report**: Include visualization/charts?
   - Recommendation: Simple table initially, enhance later
