"""Pytest plugin for collecting marked test results and calculating compliance scores.

This plugin automatically collects test outcomes (pass/fail/skip) for tests marked
with T-ID markers and makes them available for compliance scoring.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, asdict

import pytest


@dataclass
class TestMarker:
    """Represents a single marker on a test."""

    test_name: str
    marker: str
    outcome: Optional[str] = None  # 'pass', 'fail', 'skip', None if not run


@dataclass
class MarkerResult:
    """Results for a single marker across all tests that use it."""

    marker: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    tests: List[str] = None

    def __post_init__(self):
        if self.tests is None:
            self.tests = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# Global plugin instance
_compliance_plugin: Optional['CompliancePlugin'] = None


def _get_plugin(session_config=None):
    """Get or create the plugin instance."""
    global _compliance_plugin
    if _compliance_plugin is None:
        _compliance_plugin = CompliancePlugin()
        if session_config:
            _compliance_plugin._configure(session_config)
    return _compliance_plugin


class CompliancePlugin:
    """Pytest plugin for compliance tracking and scoring."""

    def __init__(self):
        self.results: Dict[str, str] = {}  # test_name -> outcome
        self.markers: Dict[str, List[str]] = {}  # test_name -> list of markers
        self.marker_outcomes: Dict[str, MarkerResult] = {}  # marker -> MarkerResult
        self.output_file: Optional[Path] = None
        self.verbose: bool = False
        self.generate_report: bool = False

    def _configure(self, config):
        """Configure the plugin instance."""
        self.output_file = Path(config.getoption("--compliance-report-output"))
        self.verbose = config.getoption("--compliance-verbose")
        self.generate_report = config.getoption("--compliance-report")
        config.addinivalue_line(
            "markers",
            "T_ID: marks test with a T-ID requirement marker (e.g., T1_setup, T10_call_limit)",
        )

    def _collection_finish(self, session):
        """Called after test collection is complete."""
        # Build marker registry from collected tests
        for item in session.items:
            test_name = item.nodeid.split("::")[-1]

            # Extract all T-ID and ASSURANCE markers
            markers = []
            for marker in item.iter_markers():
                marker_name = marker.name
                if marker_name.startswith(('T', 'ASSURANCE')):
                    # Only capture markers that look like T-ID markers
                    if '_' in marker_name:
                        markers.append(marker_name)

            if markers:
                self.markers[test_name] = markers

        if self.verbose:
            print(f"\nCompliance Plugin: Collected {len(self.markers)} marked tests")

    def _runtest_makereport(self, item, call):
        """Called after each test phase."""
        # We only care about the outcome phase
        if call.when != "call":
            return

        test_name = item.nodeid.split("::")[-1]
        if test_name in self.markers:
            # Determine outcome
            if call.excinfo is None:
                outcome = "pass"
            else:
                outcome = "fail"

            self.results[test_name] = outcome

            if self.verbose:
                markers = ", ".join(self.markers[test_name])
                print(f"\nCompliance: {test_name} -> {outcome} ({markers})")

    def _runtest_logreport(self, report):
        """Called after each test runs."""
        # Capture skip information
        if report.outcome == "skipped" and report.when == "setup":
            test_name = report.nodeid.split("::")[-1]
            if test_name in self.markers:
                self.results[test_name] = "skip"
                if self.verbose:
                    markers = ", ".join(self.markers[test_name])
                    print(f"\nCompliance: {test_name} -> skip ({markers})")

    def _sessionfinish(self, session, exitstatus):
        """Called at the end of the test session."""
        # Only generate report if requested
        if not self.generate_report:
            return

        # Build marker results
        for test_name, outcome in self.results.items():
            if test_name in self.markers:
                for marker in self.markers[test_name]:
                    if marker not in self.marker_outcomes:
                        self.marker_outcomes[marker] = MarkerResult(marker=marker)

                    result = self.marker_outcomes[marker]
                    result.total += 1
                    result.tests.append(test_name)

                    if outcome == "pass":
                        result.passed += 1
                    elif outcome == "fail":
                        result.failed += 1
                    elif outcome == "skip":
                        result.skipped += 1

        # Prepare report data
        report_data = {
            "summary": {
                "total_marked_tests": len(self.results),
                "total_markers": len(self.marker_outcomes),
                "passed": sum(1 for o in self.results.values() if o == "pass"),
                "failed": sum(1 for o in self.results.values() if o == "fail"),
                "skipped": sum(1 for o in self.results.values() if o == "skip"),
            },
            "marker_results": {
                marker: result.to_dict()
                for marker, result in sorted(self.marker_outcomes.items())
            },
            "test_results": self.results,
        }

        # Write report
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_file.write_text(json.dumps(report_data, indent=2))

        if self.verbose:
            print(f"\nCompliance report written to: {self.output_file}")
            print(f"Summary: {report_data['summary']}")


def pytest_addoption(parser):
    """Module-level hook to add pytest command line options."""
    parser.addoption(
        "--compliance-report",
        action="store_true",
        default=False,
        help="Generate a compliance report after tests run",
    )
    parser.addoption(
        "--compliance-report-output",
        action="store",
        default=".compliance_results.json",
        help="Output file for compliance report (default: .compliance_results.json)",
    )
    parser.addoption(
        "--compliance-verbose",
        action="store_true",
        default=False,
        help="Verbose output for compliance tracking",
    )


def pytest_configure(config):
    """Module-level hook to configure the plugin."""
    # The plugin is auto-loaded from the pytest11 entry point,
    # so it's already in the plugin manager. Just configure it.
    plugin = _get_plugin()
    plugin._configure(config)


def pytest_collection_finish(session):
    """Module-level hook after test collection."""
    plugin = _get_plugin()
    plugin._collection_finish(session)


def pytest_runtest_makereport(item, call):
    """Module-level hook for test reports."""
    plugin = _get_plugin()
    plugin._runtest_makereport(item, call)


def pytest_runtest_logreport(report):
    """Module-level hook for test log reports."""
    plugin = _get_plugin()
    plugin._runtest_logreport(report)


def pytest_sessionfinish(session, exitstatus):
    """Module-level hook at session end."""
    plugin = _get_plugin()
    plugin._sessionfinish(session, exitstatus)
