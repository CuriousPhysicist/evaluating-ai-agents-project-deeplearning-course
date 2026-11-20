"""Integration tests for historical score tracking with compliance checking.

Tests the integration between:
- compliance_check.py (ComplianceChecker with storage support)
- phoenix_history.py (HistoricalScoreTracker)
- git_utils.py (git metadata capture)

These tests cover:
- Automatic storage after compliance checks
- Storage timing options (always, on_pass, on_fail)
- End-to-end workflow with real Phoenix instance
- Mock-based unit tests for isolated behavior
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import os
import pytest

from agent_evals.cli.compliance_check import ComplianceChecker, ThresholdConfig
from agent_evals.exit_codes import ExitCode
from agent_evals.git_utils import (
    get_git_branch,
    get_git_commit_hash,
    get_project_version,
    get_baseline_version,
    build_version_identifier,
)
from agent_evals.phoenix_history import HistoricalScoreTracker


# Determine if we should run live tests (requires Phoenix server)
LIVE_TESTS_ENABLED = os.getenv("PYTEST_LIVE", "").lower() == "true"


class TestGitUtils:
    """Test git utility functions for metadata capture."""

    def test_get_git_branch_with_explicit(self):
        """Test that explicit branch is returned as-is."""
        result = get_git_branch(explicit_branch="main")
        assert result == "main"

    def test_get_git_branch_with_explicit_feature(self):
        """Test explicit feature branch."""
        result = get_git_branch(explicit_branch="feat/historical-tracking")
        assert result == "feat/historical-tracking"

    def test_get_git_commit_hash_with_explicit(self):
        """Test explicit commit hash."""
        result = get_git_commit_hash()
        # Should return something (even if "unknown" in isolated test env)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_project_version_with_explicit(self):
        """Test explicit version."""
        result = get_project_version(explicit_version="1.2.3")
        assert result == "1.2.3"

    def test_get_project_version_from_pyproject(self):
        """Test version extraction from pyproject.toml."""
        # This should work if running from project directory
        result = get_project_version()
        # Should return something
        assert isinstance(result, str)
        assert len(result) > 0
        # Usually semantic version or "unknown"
        assert result == "0.1.0" or result == "unknown"

    def test_get_baseline_version_with_explicit(self):
        """Test explicit baseline."""
        result = get_baseline_version(explicit_baseline="0.0.9")
        assert result == "0.0.9"

    def test_build_version_identifier(self):
        """Test building complete version identifier."""
        result = build_version_identifier(explicit_version="1.2.3")
        # Should be: v1.2.3-<date>-<time>
        assert result.startswith("v1.2.3-")
        # Should have date and time components
        parts = result.split("-")
        assert len(parts) >= 3  # v1.2.3 + date + time
        # Date should be YYYYMMDD format (8 digits)
        assert len(parts[1]) == 8
        assert parts[1].isdigit()
        # Time should be HHMMSS format (6 digits)
        assert len(parts[2]) == 6
        assert parts[2].isdigit()


class TestComplianceCheckerWithStorage:
    """Test ComplianceChecker integration with storage."""

    @pytest.fixture
    def threshold_config(self, tmp_path):
        """Create test threshold configuration."""
        config_file = tmp_path / "threshold.yaml"
        config_file.write_text(
            """
defaults:
  overall_score: 0.80
  per_requirement: 0.50
  regression_allowed: 0.05

environments:
  development:
    overall_score: 0.75
    per_requirement: 0.40
  production:
    overall_score: 0.90
    per_requirement: 0.70

baselines:
  current:
    overall_score: 0.85
