---
title: "Phase 1b: CI/CD Integration Guide"
parent: Phase 1b
grand_parent: Progress records
---

{% raw %}# Phase 1b: CI/CD Integration Guide

**Date:** 16 November 2026  
**Purpose:** Integrate compliance tracking into CI/CD pipelines  
**Supported Platforms:** GitHub Actions, GitLab CI, Jenkins, Generic CI/CD

---

## GitHub Actions Example

### Basic Workflow

Create `.github/workflows/compliance.yml`:

```yaml
name: Compliance Check

on:
  push:
    branches: [ main, develop, feat_* ]
  pull_request:
    branches: [ main, develop ]

jobs:
  compliance:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ["3.12"]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[test]"
      
      - name: Run tests with compliance report
        run: |
          pytest tests/ --compliance-report \
            --compliance-report-output compliance_results.json
      
      - name: Generate compliance reports
        if: always()
        run: |
          python -c "
            from agent_evals.compliance_reporter import generate_compliance_report
            from pathlib import Path
            
            # Generate JSON report
            generate_compliance_report(
                spec_file=Path('requirements/t1-t21-spec.yaml'),
                results_file=Path('compliance_results.json'),
                format='json',
                output_file=Path('compliance_report.json')
            )
            
            # Generate HTML report
            generate_compliance_report(
                spec_file=Path('requirements/t1-t21-spec.yaml'),
                results_file=Path('compliance_results.json'),
                format='html',
                output_file=Path('compliance_report.html')
            )
          "
      
      - name: Upload compliance reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: compliance-reports
          path: compliance_report.*
      
      - name: Comment PR with compliance score
        if: github.event_name == 'pull_request' && always()
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('compliance_report.json'));
            const score = report.compliance_score;
            
            const comment = `### Compliance Report
            
            **Overall Score:** ${score.percentage}
            
            | Metric | Value |
            |--------|-------|
            | Tests Passed | ${report.summary.passed} |
            | Tests Failed | ${report.summary.failed} |
            | Tests Skipped | ${report.summary.skipped} |
            | Total Requirements | ${report.summary.total_requirements} |
            
            [View full report](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})`;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

### With Compliance Gate

Add to `compliance.yml` to fail on threshold:

```yaml
      - name: Check compliance threshold
        run: |
          python -c "
            import json
            with open('compliance_report.json') as f:
                report = json.load(f)
            
            score = report['compliance_score']['overall_score']
            threshold = 0.80  # 80%
            
            print(f'Compliance Score: {score*100:.2f}%')
            print(f'Threshold: {threshold*100:.2f}%')
            
            if score < threshold:
                print(f'ERROR: Compliance below threshold!')
                exit(1)
            else:
                print('SUCCESS: Compliance meets threshold')
                exit(0)
          "
```

---

## GitLab CI Example

Create `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - report

test:compliance:
  stage: test
  image: python:3.12
  script:
    - pip install -e ".[test]"
    - pytest tests/ --compliance-report
      --compliance-report-output compliance_results.json
  artifacts:
    reports:
      junit: compliance_results.json
    paths:
      - compliance_results.json
    when: always

report:compliance:
  stage: report
  image: python:3.12
  dependencies:
    - test:compliance
  script:
    - pip install -e ".[test]"
    - python -c "
        from agent_evals.compliance_reporter import generate_compliance_report
        from pathlib import Path
        import json
        
        # Generate HTML report
        generate_compliance_report(
            spec_file=Path('requirements/t1-t21-spec.yaml'),
            results_file=Path('compliance_results.json'),
            format='html',
            output_file=Path('compliance_report.html')
        )
        
        # Check threshold
        with open('compliance_results.json') as f:
            results = json.load(f)
        
        # Extract marker outcomes and calculate score
        from agent_evals.spec_assurance import calculate_compliance_score, load_spec_from_yaml
        
        spec = load_spec_from_yaml('requirements/t1-t21-spec.yaml')
        marker_outcomes = {}
        
        for marker, data in results.get('marker_results', {}).items():
            if data.get('total', 0) == 0:
                outcome = 'skip'
            elif data.get('failed', 0) > 0:
                outcome = 'fail'
            else:
                outcome = 'pass'
            marker_outcomes[marker] = outcome
        
        score_result = calculate_compliance_score(spec, marker_outcomes)
        score = score_result['overall_score']
        threshold = 0.80
        
        print(f'Compliance Score: {score*100:.2f}%')
        
        if score < threshold:
            print(f'ERROR: Score {score*100:.2f}% below threshold {threshold*100:.2f}%')
            exit(1)
      "
  artifacts:
    paths:
      - compliance_report.html
    when: always
  allow_failure: false
