"""Compliance report generation for spec assurance scoring.

This module loads compliance results (from pytest plugin), calculates compliance
scores, and generates reports in multiple formats.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

from agent_evals.spec_assurance import (
    calculate_compliance_score,
    load_spec_from_yaml,
)


@dataclass
class ComplianceReportData:
    """Data structure for a compliance report."""

    overall_score: float
    per_requirement: Dict[str, Dict[str, Any]]
    aggregate: Dict[str, int]
    test_summary: Dict[str, int]
    spec_file: str
    results_file: str
    

class ComplianceReporter:
    """Base class for compliance report generation."""

    def __init__(self, spec_file: Path, results_file: Path):
        """Initialize reporter.
        
        Args:
            spec_file: Path to requirements specification (YAML)
            results_file: Path to test results JSON file (from pytest plugin)
        """
        self.spec_file = Path(spec_file)
        self.results_file = Path(results_file)
        
        # Load spec
        self.spec = load_spec_from_yaml(self.spec_file)
        
        # Load results
        self.test_results = self._load_test_results()
    
    def _load_test_results(self) -> Dict[str, str]:
        """Load test results from JSON file.
        
        Returns:
            Dict mapping marker names to outcome strings ('pass', 'fail', 'skip')
        """
        if not self.results_file.exists():
            raise FileNotFoundError(f"Results file not found: {self.results_file}")
        
        data = json.loads(self.results_file.read_text())
        return data.get("marker_results", {})
    
    def calculate_compliance(self) -> ComplianceReportData:
        """Calculate compliance score from spec and test results.
        
        Returns:
            ComplianceReportData with scores and details
        """
        # Map test results to expected format for scorer
        marker_outcomes = {}
        for marker_name, marker_data in self.test_results.items():
            # Map marker test results to pass/fail/skip
            if isinstance(marker_data, dict):
                total = marker_data.get("total", 0)
                passed = marker_data.get("passed", 0)
                failed = marker_data.get("failed", 0)
                skipped = marker_data.get("skipped", 0)
                
                # Determine outcome: pass if all passed, fail if any failed, skip if only skipped
                if total == 0:
                    outcome = "skip"
                elif failed > 0:
                    outcome = "fail"
                elif skipped > 0 and passed == 0:
                    outcome = "skip"
                else:
                    outcome = "pass"
                
                marker_outcomes[marker_name] = outcome
        
        # Calculate compliance score
        score_result = calculate_compliance_score(self.spec, marker_outcomes)
        
        return ComplianceReportData(
            overall_score=score_result["overall_score"],
            per_requirement=score_result["per_requirement"],
            aggregate=score_result["aggregate"],
            test_summary={
                "total_pass": score_result["aggregate"]["total_pass"],
                "total_fail": score_result["aggregate"]["total_fail"],
                "total_skip": score_result["aggregate"]["total_skip"],
            },
            spec_file=str(self.spec_file),
            results_file=str(self.results_file),
        )
    
    def generate(self, output_file: Optional[Path] = None) -> str:
        """Generate report (implemented by subclasses).
        
        Args:
            output_file: Optional path to write report to
            
        Returns:
            Report content as string
        """
        raise NotImplementedError("Subclasses must implement generate()")


class JSONReporter(ComplianceReporter):
    """Reporter that generates JSON compliance reports."""

    def generate(self, output_file: Optional[Path] = None) -> str:
        """Generate JSON report.
        
        Args:
            output_file: Optional path to write JSON report to
            
        Returns:
            JSON report content
        """
        report_data = self.calculate_compliance()
        
        output = {
            "metadata": {
                "spec_file": report_data.spec_file,
                "results_file": report_data.results_file,
            },
            "compliance_score": {
                "overall_score": report_data.overall_score,
                "percentage": f"{report_data.overall_score * 100:.2f}%",
            },
            "per_requirement": report_data.per_requirement,
            "summary": {
                "total_requirements": len(report_data.per_requirement),
                "passed": report_data.test_summary.get("total_pass", 0),
                "failed": report_data.test_summary.get("total_fail", 0),
                "skipped": report_data.test_summary.get("total_skip", 0),
            },
        }
        
        content = json.dumps(output, indent=2)
        
        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            Path(output_file).write_text(content)
        
        return content


class ConsoleReporter(ComplianceReporter):
    """Reporter that generates human-readable console output."""

    def generate(self, output_file: Optional[Path] = None) -> str:
        """Generate console report.
        
        Args:
            output_file: Optional path to write report to
            
        Returns:
            Formatted console report
        """
        report_data = self.calculate_compliance()
        
        lines = []
        lines.append("=" * 70)
        lines.append("COMPLIANCE ASSURANCE REPORT")
        lines.append("=" * 70)
        lines.append("")
        
        # Overall score
        score_pct = report_data.overall_score * 100
        lines.append(f"Overall Score: {report_data.overall_score:.4f} ({score_pct:.2f}%)")
        lines.append("")
        
        # Summary
        lines.append("Summary:")
        lines.append(f"  Total Requirements: {len(report_data.per_requirement)}")
        lines.append(f"  Passed: {report_data.test_summary.get('total_pass', 0)}")
        lines.append(f"  Failed: {report_data.test_summary.get('total_fail', 0)}")
        lines.append(f"  Skipped: {report_data.test_summary.get('total_skip', 0)}")
        lines.append("")
        
        # Per-requirement details
        lines.append("Per-Requirement Scores:")
        lines.append("-" * 70)
        lines.append(f"{'Requirement':<15} {'Score':<10} {'Tests':<20} {'Status':<20}")
        lines.append("-" * 70)
        
        for req_id in sorted(report_data.per_requirement.keys()):
            req = report_data.per_requirement[req_id]
            score = req.get("score", 0)
            tests_info = f"{req.get('tests_passed', 0)}P/{req.get('tests_failed', 0)}F"
            
            if score >= 1.0:
                status = "PASS"
            elif score >= 0.75:
                status = "MOSTLY OK"
            elif score >= 0.5:
                status = "PARTIAL"
            elif score > 0:
                status = "INDIRECT"
            else:
                status = "NOT COVERED"
            
            lines.append(f"{req_id:<15} {score:<10.4f} {tests_info:<20} {status:<20}")
        
        lines.append("-" * 70)
        lines.append("")
        lines.append("=" * 70)
        
        content = "\n".join(lines)
        
        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            Path(output_file).write_text(content)
        
        return content


class HTMLReporter(ComplianceReporter):
    """Reporter that generates HTML compliance reports."""

    def generate(self, output_file: Optional[Path] = None) -> str:
        """Generate HTML report.
        
        Args:
            output_file: Optional path to write HTML report to
            
        Returns:
            HTML report content
        """
        report_data = self.calculate_compliance()
        score_pct = report_data.overall_score * 100
        
        # Determine score color
        if score_pct >= 80:
            score_color = "#28a745"  # Green
        elif score_pct >= 50:
            score_color = "#ffc107"  # Yellow
        else:
            score_color = "#dc3545"  # Red
        
        # Build requirements table rows
        req_rows = []
        for req_id in sorted(report_data.per_requirement.keys()):
            req = report_data.per_requirement[req_id]
            score = req.get("score", 0)
            tests_passed = req.get("tests_passed", 0)
            tests_failed = req.get("tests_failed", 0)
            
            # Determine row color
            if score >= 1.0:
                row_color = "#f0f8f4"
            elif score >= 0.75:
                row_color = "#fffbf0"
            elif score > 0:
                row_color = "#fff5f0"
            else:
                row_color = "#fef0f0"
            
            req_rows.append(f"""
            <tr style="background-color: {row_color};">
                <td style="padding: 8px; border: 1px solid #ddd;">{req_id}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{score:.4f}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{tests_passed}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{tests_failed}</td>
            </tr>
            """)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Compliance Assurance Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .score-box {{
            background-color: {score_color};
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 20px;
        }}
        .score-value {{
            font-size: 36px;
            font-weight: bold;
        }}
        .score-label {{
            font-size: 14px;
            margin-top: 5px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        .summary-item {{
            padding: 15px;
            background-color: #f9f9f9;
            border-left: 4px solid #007bff;
            border-radius: 4px;
        }}
        .summary-item h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .summary-item .value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background-color: #007bff;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            padding: 10px;
            border: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f9f9f9;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Compliance Assurance Report</h1>
        
        <div class="score-box">
            <div class="score-value">{score_pct:.2f}%</div>
            <div class="score-label">Overall Compliance Score</div>
        </div>
        
        <div class="summary">
            <div class="summary-item">
                <h3>Requirements</h3>
                <div class="value">{len(report_data.per_requirement)}</div>
            </div>
            <div class="summary-item">
                <h3>Tests Passed</h3>
                <div class="value" style="color: #28a745;">{report_data.test_summary.get('total_pass', 0)}</div>
            </div>
            <div class="summary-item">
                <h3>Tests Failed</h3>
                <div class="value" style="color: #dc3545;">{report_data.test_summary.get('total_fail', 0)}</div>
            </div>
            <div class="summary-item">
                <h3>Tests Skipped</h3>
                <div class="value" style="color: #ffc107;">{report_data.test_summary.get('total_skip', 0)}</div>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Requirement</th>
                    <th style="text-align: center;">Score</th>
                    <th style="text-align: center;">Tests Passed</th>
                    <th style="text-align: center;">Tests Failed</th>
                </tr>
            </thead>
            <tbody>
                {"".join(req_rows)}
            </tbody>
        </table>
        
        <div class="footer">
            <p>Report generated from: {report_data.spec_file}</p>
            <p>Test results from: {report_data.results_file}</p>
        </div>
    </div>
</body>
</html>"""
        
        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            Path(output_file).write_text(html)
        
        return html


def generate_compliance_report(
    spec_file: Path,
    results_file: Path,
    format: str = "json",
    output_file: Optional[Path] = None,
) -> str:
    """Generate a compliance report in the specified format.
    
    Args:
        spec_file: Path to requirements specification YAML
        results_file: Path to test results JSON
        format: Output format ('json', 'html', or 'console')
        output_file: Optional output file path
        
    Returns:
        Report content as string
    """
    reporters = {
        "json": JSONReporter,
        "html": HTMLReporter,
        "console": ConsoleReporter,
    }
    
    if format not in reporters:
        raise ValueError(f"Unknown format: {format}. Must be one of {list(reporters.keys())}")
    
    reporter_class = reporters[format]
    reporter = reporter_class(spec_file, results_file)
    return reporter.generate(output_file)