"""
        )
        return ThresholdConfig(str(config_file))

    @pytest.fixture
    def checker(self, threshold_config):
        """Create compliance checker."""
        return ComplianceChecker(threshold_config)

    @pytest.fixture
    def mock_tracker(self):
        """Create mock HistoricalScoreTracker."""
        tracker = Mock(spec=HistoricalScoreTracker)
        tracker.version = "v1.0.0-20261120-100000"
        tracker.store_evaluation_results.return_value = True
        return tracker

    def test_check_and_store_with_pass_always_timing(self, checker, mock_tracker):
        """Test storing results when check passes with 'always' timing."""
        result = checker.check_and_store(
            overall_score=0.85,
            per_requirement_scores={"R1": 0.9, "R2": 0.8},
            store_tracker=mock_tracker,
            storage_timing="always",
        )

        assert result.exit_code == ExitCode.SUCCESS
        # Storage should be called
        assert mock_tracker.store_evaluation_results.called

    def test_check_and_store_with_fail_always_timing(self, checker, mock_tracker):
        """Test storing results when check fails with 'always' timing."""
        result = checker.check_and_store(
            overall_score=0.70,  # Below threshold
            per_requirement_scores={"R1": 0.9, "R2": 0.3},
            store_tracker=mock_tracker,
            storage_timing="always",
        )

        assert result.exit_code == ExitCode.COMPLIANCE_REGRESSION
        # Storage should still be called
        assert mock_tracker.store_evaluation_results.called

    def test_check_and_store_pass_only_timing_with_pass(self, checker, mock_tracker):
        """Test 'on_pass' timing stores when check passes."""
        result = checker.check_and_store(
            overall_score=0.85,
            per_requirement_scores={"R1": 0.9, "R2": 0.8},
            store_tracker=mock_tracker,
            storage_timing="on_pass",
        )

        assert result.exit_code == ExitCode.SUCCESS
        assert mock_tracker.store_evaluation_results.called

    def test_check_and_store_pass_only_timing_with_fail(self, checker, mock_tracker):
        """Test 'on_pass' timing does NOT store when check fails."""
        result = checker.check_and_store(
            overall_score=0.70,  # Below threshold
            per_requirement_scores={"R1": 0.9, "R2": 0.3},
            store_tracker=mock_tracker,
            storage_timing="on_pass",
        )

        assert result.exit_code == ExitCode.COMPLIANCE_REGRESSION
        # Storage should NOT be called
        assert not mock_tracker.store_evaluation_results.called

    def test_check_and_store_fail_only_timing_with_pass(self, checker, mock_tracker):
        """Test 'on_fail' timing does NOT store when check passes."""
        result = checker.check_and_store(
            overall_score=0.85,
            per_requirement_scores={"R1": 0.9, "R2": 0.8},
            store_tracker=mock_tracker,
            storage_timing="on_fail",
        )

        assert result.exit_code == ExitCode.SUCCESS
        # Storage should NOT be called
        assert not mock_tracker.store_evaluation_results.called

    def test_check_and_store_fail_only_timing_with_fail(self, checker, mock_tracker):
        """Test 'on_fail' timing stores when check fails."""
        result = checker.check_and_store(
            overall_score=0.70,  # Below threshold
            per_requirement_scores={"R1": 0.9, "R2": 0.3},
            store_tracker=mock_tracker,
            storage_timing="on_fail",
        )

        assert result.exit_code == ExitCode.COMPLIANCE_REGRESSION
        # Storage should be called
        assert mock_tracker.store_evaluation_results.called

    def test_check_and_store_without_tracker(self, checker):
        """Test that check works without tracker (backward compatible)."""
        result = checker.check_and_store(
            overall_score=0.85,
            per_requirement_scores={"R1": 0.9, "R2": 0.8},
            store_tracker=None,
            storage_timing="always",
        )

        # Should complete normally without error
        assert result.exit_code == ExitCode.SUCCESS

    def test_check_and_store_with_per_requirement_details(self, checker, mock_tracker):
        """Test storing with detailed per-requirement info."""
        per_req_details = {
            "R1": {
                "requirement_id": "R1",
                "score": 0.9,
                "weight": 1.0,
                "weighted_score": 0.9,
                "test_outcomes": {"T1": "pass", "T2": "pass"},
                "test_counts": {"pass": 2, "fail": 0},
                "evidence_source": "pytest",
            },
            "R2": {
                "requirement_id": "R2",
                "score": 0.8,
                "weight": 1.0,
                "weighted_score": 0.8,
                "test_outcomes": {"T3": "pass"},
                "test_counts": {"pass": 1, "fail": 0},
                "evidence_source": "pytest",
            },
        }

        result = checker.check_and_store(
            overall_score=0.85,
            per_requirement_details=per_req_details,
            store_tracker=mock_tracker,
            storage_timing="always",
        )

        assert result.exit_code == ExitCode.SUCCESS
        assert mock_tracker.store_evaluation_results.called

        # Verify the stored result includes the details
        call_args = mock_tracker.store_evaluation_results.call_args
        stored_result = call_args[0][0]
        assert len(stored_result["per_requirement"]) == 2
        assert stored_result["per_requirement"]["R1"]["test_outcomes"]["T1"] == "pass"

    def test_check_and_store_tracker_exception_handled(self, checker, mock_tracker):
        """Test that tracker exceptions don't crash compliance check."""
        mock_tracker.store_evaluation_results.side_effect = Exception("Phoenix error")

        # Should not raise, just log
        result = checker.check_and_store(
            overall_score=0.85,
            per_requirement_scores={"R1": 0.9, "R2": 0.8},
            store_tracker=mock_tracker,
            storage_timing="always",
        )

        # Check result should still be successful
        assert result.exit_code == ExitCode.SUCCESS