```

---

## Jenkins Example

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any
    
    stages {
        stage('Install') {
            steps {
                sh '''
                    python -m venv venv
                    . venv/bin/activate
                    pip install -e ".[test]"
                '''
            }
        }
        
        stage('Test & Compliance') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/ --compliance-report \
                        --compliance-report-output compliance_results.json \
                        --junitxml=test-results.xml
                '''
            }
        }
        
        stage('Generate Reports') {
            steps {
                sh '''
                    . venv/bin/activate
                    python -c "
                        from agent_evals.compliance_reporter import generate_compliance_report
                        from pathlib import Path
                        
                        generate_compliance_report(
                            spec_file=Path('requirements/t1-t21-spec.yaml'),
                            results_file=Path('compliance_results.json'),
                            format='html',
                            output_file=Path('compliance_report.html')
                        )
                    "
                '''
            }
        }
        
        stage('Check Compliance') {
            steps {
                sh '''
                    . venv/bin/activate
                    python scripts/check_compliance.py \
                        compliance_results.json \
                        --threshold 80
                '''
            }
        }
    }
    
    post {
        always {
            junit 'test-results.xml'
            publishHTML([
                reportDir: '.',
                reportFiles: 'compliance_report.html',
                reportName: 'Compliance Report'
            ])
            archiveArtifacts artifacts: 'compliance_*.json,compliance_*.html'
        }
    }
}
```

---

## Compliance Check Script

Create `scripts/check_compliance.py`:

```python
#!/usr/bin/env python3
"""Check if compliance score meets threshold.

Usage:
    python check_compliance.py <results_file> [--threshold THRESHOLD]
"""

import json
import sys
from pathlib import Path
from argparse import ArgumentParser

def check_compliance(results_file: Path, threshold: float = 0.80) -> bool:
    """Check if compliance score meets threshold.
    
    Args:
        results_file: Path to compliance_results.json
        threshold: Minimum score (0.0-1.0)
        
    Returns:
        True if score meets threshold, False otherwise
    """
    if not results_file.exists():
        print(f"ERROR: Results file not found: {results_file}")
        return False
    
    # Load compliance results
    with open(results_file) as f:
        results = json.load(f)
    
    # Import after checking file exists
    from agent_evals.spec_assurance import calculate_compliance_score, load_spec_from_yaml
    
    # Load spec
    spec = load_spec_from_yaml(Path("requirements/t1-t21-spec.yaml"))
    
    # Build marker outcomes from results
    marker_outcomes = {}
    for marker, data in results.get("marker_results", {}).items():
        total = data.get("total", 0)
        passed = data.get("passed", 0)
        failed = data.get("failed", 0)
        
        if total == 0:
            outcome = "skip"
        elif failed > 0:
            outcome = "fail"
        else:
            outcome = "pass"
        
        marker_outcomes[marker] = outcome
    
    # Calculate score
    score_result = calculate_compliance_score(spec, marker_outcomes)
    score = score_result["overall_score"]
    
    # Print report
    print("=" * 60)
    print("COMPLIANCE CHECK REPORT")
    print("=" * 60)
    print(f"Score: {score*100:.2f}%")
    print(f"Threshold: {threshold*100:.2f}%")
    print(f"Tests Passed: {score_result['aggregate']['total_pass']}")
    print(f"Tests Failed: {score_result['aggregate']['total_fail']}")
    print(f"Tests Skipped: {score_result['aggregate']['total_skip']}")
    print("=" * 60)
    
    # Check threshold
    if score >= threshold:
        print(f"SUCCESS: Score meets threshold ({score*100:.2f}% >= {threshold*100:.2f}%)")
        return True
    else:
        print(f"FAILURE: Score below threshold ({score*100:.2f}% < {threshold*100:.2f}%)")
        return False


if __name__ == "__main__":
    parser = ArgumentParser(description="Check compliance score")
    parser.add_argument("results_file", type=Path, help="Path to compliance_results.json")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.80,
        help="Minimum score threshold (0-100 or 0.0-1.0)"
    )
    
    args = parser.parse_args()
    
    # Normalize threshold to 0.0-1.0 range
    threshold = args.threshold
    if threshold > 1.0:
        threshold = threshold / 100.0
    
    # Run check
    success = check_compliance(args.results_file, threshold)
    sys.exit(0 if success else 1)
```

