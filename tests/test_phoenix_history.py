"""Unit tests for historical compliance score tracking.

Tests the HistoricalScoreTracker class with focus on:
- Core storage functionality
- Retrieval operations
- Error handling and graceful failure
- Data validation and edge cases
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, call
import pytest

from agent_evals.phoenix_history import HistoricalScoreTracker
from agent_evals.spec_assurance.scorer import ComplianceResult, RequirementResult


class TestHistoricalScoreTrackerInit:
    """Test HistoricalScoreTracker initialization."""

    def test_init_valid_parameters(self):
        """Test initialization with valid parameters."""
        mock_client = Mock()
        tracker = HistoricalScoreTracker(
            phoenix_client=mock_client,
            version="v1.0.0-20261120-100000",
            branch="main",
            baseline_version="v1.0.0",
        )

        assert tracker.client is mock_client
        assert tracker.version == "v1.0.0-20261120-100000"
        assert tracker.branch == "main"
        assert tracker.baseline_version == "v1.0.0"
        assert tracker.timestamp is not None

    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        mock_client = Mock()
        tracker = HistoricalScoreTracker(
            phoenix_client=mock_client,
            version="v1.0.0-20261120-100000",
        )

        assert tracker.branch == "unknown"
        assert tracker.baseline_version == "unknown"

    def test_init_invalid_version_empty(self):
        """Test initialization with empty version raises ValueError."""
        mock_client = Mock()
        with pytest.raises(ValueError):
            HistoricalScoreTracker(phoenix_client=mock_client, version="")

    def test_init_invalid_version_none(self):
        """Test initialization with None version raises ValueError."""
        mock_client = Mock()
        with pytest.raises(ValueError):
            HistoricalScoreTracker(phoenix_client=mock_client, version=None)

    def test_init_invalid_version_non_string(self):
        """Test initialization with non-string version raises ValueError."""
        mock_client = Mock()
        with pytest.raises(ValueError):
            HistoricalScoreTracker(phoenix_client=mock_client, version=12345)


class TestStoreEvaluationResults:
    """Test storing compliance evaluation results."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Phoenix client."""
        return Mock()

    @pytest.fixture
    def tracker(self, mock_client):
        """Create a HistoricalScoreTracker instance."""
        return HistoricalScoreTracker(
            phoenix_client=mock_client,
            version="v1.0.0-20261120-100000",
            branch="main",
        )

    @pytest.fixture
    def sample_compliance_result(self) -> ComplianceResult:
        """Create a sample ComplianceResult for testing."""
        return {
            "overall_score": 0.85,
            "compliance_percentage": 85.0,
            "per_requirement": {
                "REQ-001": {
                    "requirement_id": "REQ-001",
                    "description": "Test requirement 1",
                    "score": 0.9,
                    "weight": 1.0,
                    "weighted_score": 0.9,
                    "test_outcomes": {"T1": "pass", "T2": "pass"},
                    "test_counts": {"pass": 2, "fail": 0},
                    "evidence_source": "pytest",
                },
                "REQ-002": {
                    "requirement_id": "REQ-002",
                    "description": "Test requirement 2",
                    "score": 0.8,
                    "weight": 1.0,
                    "weighted_score": 0.8,
                    "test_outcomes": {"T3": "pass"},
                    "test_counts": {"pass": 1, "fail": 0},
                    "evidence_source": "pytest",
                },
            },
            "aggregate": {
                "total_weight": 2.0,
                "total_score": 1.7,
                "total_pass": 3,
                "total_fail": 0,
                "total_skip": 0,
                "compliance_percentage": 85.0,
            },
            "metadata": {"run_id": "test-run-001"},
        }

    def test_store_valid_results(self, tracker, mock_client, sample_compliance_result):
        """Test storing valid compliance results."""
        result = tracker.store_evaluation_results(sample_compliance_result)

        assert result is True
        assert mock_client.log_traces.call_count == 2  # Called once per requirement

    def test_store_results_calls_phoenix(self, tracker, mock_client, sample_compliance_result):
        """Test that store_evaluation_results calls Phoenix client correctly."""
        tracker.store_evaluation_results(sample_compliance_result)

        # Verify log_traces was called
        assert mock_client.log_traces.called
        calls = mock_client.log_traces.call_args_list

        # Should have one call per requirement
        assert len(calls) == 2

        # Check first call contains correct data
        first_call_docs = calls[0][1]["documents"]
        assert len(first_call_docs) == 1
        doc = first_call_docs[0]
        assert "REQ-001" in doc["name"]
        assert doc["attributes"]["compliance_version"] == "v1.0.0-20261120-100000"
        assert doc["attributes"]["requirement_id"] == "REQ-001"
        assert doc["attributes"]["score"] == 0.9

    def test_store_empty_per_requirement(self, tracker, mock_client):
        """Test storing result with empty per_requirement dict."""
        compliance_result: ComplianceResult = {
            "overall_score": 0.0,
            "compliance_percentage": 0.0,
            "per_requirement": {},
            "aggregate": {},
            "metadata": {},
        }

        result = tracker.store_evaluation_results(compliance_result)

        assert result is False
        assert not mock_client.log_traces.called

    def test_store_invalid_result_none(self, tracker, mock_client):
        """Test storing None as result."""
        result = tracker.store_evaluation_results(None)
        assert result is False

    def test_store_invalid_result_dict_missing_per_requirement(self, tracker, mock_client):
        """Test storing result missing per_requirement key."""
        result = tracker.store_evaluation_results({"overall_score": 0.85})
        assert result is False

    def test_store_phoenix_client_error(self, tracker, mock_client, sample_compliance_result):
        """Test graceful handling of Phoenix client errors."""
        mock_client.log_traces.side_effect = Exception("Phoenix connection failed")

        result = tracker.store_evaluation_results(sample_compliance_result)

        # Should return False but not raise exception
        assert result is False

    def test_store_includes_all_metadata(self, tracker, mock_client, sample_compliance_result):
        """Test that stored records include all required metadata."""
        tracker.store_evaluation_results(sample_compliance_result)

        # Get the first call's documents
        docs = mock_client.log_traces.call_args_list[0][1]["documents"][0]
        attrs = docs["attributes"]

        # Verify required attributes
        assert attrs["compliance_version"] == tracker.version
        assert attrs["git_branch"] == tracker.branch
        assert attrs["baseline_version"] == tracker.baseline_version
        assert attrs["evaluation_timestamp"] == tracker.timestamp
        assert "requirement_id" in attrs
        assert "score" in attrs
        assert "weight" in attrs
        assert "weighted_score" in attrs

    def test_store_requirement_with_zero_scores(self, tracker, mock_client):
        """Test storing requirement with zero scores."""
        compliance_result: ComplianceResult = {
            "overall_score": 0.0,
            "compliance_percentage": 0.0,
            "per_requirement": {
                "REQ-001": {
                    "requirement_id": "REQ-001",
                    "description": "Failed requirement",
                    "score": 0.0,
                    "weight": 1.0,
                    "weighted_score": 0.0,
                    "test_outcomes": {"T1": "fail"},
                    "test_counts": {"pass": 0, "fail": 1},
                    "evidence_source": "pytest",
                },
            },
            "aggregate": {},
            "metadata": {},
        }

        result = tracker.store_evaluation_results(compliance_result)

        assert result is True
        docs = mock_client.log_traces.call_args_list[0][1]["documents"][0]
        assert docs["attributes"]["score"] == 0.0

    def test_store_requirement_with_high_scores(self, tracker, mock_client):
        """Test storing requirement with perfect score."""
        compliance_result: ComplianceResult = {
            "overall_score": 1.0,
            "compliance_percentage": 100.0,
            "per_requirement": {
                "REQ-001": {
                    "requirement_id": "REQ-001",
                    "description": "Perfect requirement",
                    "score": 1.0,
                    "weight": 1.0,
                    "weighted_score": 1.0,
                    "test_outcomes": {"T1": "pass"},
                    "test_counts": {"pass": 1, "fail": 0},
                    "evidence_source": "pytest",
                },
            },
            "aggregate": {},
            "metadata": {},
        }

        result = tracker.store_evaluation_results(compliance_result)

        assert result is True
        docs = mock_client.log_traces.call_args_list[0][1]["documents"][0]
        assert docs["attributes"]["score"] == 1.0

    def test_store_multiple_requirements_partial_failure(self, tracker, mock_client):
        """Test that partial failures still return False."""
        compliance_result: ComplianceResult = {
            "overall_score": 0.85,
            "compliance_percentage": 85.0,
            "per_requirement": {
                "REQ-001": {
                    "requirement_id": "REQ-001",
                    "description": "Test 1",
                    "score": 0.9,
                    "weight": 1.0,
                    "weighted_score": 0.9,
                    "test_outcomes": {},
                    "test_counts": {},
                    "evidence_source": "pytest",
                },
                "REQ-002": {
                    "requirement_id": "REQ-002",
                    "description": "Test 2",
                    "score": 0.8,
                    "weight": 1.0,
                    "weighted_score": 0.8,
                    "test_outcomes": {},
                    "test_counts": {},
                    "evidence_source": "pytest",
                },
            },
            "aggregate": {},
            "metadata": {},
        }

        # First call succeeds, second raises exception
        mock_client.log_traces.side_effect = [None, Exception("Failed")]

        result = tracker.store_evaluation_results(compliance_result)

        # Should return False because one requirement failed
        assert result is False


