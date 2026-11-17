# Pytest Plugin Loading: Issue & Resolution

**Date:** 2026-11-16  
**Component:** Phase 1b - Pytest Integration  
**Status:** ✅ Resolved

## Problem

After implementing Phase 1b's pytest plugin for compliance tracking, the `--compliance-report` CLI flag was not recognized by pytest, even though:
- The plugin was correctly registered in `pyproject.toml` via the `pytest11` entry point
- The plugin module could be imported manually without errors
- Tests were running but the compliance reporting functionality didn't work

### Error Symptoms

```
pytest: error: unrecognized arguments: --compliance-report
```

Additionally:
- 56 warnings about "Unknown pytest.mark" markers (T1_setup, T2_upload, etc.)
- One test failure in `test_reporter_missing_results_file` due to incomplete test spec

## Root Causes

### 1. Incorrect Pytest Plugin Architecture

**The Problem:**
The plugin attempted to use a class-based approach where the `CompliancePlugin` class had methods named `pytest_addoption()` and `pytest_configure()`. However, pytest's plugin system requires:
- Either module-level hook functions (`def pytest_addoption(parser):`)
- Or a properly instantiated class registered via `config.pluginmanager.register()`

The entry point `compliance = "agent_evals.pytest_plugin"` loads the **module**, not a class instance. When pytest looks for hooks, it expects either:
1. Module-level functions matching the hook names
2. A `pytest_plugins` list pointing to objects with hook methods

**What Was Happening:**
- Entry point loaded the module successfully
- Pytest couldn't find `pytest_addoption` at module level (it was on the class)
- The `--compliance-report` option was never registered
- When the code tried to get the option in `pytest_configure`, it failed with "unrecognized arguments"

### 2. Marker Registration

Pytest doesn't auto-discover custom markers. Without registration, it warns about unknown markers even though they work. Markers need to be registered in:
- `pytest.ini`, `setup.cfg`, or
- `pyproject.toml` under `[tool.pytest.ini_options]`

### 3. Test Spec Validation

The test `test_reporter_missing_results_file` created a minimal spec YAML with only `metadata` but the validator requires a `requirements` key. The test failed before even checking for the missing results file.

## Solution

### 1. Refactored Plugin to Use Module-Level Hooks

**Changed from:**
```python
class CompliancePlugin:
    def pytest_addoption(self, parser):
        parser.addoption(...)
    
    def pytest_configure(self, config):
        ...
```

**Changed to:**
```python
# Module-level hooks that pytest discovers
def pytest_addoption(parser):
    """Module-level hook to add pytest command line options."""
    parser.addoption(...)

def pytest_configure(config):
    """Module-level hook to configure the plugin."""
    plugin = _get_plugin()
    plugin._configure(config)

# Internal class methods (renamed to private)
class CompliancePlugin:
    def _configure(self, config):
        """Configure the plugin instance."""
        ...
```

**Key Pattern:**
- Module-level hook functions are discovered by pytest via entry points
- They delegate to a plugin instance stored in module state (`_compliance_plugin`)
- Internal methods on the class are renamed to private (`_configure`, `_collection_finish`, etc.)
- Added a `_get_plugin()` function to lazily initialize the plugin instance

### 2. Registered All Markers in `pyproject.toml`

Added all T-ID and ASSURANCE markers to eliminate warnings:
```toml
[tool.pytest.ini_options]
markers = [
    "T1_setup: T1 - Core setup and configuration",
    "T2_upload: T2 - Artifact upload and management",
    # ... 25 more markers
]
```

### 3. Fixed Test Spec

Updated `test_reporter_missing_results_file` to include required `requirements` section:
```python
spec_file.write_text("""
metadata:
  version: "1.0"
requirements:
  - id: T1
    description: "Test"
    weight: 1.0
    test_markers: [T1_test]
""")
```

### 4. Added `.compliance_results.json` to `.gitignore`

The compliance report JSON is a generated artifact (like `.coverage`), not source code:
```
# compliance reporting artifacts
.compliance_results.json
```

## Verification

After these changes:

✅ `pytest --compliance-report` works correctly  
✅ Compliance reports generate successfully  
✅ All 166 tests pass  
✅ No unknown marker warnings  
✅ Plugin loads as `agent-evals-0.1.0`

**Test Command:**
```bash
pytest tests/test_core.py::test_t03_records_exact_tool_names_and_arguments --compliance-report
```

**Output:** `.compliance_results.json` containing:
```json
{
  "summary": {
    "total_marked_tests": 1,
    "total_markers": 2,
    "passed": 1,
    "failed": 0,
    "skipped": 0
  },
  "marker_results": {
    "T3_protocol": {...},
    "T3_tool_arguments": {...}
  },
  "test_results": {
    "test_t03_records_exact_tool_names_and_arguments": "pass"
  }
}
```

## Learning Points

### For Future Pytest Plugin Development

1. **Pytest Discovery Mechanism**
   - Entry point loads the module (not instantiates a class)
   - Pytest looks for module-level hook functions
   - Hook names are fixed: `pytest_addoption`, `pytest_configure`, etc.
   - Use class methods only if you register the class instance manually

2. **Module-Level State Management**
   - Use module-level variables with global declarations for plugin state
   - Lazy initialize via helper functions to avoid timing issues
   - Pattern: `_global_instance`, `_get_instance()` function, module-level hooks

3. **Marker Registration**
   - Always register custom markers in `pyproject.toml` or pytest config
   - Format: `"MARKER_NAME: Description of what this marker means"`
   - Prevents warnings and documents marker purpose

4. **Configuration Validation**
   - Test fixtures should use realistic data (complete YAML, valid JSON)
   - Minimal specs for testing should still pass validation rules
   - Consider using factory functions for test spec creation

## Files Modified

- `agent_evals/pytest_plugin.py` - Refactored to module-level hooks
- `tests/test_pytest_plugin.py` - Fixed test spec, removed obsolete tests
- `pyproject.toml` - Added marker registration, confirmed entry point
- `.gitignore` - Added compliance results file

## Commit

```
fix: Correct pytest plugin loading and marker registration

Changes:
- Refactored pytest plugin to use module-level hooks
- Fixed entry point loading mechanism
- Registered all T-ID and ASSURANCE markers
- Updated test spec to include required fields
- Added compliance results to .gitignore

Result: pytest --compliance-report now works correctly
```

---

**Related Documentation:**
- Phase 1b Implementation: `PHASE_1b_PYTEST_INTEGRATION.md`
- Phase 1b Completion: `PHASE_1b_COMPLETION_SUMMARY.md`
- Pytest Plugin Entry Points: https://docs.pytest.org/en/stable/how-to/plugins.html
