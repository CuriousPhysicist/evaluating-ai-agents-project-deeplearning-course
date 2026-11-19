---
title: "CI/CD Compliance Gating - Implementation Plan"
nav_order: 1
---

# CI/CD Compliance Gating - Phase 1c Task 2

**Task:** Set up CI/CD Compliance Gating  
**Priority:** 🔴 HIGH  
**Effort Estimate:** 3-5 days  
**Blocking:** Phase 1c → Phase 1d planning  
**Depends On:** Phase 1b merged to main  
**Status:** Starting development (feature branch: feat_cicd_gating)

---

## 📋 Planned Implementation

### **Phase 1: Core Exit Code Implementation** (Days 1-2)

#### 1.1 Exit Code Contract Definition

**File:** `agent_evals/cli/exit_codes.py` (new)

```python
"""
Exit code definitions for CI/CD integration.

Standards:
- 0 = SUCCESS: All tests pass, compliance above threshold
- 1 = COMPLIANCE_REGRESSION: Scores dropped below threshold
- 2 = CONFIGURATION_ERROR: Invalid config/setup issue
- 3 = TEST_FAILURE: Tests failed (non-compliance)
- 4 = MISSING_BASELINE: No baseline for comparison
"""

EXIT_SUCCESS = 0
EXIT_COMPLIANCE_REGRESSION = 1
EXIT_CONFIGURATION_ERROR = 2
EXIT_TEST_FAILURE = 3
EXIT_MISSING_BASELINE = 4

class ExitCodeReason(Enum):
    """Detailed reason for exit code (for logging)"""
    SUCCESS = "All tests passed and compliance met"
    REGRESSION_SCORE = "Overall compliance score below threshold"
    REGRESSION_REQUIREMENT = "Individual requirement score decreased"
    CONFIG_MISSING_SPEC = "Specification file not found"
    CONFIG_INVALID_YAML = "Invalid specification YAML"
    CONFIG_INVALID_THRESHOLD = "Invalid threshold configuration"
    TEST_COLLECTION_FAILED = "Pytest test collection failed"
    TEST_EXECUTION_FAILED = "Tests failed during execution"
    BASELINE_MISSING = "No baseline for comparison"
```

#### 1.2 Threshold Configuration

**File:** `specifications/compliance/threshold.yaml` (new)

```yaml
# Compliance Gating Thresholds
# Used by CI/CD pipeline to determine pass/fail

defaults:
  overall_score: 0.80      # Overall compliance must be >= 80%
  per_requirement: 0.50    # Each requirement must be >= 50%
  regression_allowed: 0.05 # Allow max 5% regression from baseline

environments:
  development:
    overall_score: 0.70
    per_requirement: 0.40
    regression_allowed: 0.10
  
  staging:
    overall_score: 0.80
    per_requirement: 0.50
    regression_allowed: 0.05
  
  production:
    overall_score: 0.90
    per_requirement: 0.75
    regression_allowed: 0.00

# Baseline scores for regression detection
baselines:
  current:
    version: "main"
    commit: null  # Will be set at runtime
    overall_score: 0.9048
    timestamp: "2026-11-19T00:00:00Z"
```

#### 1.3 CLI Integration

**File:** `agent_evals/cli/commands.py` (modify)

Add new command: `agent_evals check --threshold-config=<file> [--baseline=<version>]`

```python
@click.command()
@click.option('--threshold-config', 
              type=click.Path(exists=True),
              default='specifications/compliance/threshold.yaml',
              help='Path to threshold configuration file')
@click.option('--baseline',
              default='current',
              help='Baseline version for regression detection')
@click.option('--environment',
              type=click.Choice(['development', 'staging', 'production']),
              default='development',
              help='Environment for threshold selection')
def check(threshold_config: str, baseline: str, environment: str) -> int:
    """
    Check compliance scores against configured thresholds.
    
    Exit codes:
        0 = Pass (scores above threshold)
        1 = Compliance regression detected
        2 = Configuration error
        3 = Test execution failed
        4 = Missing baseline for comparison
    """
    # Implementation here
    return exit_code
```