class TestGetScoresForVersion:
    """Test retrieving scores for a specific version."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Phoenix client."""
        return Mock()

    @pytest.fixture
    def tracker(self, mock_client):
        """Create a HistoricalScoreTracker instance."""
        return HistoricalScoreTracker(
            phoenix_client=mock_client,
            version="v1.0.0-20261120-100000",
        )

    def test_get_scores_uses_current_version_when_none_specified(self, tracker):
        """Test that get_scores_for_version uses current version when none specified."""
        # Patch the internal query method
        with patch.object(tracker, "_query_phoenix_by_version") as mock_query:
            mock_query.return_value = {}

            tracker.get_scores_for_version()

            # Should be called with current version
            mock_query.assert_called_once_with("v1.0.0-20261120-100000")

    def test_get_scores_uses_specified_version(self, tracker):
        """Test that get_scores_for_version uses specified version."""
        with patch.object(tracker, "_query_phoenix_by_version") as mock_query:
            mock_query.return_value = {}

            tracker.get_scores_for_version("v2.0.0-20261120-150000")

            mock_query.assert_called_once_with("v2.0.0-20261120-150000")

    def test_get_scores_returns_empty_on_no_version(self, tracker):
        """Test that empty version returns empty dict."""
        result = tracker.get_scores_for_version("")
        assert result == {}

    def test_get_scores_returns_empty_on_query_failure(self, tracker):
        """Test that query exceptions are caught and empty dict returned."""
        with patch.object(tracker, "_query_phoenix_by_version") as mock_query:
            mock_query.side_effect = Exception("Query failed")

            result = tracker.get_scores_for_version("v1.0.0-20261120-100000")

            assert result == {}