@pytest.mark.skipif(not LIVE_TESTS_ENABLED, reason="Set PYTEST_LIVE=true to run live tests")
class TestComplianceCheckerIntegrationLive:
    """Integration tests with real Phoenix server."""

    @pytest.fixture
    def threshold_config(self, tmp_path):
        """Create test threshold configuration."""
        config_file = tmp_path / "threshold.yaml"
        config_file.write_text(
            """
defaults:
  overall_score: 0.80
  per_requirement: 0.50
  regression_allowed: 0.05
"""
        )
        return ThresholdConfig(str(config_file))

    @pytest.fixture
    def checker(self, threshold_config):
        """Create compliance checker."""
        return ComplianceChecker(threshold_config)

    def test_check_and_store_end_to_end_with_real_phoenix(
        self, checker, isolated_phoenix
    ):
        """Test full workflow with real Phoenix server."""
        from agent_evals.phoenix_history import HistoricalScoreTracker

        # Create tracker with real Phoenix client
        tracker = HistoricalScoreTracker(
            phoenix_client=isolated_phoenix.client,
            version="v1.0.0-20261120-100000",
            branch="test",
            baseline_version="v0.9.9",
        )

        # Run check with storage
        result = checker.check_and_store(
            overall_score=0.85,
            per_requirement_scores={"REQ-001": 0.9, "REQ-002": 0.8},
            per_requirement_details={
                "REQ-001": {
                    "requirement_id": "REQ-001",
                    "score": 0.9,
                    "weight": 1.0,
                    "weighted_score": 0.9,
                    "test_outcomes": {"T1": "pass"},
                    "test_counts": {"pass": 1, "fail": 0},
                    "evidence_source": "pytest",
                },
                "REQ-002": {
                    "requirement_id": "REQ-002",
                    "score": 0.8,
                    "weight": 1.0,
                    "weighted_score": 0.8,
                    "test_outcomes": {"T2": "pass"},
                    "test_counts": {"pass": 1, "fail": 0},
                    "evidence_source": "pytest",
                },
            },
            store_tracker=tracker,
            storage_timing="always",
        )

        # Verify check passed
        assert result.exit_code == ExitCode.SUCCESS

        # Verify storage succeeded
        # (In Phase 3, we'll be able to query and verify the data)

    def test_check_and_store_multiple_runs_with_real_phoenix(
        self, checker, isolated_phoenix
    ):
        """Test storing multiple compliance check results."""
        from agent_evals.phoenix_history import HistoricalScoreTracker

        # First run
        tracker1 = HistoricalScoreTracker(
            phoenix_client=isolated_phoenix.client,
            version="v1.0.0-20261120-100000",
            branch="main",
            baseline_version="v0.9.9",
        )

        result1 = checker.check_and_store(
            overall_score=0.85,
            per_requirement_scores={"R1": 0.9, "R2": 0.8},
            store_tracker=tracker1,
            storage_timing="always",
        )
        assert result1.exit_code == ExitCode.SUCCESS

        # Second run with different scores
        tracker2 = HistoricalScoreTracker(
            phoenix_client=isolated_phoenix.client,
            version="v1.0.1-20261120-110000",
            branch="main",
            baseline_version="v1.0.0",
        )

        result2 = checker.check_and_store(
            overall_score=0.87,
            per_requirement_scores={"R1": 0.95, "R2": 0.8},
            store_tracker=tracker2,
            storage_timing="always",
        )
        assert result2.exit_code == ExitCode.SUCCESS

        # Both checks should have stored successfully
        # (Phase 3 will add comparison capability)