**Features:**
- Load latest compliance scores from last test run
- Compare against configured thresholds
- Detect regressions vs baseline
- Return appropriate exit code
- Write detailed report to stdout/file

---

### **Phase 2: CI/CD Integration Examples** (Days 2-3)

#### 2.1 GitHub Actions Workflow

**File:** `.github/workflows/compliance-check.yml` (new)

```yaml
name: Compliance Check

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  compliance:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest
      
      - name: Run tests
        run: pytest tests/ -v --tb=short
      
      - name: Check compliance
        run: |
          agent_evals check \
            --threshold-config=specifications/compliance/threshold.yaml \
            --environment=staging \
            --baseline=main
        continue-on-error: false
      
      - name: Comment on PR
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: 'Compliance check failed. See workflow logs for details.'
            })
```

#### 2.2 GitLab CI Configuration

**File:** `.gitlab-ci.yml` (modify/create)

```yaml
stages:
  - test
  - compliance

compliance:check:
  stage: compliance
  script:
    - pip install -e .
    - pytest tests/ -v
    - agent_evals check \
        --threshold-config=specifications/compliance/threshold.yaml \
        --environment=staging \
        --baseline=origin/main
  only:
    - merge_requests
    - main
  allow_failure: false
```

#### 2.3 Jenkins Pipeline

**File:** `Jenkinsfile` (new)

```groovy
pipeline {
    agent any
    
    stages {
        stage('Test') {
            steps {
                sh '''
                    python -m pip install -e .
                    pytest tests/ -v --junit-xml=test-results.xml
                '''
            }
        }
        
        stage('Compliance Check') {
            steps {
                script {
                    int exitCode = sh(
                        script: '''
                            agent_evals check \\
                              --threshold-config=specifications/compliance/threshold.yaml \\
                              --environment=production \\
                              --baseline=${GIT_COMMIT}
                        ''',
                        returnStatus: true
                    )
                    
                    if (exitCode == 1) {
                        error("Compliance regression detected")
                    } else if (exitCode == 2) {
                        error("Configuration error")
                    } else if (exitCode != 0) {
                        error("Compliance check failed with code: ${exitCode}")
                    }
                }
            }
        }
    }
    
    post {
        always {
            junit 'test-results.xml'
            publishHTML([
                reportDir: 'compliance-report',
                reportFiles: 'index.html',
                reportName: 'Compliance Report'
            ])
        }
    }
}
```

---

### **Phase 3: Implementation & Testing** (Days 3-5)

#### 3.1 Implementation Tasks

**File Structure:**
```
agent_evals/
├── cli/
│   ├── exit_codes.py (NEW)
│   ├── compliance_check.py (NEW)
│   └── commands.py (MODIFY - add check command)
├── compliance/
│   ├── threshold_manager.py (NEW)
│   ├── regression_detector.py (NEW)
│   └── reporter.py (MODIFY - add exit code reporting)

specifications/
├── compliance/
│   ├── threshold.yaml (NEW)
│   └── schema.json (may need threshold schema)

.github/
├── workflows/
│   └── compliance-check.yml (NEW)

tests/
├── test_exit_codes.py (NEW)
├── test_threshold_config.py (NEW)
└── test_compliance_check_command.py (NEW)
```

#### 3.2 Key Implementation Areas

**A. Threshold Manager**
- Load and validate threshold config (YAML)
- Select thresholds by environment
- Apply to current scores
- Return pass/fail decision

**B. Regression Detector**
- Load baseline scores
- Compare current vs baseline
- Calculate regression magnitude
- Flag problematic changes

**C. Compliance Check Command**
- Load test results
- Calculate compliance scores
- Load threshold configuration
- Compare scores to thresholds
- Determine exit code
- Generate report
- Return appropriate code