class TestGetScoresByDateRange:
    """Test retrieving scores by date range."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Phoenix client."""
        return Mock()

    @pytest.fixture
    def tracker(self, mock_client):
        """Create a HistoricalScoreTracker instance."""
        return HistoricalScoreTracker(
            phoenix_client=mock_client,
            version="v1.0.0-20261120-100000",
        )

    def test_get_scores_by_date_range_valid(self, tracker):
        """Test getting scores for valid date range."""
        with patch.object(tracker, "_query_phoenix_by_date_range") as mock_query:
            mock_query.return_value = []

            start = datetime(2026, 11, 15)
            end = datetime(2026, 11, 20)

            result = tracker.get_scores_by_date_range(start, end)

            mock_query.assert_called_once_with(start, end, None)
            assert result == []

    def test_get_scores_by_date_range_uses_now_as_default_end(self, tracker):
        """Test that end_date defaults to now."""
        with patch.object(tracker, "_query_phoenix_by_date_range") as mock_query:
            mock_query.return_value = []

            start = datetime(2026, 11, 15)
            before_call = datetime.utcnow()

            tracker.get_scores_by_date_range(start)

            after_call = datetime.utcnow()

            # Get the actual end_date passed to the query
            call_args = mock_query.call_args
            actual_end = call_args[0][1]

            # end_date should be between before_call and after_call
            assert before_call <= actual_end <= after_call

    def test_get_scores_by_date_range_with_requirement_filter(self, tracker):
        """Test filtering by requirement_id."""
        with patch.object(tracker, "_query_phoenix_by_date_range") as mock_query:
            mock_query.return_value = []

            start = datetime(2026, 11, 15)
            end = datetime(2026, 11, 20)

            tracker.get_scores_by_date_range(start, end, requirement_id="REQ-001")

            mock_query.assert_called_once_with(start, end, "REQ-001")

    def test_get_scores_by_date_range_invalid_dates(self, tracker):
        """Test that start > end returns empty list."""
        start = datetime(2026, 11, 20)
        end = datetime(2026, 11, 15)

        result = tracker.get_scores_by_date_range(start, end)

        assert result == []

    def test_get_scores_by_date_range_query_exception(self, tracker):
        """Test that query exceptions are caught."""
        with patch.object(tracker, "_query_phoenix_by_date_range") as mock_query:
            mock_query.side_effect = Exception("Query failed")

            start = datetime(2026, 11, 15)
            end = datetime(2026, 11, 20)

            result = tracker.get_scores_by_date_range(start, end)

            assert result == []