---

## Usage Examples

### Run Tests and Generate Compliance

```bash
# Local development
pytest tests/ --compliance-report --compliance-verbose

# View report
cat compliance_report.json
python -m json.tool compliance_report.json
```

### Generate Multiple Report Formats

```bash
# After running tests
pytest tests/ --compliance-report

# Generate JSON
python -c "
  from agent_evals.compliance_reporter import generate_compliance_report
  from pathlib import Path
  generate_compliance_report(
      Path('requirements/t1-t21-spec.yaml'),
      Path('compliance_results.json'),
      format='json',
      output_file=Path('report.json')
  )
"

# Generate HTML
python -c "
  from agent_evals.compliance_reporter import generate_compliance_report
  from pathlib import Path
  generate_compliance_report(
      Path('requirements/t1-t21-spec.yaml'),
      Path('compliance_results.json'),
      format='html',
      output_file=Path('report.html')
  )
"

# View in browser
open report.html  # macOS
xdg-open report.html  # Linux
start report.html  # Windows
```

### Check Compliance Locally

```bash
python scripts/check_compliance.py compliance_results.json --threshold 80
```

---

## Artifact Storage

### Store Reports in Cloud

```yaml
# GitHub Actions
- name: Upload to S3
  run: aws s3 cp compliance_report.html s3://my-bucket/compliance/

# GitLab CI
artifacts:
  paths:
    - compliance_report.html
  expire_in: 30 days
```

### Persist Historical Data

Track compliance scores over time:

```bash
# Archive by date
mkdir -p compliance_history/$(date +%Y-%m-%d)
cp compliance_report.json compliance_history/$(date +%Y-%m-%d)/
cp compliance_results.json compliance_history/$(date +%Y-%m-%d)/

# Compare across runs
python scripts/compare_compliance.py \
  compliance_history/2026-11-15/ \
  compliance_history/2026-11-16/
```

---

## Troubleshooting CI/CD Integration

### Workflow Fails at Report Generation

**Problem:** "ModuleNotFoundError: No module named 'agent_evals'"

**Solution:** Ensure dependencies are installed before running compliance scripts
```yaml
- pip install -e .
- pip install -e ".[test]"
```

### Artifact Upload Fails

**Problem:** "No files matching pattern"

**Solution:** Verify reports are generated before upload
```bash
ls -la compliance_*.* 2>&1 || echo "No compliance reports found"
pytest tests/ --compliance-report -v
```

### Threshold Check Always Passes

**Problem:** Compliance check doesn't fail even below threshold

**Solution:** Verify exit code handling
```bash
python scripts/check_compliance.py ... || exit 1
```

---

## Best Practices

1. **Run on Every PR:** Catch regressions before merge
2. **Archive Reports:** Store historical data for trending
3. **Notify Team:** Comment on PR with score change
4. **Set Reasonable Threshold:** Start at current score, gradually increase
5. **Review Failures:** Investigate CI failures with detailed logs
6. **Monitor Trends:** Track score over time (Phase 1c feature)

---

## Related Sections

- [Pytest Integration Guide](PHASE_1b_PYTEST_INTEGRATION.md)
- [Phase 1a: Scoring Engine](../phase-1a/PHASE_1_IMPLEMENTATION.md)
- [Requirements Specification](https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course/blob/main/requirements/t1-t21-spec.yaml)
{% endraw %}