**D. Exit Code Reporting**
- Include exit code in all outputs
- Document reasons in logs
- Support JSON reporting for parsing

---

### **Phase 4: Documentation** (Days 4-5)

#### 4.1 Configuration Guide

**File:** `docs/progress/phase-1b/CICD_GATING_CONFIGURATION.md` (new)

Topics:
- Threshold configuration syntax
- Environment-specific settings
- Baseline management
- Customization examples

#### 4.2 Integration Guide

**File:** `docs/progress/phase-1b/CICD_GATING_INTEGRATION.md` (new)

Topics:
- Exit code reference
- GitHub Actions setup
- GitLab CI setup
- Jenkins setup
- Troubleshooting

#### 4.3 Best Practices

**File:** `docs/progress/phase-1b/CICD_GATING_BEST_PRACTICES.md` (new)

Topics:
- Threshold selection guidance
- Regression allowance rationale
- Environment-specific strategies
- Failure handling

---

## 🎯 Success Criteria

**Core Implementation:**
- ✅ Exit code contract defined and implemented
- ✅ Threshold configuration system working
- ✅ CLI `check` command functional
- ✅ At least 2 CI/CD examples (GitHub Actions, GitLab CI)

**Testing:**
- ✅ All exit codes tested (0, 1, 2, 3, 4)
- ✅ Threshold logic verified
- ✅ Regression detection working
- ✅ Zero false positives in baseline case

**Documentation:**
- ✅ Configuration guide complete
- ✅ Integration examples working
- ✅ Troubleshooting guide provided
- ✅ Best practices documented

**Integration:**
- ✅ CI/CD workflows can be enabled
- ✅ Exit codes used for pipeline gating
- ✅ Reports generated in CI/CD context

---

## 📝 Deliverables

| Item | Type | Status |
|------|------|--------|
| `agent_evals/cli/exit_codes.py` | Code | Planned |
| `agent_evals/cli/compliance_check.py` | Code | Planned |
| `specifications/compliance/threshold.yaml` | Config | Planned |
| `.github/workflows/compliance-check.yml` | Config | Planned |
| `.gitlab-ci.yml` | Config | Planned |
| `Jenkinsfile` | Config | Planned |
| `tests/test_exit_codes.py` | Tests | Planned |
| `tests/test_compliance_check_command.py` | Tests | Planned |
| `docs/.../CICD_GATING_CONFIGURATION.md` | Docs | Planned |
| `docs/.../CICD_GATING_INTEGRATION.md` | Docs | Planned |
| `docs/.../CICD_GATING_BEST_PRACTICES.md` | Docs | Planned |

---

## 🔄 Development Workflow

**Branch:** `feat_cicd_gating`  
**Base:** `main`  
**Strategy:** Feature branch with daily commits

**Commit Pattern:**
```
feat: Add exit code contract definition
feat: Implement threshold configuration manager
feat: Add compliance check CLI command
feat: Add GitHub Actions workflow example
feat: Add GitLab CI example
feat: Add Jenkins pipeline example
test: Add comprehensive exit code tests
docs: Add CI/CD gating configuration guide
docs: Add CI/CD integration examples
docs: Add best practices guide
```

**Testing Strategy:**
- Unit tests for each module (day 3)
- Integration tests for CLI (day 4)
- Manual CI/CD validation (day 5)

---

## 🚀 Next Steps

1. ✅ Create feature branch: `feat_cicd_gating`
2. ⏳ Implement Phase 1 (Exit codes) - Days 1-2
3. ⏳ Implement Phase 2 (CI/CD examples) - Days 2-3
4. ⏳ Implement Phase 3 (Full integration) - Days 3-5
5. ⏳ Document Phase 4 - Days 4-5
6. ⏳ Code review and merge to main

---

**Created:** 19 November 2026  
**Author:** Copilot  
**Purpose:** Implementation guide for CI/CD compliance gating feature