class TestCompareVersions:
    """Test version comparison functionality."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Phoenix client."""
        return Mock()

    @pytest.fixture
    def tracker(self, mock_client):
        """Create a HistoricalScoreTracker instance."""
        return HistoricalScoreTracker(
            phoenix_client=mock_client,
            version="v1.0.0-20261120-100000",
        )

    @pytest.fixture
    def sample_scores_v1(self) -> dict[str, RequirementResult]:
        """Sample scores for version 1."""
        return {
            "REQ-001": {
                "requirement_id": "REQ-001",
                "score": 0.8,
                "weight": 1.0,
                "weighted_score": 0.8,
            },
            "REQ-002": {
                "requirement_id": "REQ-002",
                "score": 0.9,
                "weight": 1.0,
                "weighted_score": 0.9,
            },
        }

    @pytest.fixture
    def sample_scores_v2(self) -> dict[str, RequirementResult]:
        """Sample scores for version 2."""
        return {
            "REQ-001": {
                "requirement_id": "REQ-001",
                "score": 0.85,  # Improved
                "weight": 1.0,
                "weighted_score": 0.85,
            },
            "REQ-002": {
                "requirement_id": "REQ-002",
                "score": 0.85,  # Regressed
                "weight": 1.0,
                "weighted_score": 0.85,
            },
        }

    def test_compare_versions_valid(self, tracker, sample_scores_v1, sample_scores_v2):
        """Test comparing two versions with valid scores."""
        with patch.object(tracker, "get_scores_for_version") as mock_get:
            mock_get.side_effect = [sample_scores_v1, sample_scores_v2]

            result = tracker.compare_versions("v1.0.0", "v2.0.0")

            assert result is not None
            assert result["version1"] == "v1.0.0"
            assert result["version2"] == "v2.0.0"
            assert "deltas" in result
            assert "regressions" in result
            assert "improvements" in result

    def test_compare_versions_detects_improvements(self, tracker, sample_scores_v1, sample_scores_v2):
        """Test that improvements are detected."""
        with patch.object(tracker, "get_scores_for_version") as mock_get:
            mock_get.side_effect = [sample_scores_v1, sample_scores_v2]

            result = tracker.compare_versions("v1.0.0", "v2.0.0")

            # REQ-001: 0.8 → 0.85 (improvement)
            assert "REQ-001" in result["improvements"]

    def test_compare_versions_detects_regressions(self, tracker, sample_scores_v1, sample_scores_v2):
        """Test that regressions are detected."""
        with patch.object(tracker, "get_scores_for_version") as mock_get:
            mock_get.side_effect = [sample_scores_v1, sample_scores_v2]

            result = tracker.compare_versions("v1.0.0", "v2.0.0")

            # REQ-002: 0.9 → 0.85 (regression)
            assert "REQ-002" in result["regressions"]

    def test_compare_versions_missing_v1(self, tracker, sample_scores_v2):
        """Test comparison when version 1 scores not found."""
        with patch.object(tracker, "get_scores_for_version") as mock_get:
            mock_get.side_effect = [{}, sample_scores_v2]

            result = tracker.compare_versions("v1.0.0", "v2.0.0")

            assert result is None

    def test_compare_versions_missing_v2(self, tracker, sample_scores_v1):
        """Test comparison when version 2 scores not found."""
        with patch.object(tracker, "get_scores_for_version") as mock_get:
            mock_get.side_effect = [sample_scores_v1, {}]

            result = tracker.compare_versions("v1.0.0", "v2.0.0")

            assert result is None

    def test_compare_versions_exception(self, tracker):
        """Test that exceptions during comparison are caught."""
        with patch.object(tracker, "get_scores_for_version") as mock_get:
            mock_get.side_effect = Exception("Query failed")

            result = tracker.compare_versions("v1.0.0", "v2.0.0")

            assert result is None


