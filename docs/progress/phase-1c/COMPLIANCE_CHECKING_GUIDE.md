---
title: "Compliance Checking Guide"
nav_order: 3
parent: "Phase 1c - CI/CD Gating"
---

# Compliance Checking Guide

This guide explains how to use the compliance checking framework to validate evaluation compliance scores against configured thresholds.

## Quick Start

### 1. Load Configuration

```python
from agent_evals.cli.compliance_check import ThresholdConfig, ComplianceChecker

# Load threshold configuration from YAML
config = ThresholdConfig('specifications/compliance/threshold.yaml')
```

### 2. Run Compliance Check

```python
# Create a checker
checker = ComplianceChecker(config)

# Check compliance scores
result = checker.check(
    overall_score=0.85,
    per_requirement_scores={'T1': 0.90, 'T2': 0.80},
    environment='staging',
    baseline_name='current'
)
```

### 3. Handle Results

```python
# Check exit code
if result.exit_code == 0:
    print("✅ Compliance check passed")
else:
    print(f"❌ Compliance check failed: {result.message}")
    print(f"   Reason: {result.reason.value}")
    if result.regression_magnitude:
        print(f"   Regression: {result.regression_magnitude:.2%}")

# Use in CI/CD
exit(result.exit_code)
```

## Configuration Structure

### File: `specifications/compliance/threshold.yaml`

```yaml
defaults:
  overall_score: 0.80        # Minimum overall compliance
  per_requirement: 0.50      # Minimum per-requirement score
  regression_allowed: 0.05   # Maximum regression tolerance

environments:
  development:               # For development branches
    overall_score: 0.70
    per_requirement: 0.40
    regression_allowed: 0.10
  
  staging:                   # For pre-release validation
    overall_score: 0.80
    per_requirement: 0.50
    regression_allowed: 0.05
  
  production:                # For production release gates
    overall_score: 0.90
    per_requirement: 0.75
    regression_allowed: 0.00

baselines:
  current:                   # Baseline for regression detection
    version: "main"
    commit: null
    overall_score: 0.9048
    timestamp: "2026-11-19T00:00:00Z"
```

## Exit Codes

The compliance checking system returns standardized exit codes:

| Code | Name | Meaning |
|------|------|---------|
| 0 | SUCCESS | All checks passed ✅ |
| 1 | COMPLIANCE_REGRESSION | Score below threshold or regressed ❌ |
| 2 | CONFIGURATION_ERROR | Invalid config/setup 🔧 |
| 3 | TEST_FAILURE | Test execution failed 💥 |
| 4 | MISSING_BASELINE | No baseline for comparison ⚠️ |

## Detailed Failure Reasons

The `ComplianceCheckResult.reason` field provides detailed failure information:

**Success:**
- `SUCCESS` - All tests passed and compliance met

**Regressions:**
- `REGRESSION_OVERALL` - Overall score below threshold
- `REGRESSION_REQUIREMENT` - Individual requirement score decreased
- `REGRESSION_MAGNITUDE` - Regression exceeded allowed tolerance

**Configuration Errors:**
- `CONFIG_MISSING_THRESHOLD` - Threshold config file not found
- `CONFIG_INVALID_YAML` - Invalid YAML syntax
- `CONFIG_INVALID_THRESHOLD` - Invalid threshold values
- `CONFIG_MISSING_ENVIRONMENT` - Environment not in config
- `CONFIG_MISSING_SPEC` - Specification file not found

**Test Errors:**
- `TEST_COLLECTION_FAILED` - Pytest collection failed
- `TEST_EXECUTION_FAILED` - Tests failed during execution
- `TEST_RESULTS_MISSING` - Results file not found

**Baseline Issues:**
- `BASELINE_NOT_FOUND` - Specified baseline not found
- `BASELINE_LOAD_ERROR` - Error loading baseline
- `BASELINE_INVALID` - Baseline data corrupted

## Compliance Result Fields

```python
ComplianceCheckResult(
    exit_code: int              # 0-4 for decision making
    reason: ComplianceFailureReason  # Detailed reason enum
    message: str                # Human-readable explanation
    overall_score: float        # Current compliance score (0.0-1.0)
    threshold: float            # Applied threshold (0.0-1.0)
    regression_magnitude: float # Regression amount if applicable
    details: dict               # Additional details (failed requirements, etc.)
)
```

### Result Methods

```python
# String representation for logging
print(result)
# Output:
# Exit Code: 1
# Reason: Compliance regression detected
# Message: ...
# Overall Score: 85.00%
# Threshold: 90.00%
# Regression: 1.48%

# Dictionary for JSON serialization
result_dict = result.to_dict()
json.dump(result_dict, file)
```

