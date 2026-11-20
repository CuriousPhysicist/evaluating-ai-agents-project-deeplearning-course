"""
Tests for Dashboard Query Service and Data Transformer

Tests cover:
- Query service data retrieval
- Data transformation to chart formats
- Filtering and date range operations
- Version comparison
- Regression detection
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from agent_evals.dashboard.query_service import (
    DashboardQueryService,
    ScoreTrendPoint,
    PerRequirementSnapshot,
    VersionComparisonResult
)
from agent_evals.dashboard.data_transformer import DashboardDataTransformer


class TestDashboardQueryService:
    """Test cases for query service functionality."""

    @pytest.fixture
    def mock_data(self):
        """Create sample mock data."""
        return {
            "v1.0.0_main_a1b2c3d_20261115T120000Z": {
                "overall_score": 0.90,
                "per_requirement_scores": {"T1": 0.95, "T2": 0.85, "T3": 0.90},
                "per_requirement_details": {},
                "git_branch": "main",
                "git_commit": "a1b2c3d",
                "project_version": "1.0.0",
                "timestamp": "2026-11-15T12:00:00Z",
                "environment": "development"
            },
            "v1.0.0_main_b2c3d4e_20261116T120000Z": {
                "overall_score": 0.92,
                "per_requirement_scores": {"T1": 0.96, "T2": 0.87, "T3": 0.92},
                "per_requirement_details": {},
                "git_branch": "main",
                "git_commit": "b2c3d4e",
                "project_version": "1.0.0",
                "timestamp": "2026-11-16T12:00:00Z",
                "environment": "development"
            },
            "v1.0.1_feat_c3d4e5f_20261117T120000Z": {
                "overall_score": 0.85,
                "per_requirement_scores": {"T1": 0.90, "T2": 0.80, "T3": 0.85},
                "per_requirement_details": {},
                "git_branch": "feat/optimization",
                "git_commit": "c3d4e5f",
                "project_version": "1.0.1",
                "timestamp": "2026-11-17T12:00:00Z",
                "environment": "development"
            },
        }

    @pytest.fixture
    def query_service(self, mock_data):
        """Create query service with mock data."""
        return DashboardQueryService(mock_data=mock_data)

    def test_get_all_scores(self, query_service):
        """Test retrieving all historical scores."""
        scores = query_service.get_all_scores()
        
        assert len(scores) == 3
        assert all(isinstance(s, ScoreTrendPoint) for s in scores)
        assert scores[0].overall_score == 0.90
        assert scores[1].overall_score == 0.92
        assert scores[2].overall_score == 0.85

    def test_get_scores_by_date_range(self, query_service):
        """Test filtering scores by date range."""
        start = datetime(2026, 11, 16, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 11, 16, 23, 59, 59, tzinfo=timezone.utc)
        
        scores = query_service.get_scores_by_date_range(start, end)
        
        assert len(scores) == 1
        assert scores[0].overall_score == 0.92

    def test_get_scores_by_version(self, query_service):
        """Test retrieving a specific version."""
        version_id = "v1.0.0_main_a1b2c3d_20261115T120000Z"
        score = query_service.get_scores_by_version(version_id)
        
        assert score is not None
        assert score.overall_score == 0.90
        assert score.version_identifier == version_id

    def test_get_per_requirement_trend(self, query_service):
        """Test getting trend for specific requirement."""
        trend = query_service.get_per_requirement_trend("T1")
        
        assert len(trend) == 3
        assert all(isinstance(t, PerRequirementSnapshot) for t in trend)
        assert trend[0].score == 0.95
        assert trend[1].score == 0.96
        assert trend[2].score == 0.90

    def test_get_version_comparison(self, query_service):
        """Test version comparison."""
        comp = query_service.get_version_comparison(
            "v1.0.0_main_a1b2c3d_20261115T120000Z",
            "v1.0.0_main_b2c3d4e_20261116T120000Z"
        )
        
        assert comp is not None
        assert abs(comp.overall_score_change - 0.02) < 0.001
        assert "T1" in comp.improved_requirements

    def test_get_regression_comparison(self, query_service):
        """Test version comparison with regression."""
        comp = query_service.get_version_comparison(
            "v1.0.0_main_b2c3d4e_20261116T120000Z",
            "v1.0.1_feat_c3d4e5f_20261117T120000Z"
        )
        
        assert comp is not None
        assert abs(comp.overall_score_change - (-0.07)) < 0.001
        assert len(comp.regressed_requirements) == 3

    def test_get_latest_scores(self, query_service):
        """Test getting N most recent scores."""
        latest = query_service.get_latest_scores(limit=2)
        
        assert len(latest) == 2
        assert latest[0].overall_score == 0.85
        assert latest[1].overall_score == 0.92

    def test_get_requirement_list(self, query_service):
        """Test getting all requirements."""
        reqs = query_service.get_requirement_list()
        
        assert len(reqs) == 3
        assert "T1" in reqs
        assert "T2" in reqs
        assert "T3" in reqs

    def test_get_regression_alerts(self, query_service):
        """Test regression detection."""
        alerts = query_service.get_regression_alerts(threshold=0.05)
        
        assert len(alerts) > 0
        assert any(a['drop'] >= 0.05 for a in alerts)

    def test_compute_average_score(self, query_service):
        """Test average score computation."""
        scores = [
            ScoreTrendPoint("2026-11-15T12:00:00Z", "v1", 0.80, "main", "abc"),
            ScoreTrendPoint("2026-11-16T12:00:00Z", "v2", 0.90, "main", "def"),
            ScoreTrendPoint("2026-11-17T12:00:00Z", "v3", 0.90, "main", "ghi"),
        ]
        
        avg = query_service.compute_average_score(scores)
        assert abs(avg - 0.8667) < 0.001

    def test_compute_trend_improving(self, query_service):
        """Test trend direction detection - improving."""
        scores = [
            ScoreTrendPoint("2026-11-15T12:00:00Z", "v1", 0.70, "main", "abc"),
            ScoreTrendPoint("2026-11-16T12:00:00Z", "v2", 0.75, "main", "def"),
            ScoreTrendPoint("2026-11-17T12:00:00Z", "v3", 0.80, "main", "ghi"),
        ]
        
        trend = query_service.compute_trend_direction(scores)
        assert trend == "improving"


class TestDashboardDataTransformer:
    """Test cases for data transformation."""

    @pytest.fixture
    def mock_query_service(self):
        """Create mock query service."""
        service = Mock(spec=DashboardQueryService)
        
        service.get_all_scores.return_value = [
            ScoreTrendPoint("2026-11-15T12:00:00Z", "v1", 0.90, "main", "a1b2c3d"),
            ScoreTrendPoint("2026-11-16T12:00:00Z", "v2", 0.92, "main", "b2c3d4e"),
        ]
        
        service.get_requirement_list.return_value = ["T1", "T2", "T3"]
        service.compute_average_score.return_value = 0.91
        service.compute_trend_direction.return_value = "stable"
        
        return service

    @pytest.fixture
    def transformer(self, mock_query_service):
        """Create transformer with mock service."""
        return DashboardDataTransformer(query_service=mock_query_service)

    def test_transform_to_line_chart(self, transformer):
        """Test transformation to line chart format."""
        scores = [
            ScoreTrendPoint("2026-11-15T12:00:00Z", "v1", 0.90, "main", "a1b2c3d"),
            ScoreTrendPoint("2026-11-16T12:00:00Z", "v2", 0.92, "main", "b2c3d4e"),
        ]
        
        result = transformer.transform_to_line_chart(scores)
        
        assert result['title'] == "Compliance Score Trend"
        assert len(result['x']) == 2
        assert result['y'] == [0.90, 0.92]
        assert result['latest_score'] == 0.92

    def test_transform_version_comparison(self, transformer):
        """Test version comparison transformation."""
        comp = VersionComparisonResult(
            version_a="v1.0.0",
            version_b="v1.0.1",
            overall_score_a=0.90,
            overall_score_b=0.92,
            overall_score_change=0.02,
            per_requirement_changes={"T1": 0.02, "T2": 0.01},
            improved_requirements=["T1", "T2"],
            regressed_requirements=[],
            stable_requirements=[]
        )
        
        result = transformer.transform_version_comparison(comp)
        
        assert result['version_a'] == "v1.0.0"
        assert result['version_b'] == "v1.0.1"
        assert result['overall_change'] == 0.02
        assert result['summary']['improved_count'] == 2

    def test_normalize_scores(self, transformer):
        """Test score normalization."""
        scores = [0.2, 0.5, 0.8]
        
        normalized = transformer.normalize_scores(scores)
        
        assert len(normalized) == 3
        assert normalized[0] == 0.0
        assert abs(normalized[1] - 0.5) < 0.001
        assert normalized[2] == 1.0

    def test_compute_color_code(self, transformer):
        """Test color code computation for scores."""
        assert 'rgb(76, 175, 80)' == transformer.compute_color_code(0.9)  # Green
        assert 'rgb(255, 193, 7)' == transformer.compute_color_code(0.7)  # Amber
        assert 'rgb(255, 152, 0)' == transformer.compute_color_code(0.5)  # Orange
        assert 'rgb(244, 67, 54)' == transformer.compute_color_code(0.2)  # Red