class TestDetectRegression:
    """Test regression detection functionality."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Phoenix client."""
        return Mock()

    @pytest.fixture
    def tracker(self, mock_client):
        """Create a HistoricalScoreTracker instance."""
        return HistoricalScoreTracker(
            phoenix_client=mock_client,
            version="v1.0.0-20261120-100000",
        )

    def test_detect_regression_no_regression(self, tracker):
        """Test detection when no regression occurs."""
        comparison_result = {
            "version1": "v1.0.0",
            "version2": "v2.0.0",
            "deltas": {"REQ-001": 0.05, "REQ-002": 0.02},
            "regressions": [],
            "improvements": ["REQ-001", "REQ-002"],
        }

        with patch.object(tracker, "compare_versions") as mock_compare:
            mock_compare.return_value = comparison_result

            has_regression, reqs = tracker.detect_regression("v1.0.0", "v2.0.0")

            assert has_regression is False
            assert reqs == []

    def test_detect_regression_with_regression(self, tracker):
        """Test detection when regression occurs."""
        comparison_result = {
            "version1": "v1.0.0",
            "version2": "v2.0.0",
            "deltas": {"REQ-001": -0.1, "REQ-002": 0.02},
            "regressions": ["REQ-001"],
            "improvements": ["REQ-002"],
        }

        with patch.object(tracker, "compare_versions") as mock_compare:
            mock_compare.return_value = comparison_result

            has_regression, reqs = tracker.detect_regression("v1.0.0", "v2.0.0")

            assert has_regression is True
            assert "REQ-001" in reqs

    def test_detect_regression_uses_threshold(self, tracker):
        """Test that regression detection respects threshold."""
        comparison_result = {
            "version1": "v1.0.0",
            "version2": "v2.0.0",
            "deltas": {"REQ-001": -0.03, "REQ-002": -0.08},
            "regressions": [],
            "improvements": [],
        }

        with patch.object(tracker, "compare_versions") as mock_compare:
            mock_compare.return_value = comparison_result

            # With 5% threshold, only -0.08 should trigger regression
            has_regression, reqs = tracker.detect_regression(
                "v1.0.0", "v2.0.0", regression_threshold=0.05
            )

            assert has_regression is True
            assert "REQ-002" in reqs
            assert "REQ-001" not in reqs

    def test_detect_regression_comparison_fails(self, tracker):
        """Test detection when comparison fails."""
        with patch.object(tracker, "compare_versions") as mock_compare:
            mock_compare.return_value = None

            result = tracker.detect_regression("v1.0.0", "v2.0.0")

            assert result is None