## Usage Examples

### Example 1: Check Development Build

```python
from agent_evals.cli.compliance_check import ThresholdConfig, ComplianceChecker

config = ThresholdConfig('specifications/compliance/threshold.yaml')
checker = ComplianceChecker(config)

# Development has 70% threshold, 10% regression tolerance
result = checker.check(
    overall_score=0.75,
    environment='development'
)

print(f"Exit: {result.exit_code}, Score: {result.overall_score:.1%}")
```

### Example 2: Check Staging with Per-Requirement Scores

```python
config = ThresholdConfig('specifications/compliance/threshold.yaml')
checker = ComplianceChecker(config)

per_requirement = {
    'T1': 0.95,  # Excellent
    'T2': 0.80,  # Good
    'T3': 0.45,  # Below 50% threshold
}

result = checker.check(
    overall_score=0.73,  # Average of per-requirement scores
    per_requirement_scores=per_requirement,
    environment='staging'
)

if result.exit_code != 0:
    print(f"Failed requirements: {result.details['failed_requirements']}")
```

### Example 3: Check Production with Regression Detection

```python
config = ThresholdConfig('specifications/compliance/threshold.yaml')
checker = ComplianceChecker(config)

# Production: 90% threshold, ZERO regression tolerance
result = checker.check(
    overall_score=0.9050,  # Barely above baseline
    environment='production',
    baseline_name='current'
)

if result.regression_magnitude:
    print(f"Regression: {result.regression_magnitude:.2%}")
    # Even tiny regressions fail in production
```

### Example 4: CI/CD Integration

```python
import sys
import json
from pathlib import Path
from agent_evals.cli.compliance_check import (
    ThresholdConfig,
    ComplianceChecker,
    load_compliance_results
)

# Load test results from JSON
results_file = '.compliance_results.json'
test_results = load_compliance_results(results_file)

# Load configuration
config = ThresholdConfig('specifications/compliance/threshold.yaml')
checker = ComplianceChecker(config)

# Run check with environment from env variable
environment = os.getenv('CI_ENVIRONMENT', 'staging')
result = checker.check(
    overall_score=test_results['overall_score'],
    per_requirement_scores=test_results.get('per_requirement', {}),
    environment=environment,
    baseline_name='current'
)

# Write report
report = result.to_dict()
with open('compliance-report.json', 'w') as f:
    json.dump(report, f, indent=2)

# Exit with appropriate code
sys.exit(result.exit_code)
```

## Threshold Selection Guide

### Overall Score Thresholds

- **90%+**: Production-ready, all requirements well-covered
- **80-90%**: Good coverage, minor gaps acceptable
- **70-80%**: Acceptable for development, needs improvement
- **<70%**: Significant gaps, blockers likely

### Per-Requirement Score Thresholds

- **75%+**: Well-tested, high confidence
- **50-75%**: Adequate coverage, some gaps
- **<50%**: Weak coverage, high risk

### Regression Tolerance

- **0%**: Zero regression allowed (production, strict enforcement)
- **5%**: 5% regression acceptable (staging, balanced approach)
- **10%+**: Flexible regression (development, experimentation)

## Common Errors

### Configuration File Not Found

```python
ConfigurationError: Threshold configuration file not found
```

**Solution:** Ensure `specifications/compliance/threshold.yaml` exists

### Invalid YAML Syntax

```python
ConfigurationError: Invalid YAML in threshold configuration
```

**Solution:** Validate YAML syntax at [yamllint.com](https://www.yamllint.com/)

### Invalid Threshold Value

```python
ConfigurationError: Invalid threshold value for overall_score: 1.5
```

**Solution:** Thresholds must be between 0.0 and 1.0

### Invalid Score Value

```python
ConfigurationError: Invalid overall score: 1.5
```

**Solution:** Compliance scores must be between 0.0 and 1.0

## Testing

The compliance checking framework includes comprehensive tests:

```bash
# Run compliance checking tests
pytest tests/test_compliance_check.py -v

# Run all CI/CD gating tests
pytest tests/test_exit_codes.py tests/test_compliance_check.py -v
```

## See Also

- [Exit Code Contract](../../CI_CD_GATING_PLAN.md#exit-code-contract-definition)
- [CI/CD Integration Examples](../../CI_CD_INTEGRATION_EXAMPLES.md)
- [Best Practices](../../CI_CD_GATING_BEST_PRACTICES.md)

---

**Last Updated:** 19 November 2026  
**Version:** 1.0
