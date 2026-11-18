"""Tests for pytest plugin and compliance reporter integration."""

from __future__ import annotations

import json
import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import Mock, patch

from agent_evals.pytest_plugin import CompliancePlugin
from agent_evals.cli_compliance import compliance
from agent_evals.pytest_plugin_config import CompliancePluginConfig, load_config_from_dict
from agent_evals.compliance_reporter import (
    JSONReporter,
    ConsoleReporter,
    HTMLReporter,
    generate_compliance_report,
)


class TestCompliancePluginConfig:
    """Test pytest plugin configuration."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = CompliancePluginConfig()
        assert config.report_output == ".compliance_results.json"
        assert config.generate_report is True
        assert config.verbose is False
        assert config.fail_below_threshold is None

    def test_config_from_dict(self):
        """Test loading configuration from dictionary."""
        data = {
            "report_output": "custom_report.json",
            "generate_report": True,
            "verbose": True,
            "fail_below_threshold": 80.0,
        }
        config = load_config_from_dict(data)
        assert config.report_output == "custom_report.json"
        assert config.verbose is True
        assert config.fail_below_threshold == 80.0

    def test_config_threshold_validation(self):
        """Test threshold validation."""
        # Valid values
        config = CompliancePluginConfig(fail_below_threshold=50.0)
        assert config.fail_below_threshold == 50.0

        config = CompliancePluginConfig(fail_below_threshold=0.0)
        assert config.fail_below_threshold == 0.0

        config = CompliancePluginConfig(fail_below_threshold=100.0)
        assert config.fail_below_threshold == 100.0

        # Invalid values
        with pytest.raises(ValueError):
            CompliancePluginConfig(fail_below_threshold=-1.0)

        with pytest.raises(ValueError):
            CompliancePluginConfig(fail_below_threshold=101.0)


def test_compliance_report_uses_relocated_default_spec(tmp_path, monkeypatch):
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    results = tmp_path / "results.json"
    results.write_text(json.dumps({"marker_results": {}, "test_results": {}}), encoding="utf-8")

    result = CliRunner().invoke(compliance, ["report", str(results), "--format", "json"])

    assert result.exit_code == 0, result.output
    assert len(json.loads(result.output)["per_requirement"]) == 21


class TestCompliancePlugin:
    """Test the compliance pytest plugin."""

    def test_plugin_initialization(self):
        """Test plugin initializes correctly."""
        plugin = CompliancePlugin()
        assert plugin.results == {}
        assert plugin.markers == {}
        assert plugin.marker_outcomes == {}
        assert plugin.verbose is False


class TestComplianceReporter:
    """Test compliance report generation."""

    def test_json_reporter_basic(self, tmp_path):
        """Test JSON reporter generates valid output."""
        # Create test spec
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text("""
metadata:
  version: "1.0"
  description: "Test spec"

requirements:
  - id: T1
    description: "Test requirement"
    weight: 1.0
    test_markers: [T1_test]
""")

        # Create test results
        results_file = tmp_path / "results.json"
        results_file.write_text(json.dumps({
            "marker_results": {
                "T1_test": {
                    "total": 1,
                    "passed": 1,
                    "failed": 0,
                    "skipped": 0,
                    "tests": ["test_something"]
                }
            },
            "test_results": {"test_something": "pass"}
        }))

        # Generate report
        reporter = JSONReporter(spec_file, results_file)
        output = reporter.generate()
        
        # Verify output
        report = json.loads(output)
        assert "compliance_score" in report
        assert "metadata" in report
        assert "per_requirement" in report
        assert "summary" in report

    def test_console_reporter_generates_text(self, tmp_path):
        """Test console reporter generates readable text."""
        # Create minimal spec
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text("""
metadata:
  version: "1.0"
requirements:
  - id: T1
    description: "Test"
    weight: 1.0
    test_markers: [T1_test]
""")

        results_file = tmp_path / "results.json"
        results_file.write_text(json.dumps({
            "marker_results": {
                "T1_test": {"total": 1, "passed": 1, "failed": 0, "skipped": 0, "tests": []}
            },
            "test_results": {}
        }))

        reporter = ConsoleReporter(spec_file, results_file)
        output = reporter.generate()
        
        # Verify output contains expected sections
        assert "COMPLIANCE ASSURANCE REPORT" in output
        assert "Overall Score" in output
        assert "Summary" in output

    def test_html_reporter_generates_valid_html(self, tmp_path):
        """Test HTML reporter generates valid HTML."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text("""
metadata:
  version: "1.0"
requirements:
  - id: T1
    description: "Test"
    weight: 1.0
    test_markers: [T1_test]
""")

        results_file = tmp_path / "results.json"
        results_file.write_text(json.dumps({
            "marker_results": {
                "T1_test": {"total": 1, "passed": 1, "failed": 0, "skipped": 0, "tests": []}
            },
            "test_results": {}
        }))

        reporter = HTMLReporter(spec_file, results_file)
        output = reporter.generate()
        
        # Verify HTML structure
        assert "<!DOCTYPE html>" in output
        assert "<html>" in output
        assert "</html>" in output
        assert "Compliance Assurance Report" in output

    def test_reporter_writes_to_file(self, tmp_path):
        """Test reporter can write to file."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text("""
metadata:
  version: "1.0"
requirements:
  - id: T1
    description: "Test"
    weight: 1.0
    test_markers: [T1_test]
""")

        results_file = tmp_path / "results.json"
        results_file.write_text(json.dumps({
            "marker_results": {
                "T1_test": {"total": 1, "passed": 1, "failed": 0, "skipped": 0, "tests": []}
            },
            "test_results": {}
        }))

        output_file = tmp_path / "report.json"
        
        reporter = JSONReporter(spec_file, results_file)
        reporter.generate(output_file)
        
        assert output_file.exists()
        content = json.loads(output_file.read_text())
        assert "compliance_score" in content

    def test_generate_compliance_report_convenience(self, tmp_path):
        """Test convenience function for report generation."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text("""
metadata:
  version: "1.0"
requirements:
  - id: T1
    description: "Test"
    weight: 1.0
    test_markers: [T1_test]
""")

        results_file = tmp_path / "results.json"
        results_file.write_text(json.dumps({
            "marker_results": {
                "T1_test": {"total": 1, "passed": 1, "failed": 0, "skipped": 0, "tests": []}
            },
            "test_results": {}
        }))

        # Test JSON format
        output = generate_compliance_report(spec_file, results_file, format="json")
        assert json.loads(output)  # Valid JSON

        # Test console format
        output = generate_compliance_report(spec_file, results_file, format="console")
        assert "COMPLIANCE" in output

        # Test HTML format
        output = generate_compliance_report(spec_file, results_file, format="html")
        assert "<!DOCTYPE html>" in output

    def test_generate_report_invalid_format(self, tmp_path):
        """Test error handling for invalid format."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text("metadata:\n  version: '1.0'")
        
        results_file = tmp_path / "results.json"
        results_file.write_text("{}")

        with pytest.raises(ValueError):
            generate_compliance_report(spec_file, results_file, format="invalid")

    def test_reporter_missing_results_file(self, tmp_path):
        """Test error handling when results file is missing."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text("""
metadata:
  version: "1.0"
requirements:
  - id: T1
    description: "Test"
    weight: 1.0
    test_markers: [T1_test]
""")
        
        results_file = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            JSONReporter(spec_file, results_file)
