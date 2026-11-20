"""
Dashboard Query Service

Provides high-level queries for compliance score visualization.
Abstracts Phoenix data access and provides optimized queries for dashboard operations.

This module handles:
- Querying historical compliance scores
- Filtering by date range, version, requirement
- Computing trends and comparisons
- Preparing data for visualization

NOTE: In Phase 2b-2, this will integrate with actual Phoenix queries via HistoricalScoreTracker.
For now, it provides a data abstraction that works with mock data for development.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScoreTrendPoint:
    """Single point in a compliance score trend."""
    timestamp: str
    version_identifier: str
    overall_score: float
    git_branch: str
    git_commit: str


@dataclass
class PerRequirementSnapshot:
    """Per-requirement scores at a specific point in time."""
    requirement_id: str
    score: float
    timestamp: str
    version_identifier: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class VersionComparisonResult:
    """Result of comparing two versions."""
    version_a: str
    version_b: str
    overall_score_a: float
    overall_score_b: float
    overall_score_change: float
    per_requirement_changes: Dict[str, float]
    improved_requirements: List[str]
    regressed_requirements: List[str]
    stable_requirements: List[str]


class DashboardQueryService:
    """
    Query service for dashboard data retrieval and transformation.
    
    Provides high-level queries optimized for dashboard visualization:
    - Score trends over time
    - Per-requirement analysis
    - Version comparison
    - Date range filtering
    - Regression detection
    
    Attributes:
        _mock_data: Mock data dictionary for testing/development
        _cache: Optional cache for query results (for future optimization)
    """

    def __init__(self, mock_data: Optional[Dict] = None):
        """
        Initialize query service.
        
        Args:
            mock_data: Optional mock data dictionary for testing/development
        """
        self._mock_data = mock_data or {}
        self._cache: Dict[str, Any] = {}
        logger.info("Dashboard query service initialized")

    def set_mock_data(self, mock_data: Dict) -> None:
        """
        Set mock data for testing/development.
        
        Args:
            mock_data: Dictionary of mock compliance records
        """
        self._mock_data = mock_data
        logger.debug(f"Set mock data with {len(mock_data)} records")

    def get_all_scores(self) -> List[ScoreTrendPoint]:
        """
        Get all historical compliance scores.
        
        Returns:
            List of ScoreTrendPoint objects sorted by timestamp (oldest first)
        """
        logger.debug("Fetching all historical scores")
        
        trend_points = []
        for version_id, record in self._mock_data.items():
            point = ScoreTrendPoint(
                timestamp=record.get('timestamp', ''),
                version_identifier=version_id,
                overall_score=record.get('overall_score', 0.0),
                git_branch=record.get('git_branch', 'unknown'),
                git_commit=record.get('git_commit', 'unknown')
            )
            trend_points.append(point)
        
        # Sort by timestamp
        trend_points.sort(key=lambda p: p.timestamp)
        
        logger.info(f"Retrieved {len(trend_points)} historical score records")
        return trend_points

    def get_scores_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[ScoreTrendPoint]:
        """
        Get scores within a date range.
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
        
        Returns:
            List of ScoreTrendPoint objects within date range, sorted by timestamp
        """
        logger.debug(f"Filtering scores by date range: {start_date} to {end_date}")
        
        all_scores = self.get_all_scores()
        
        filtered = [
            score for score in all_scores
            if self._parse_timestamp(score.timestamp) >= start_date
            and self._parse_timestamp(score.timestamp) <= end_date
        ]
        
        logger.info(f"Found {len(filtered)} scores in date range")
        return filtered

    def get_scores_by_version(self, version_identifier: str) -> Optional[ScoreTrendPoint]:
        """
        Get score for a specific version.
        
        Args:
            version_identifier: Version ID to query
        
        Returns:
            ScoreTrendPoint for the version, or None if not found
        """
        logger.debug(f"Fetching score for version: {version_identifier}")
        
        if version_identifier not in self._mock_data:
            logger.warning(f"Version not found: {version_identifier}")
            return None
        
        record = self._mock_data[version_identifier]
        point = ScoreTrendPoint(
            timestamp=record.get('timestamp', ''),
            version_identifier=version_identifier,
            overall_score=record.get('overall_score', 0.0),
            git_branch=record.get('git_branch', 'unknown'),
            git_commit=record.get('git_commit', 'unknown')
        )
        
        return point

    def get_per_requirement_trend(
        self,
        requirement_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[PerRequirementSnapshot]:
        """
        Get historical trend for a specific requirement.
        
        Args:
            requirement_id: Requirement ID (e.g., "T1", "T2")
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            List of PerRequirementSnapshot objects sorted by timestamp
        """
        logger.debug(f"Fetching trend for requirement: {requirement_id}")
        
        snapshots = []
        
        for version_id, record in self._mock_data.items():
            # Check date range if specified
            if start_date or end_date:
                record_time = self._parse_timestamp(record.get('timestamp', ''))
                if start_date and record_time < start_date:
                    continue
                if end_date and record_time > end_date:
                    continue
            
            # Get requirement score if available
            per_req_scores = record.get('per_requirement_scores', {})
            if requirement_id in per_req_scores:
                score = per_req_scores[requirement_id]
                details = None
                per_req_details = record.get('per_requirement_details', {})
                if requirement_id in per_req_details:
                    details = per_req_details[requirement_id]
                
                snapshot = PerRequirementSnapshot(
                    requirement_id=requirement_id,
                    score=score,
                    timestamp=record.get('timestamp', ''),
                    version_identifier=version_id,
                    details=details
                )
                snapshots.append(snapshot)
        
        # Sort by timestamp
        snapshots.sort(key=lambda s: s.timestamp)
        
        logger.info(f"Found {len(snapshots)} snapshots for requirement {requirement_id}")
        return snapshots

    def get_version_comparison(
        self,
        version_a: str,
        version_b: str
    ) -> Optional[VersionComparisonResult]:
        """
        Compare compliance scores between two versions.
        
        Args:
            version_a: First version ID
            version_b: Second version ID
        
        Returns:
            VersionComparisonResult with differences, or None if versions not found
        """
        logger.debug(f"Comparing versions: {version_a} vs {version_b}")
        
        # Verify both versions exist
        if version_a not in self._mock_data:
            logger.warning(f"Version not found: {version_a}")
            return None
        if version_b not in self._mock_data:
            logger.warning(f"Version not found: {version_b}")
            return None
        
        record_a = self._mock_data[version_a]
        record_b = self._mock_data[version_b]
        
        overall_score_a = record_a.get('overall_score', 0.0)
        overall_score_b = record_b.get('overall_score', 0.0)
        overall_change = overall_score_b - overall_score_a
        
        # Compare per-requirement scores
        per_req_changes = {}
        improved = []
        regressed = []
        stable = []
        
        all_requirements = set()
        scores_a = record_a.get('per_requirement_scores', {})
        scores_b = record_b.get('per_requirement_scores', {})
        all_requirements.update(scores_a.keys())
        all_requirements.update(scores_b.keys())
        
        for req_id in sorted(all_requirements):
            score_a = scores_a.get(req_id, 0.0)
            score_b = scores_b.get(req_id, 0.0)
            change = score_b - score_a
            
            per_req_changes[req_id] = change
            
            # Classify change with small tolerance to avoid floating point issues
            if change > 0.001:
                improved.append(req_id)
            elif change < -0.001:
                regressed.append(req_id)
            else:
                stable.append(req_id)
        
        result = VersionComparisonResult(
            version_a=version_a,
            version_b=version_b,
            overall_score_a=overall_score_a,
            overall_score_b=overall_score_b,
            overall_score_change=overall_change,
            per_requirement_changes=per_req_changes,
            improved_requirements=improved,
            regressed_requirements=regressed,
            stable_requirements=stable
        )
        
        logger.info(f"Comparison complete: {len(improved)} improved, {len(regressed)} regressed, {len(stable)} stable")
        return result

    def get_latest_scores(self, limit: int = 10) -> List[ScoreTrendPoint]:
        """
        Get the N most recent compliance scores.
        
        Args:
            limit: Number of records to return (default 10)
        
        Returns:
            List of ScoreTrendPoint objects (most recent first)
        """
        logger.debug(f"Fetching latest {limit} scores")
        
        all_scores = self.get_all_scores()
        
        # Return in reverse order (most recent first)
        return list(reversed(all_scores[-limit:]))

    def get_requirement_list(self) -> List[str]:
        """
        Get list of all requirements that have scores.
        
        Returns:
            Sorted list of requirement IDs (e.g., ["T1", "T2", ...])
        """
        logger.debug("Fetching requirement list")
        
        requirements = set()
        
        for record in self._mock_data.values():
            per_req_scores = record.get('per_requirement_scores', {})
            requirements.update(per_req_scores.keys())
        
        sorted_reqs = sorted(list(requirements))
        logger.info(f"Found {len(sorted_reqs)} unique requirements")
        return sorted_reqs

    def get_regression_alerts(
        self,
        threshold: float = 0.05
    ) -> List[Dict[str, Any]]:
        """
        Detect regressions (score drops) in historical data.
        
        Args:
            threshold: Minimum score drop to flag as regression (default 5%)
        
        Returns:
            List of regression alerts with details
        """
        logger.debug(f"Detecting regressions with threshold {threshold}")
        
        all_scores = self.get_all_scores()
        alerts = []
        
        # Check consecutive scores for drops
        for i in range(1, len(all_scores)):
            prev_score = all_scores[i - 1].overall_score
            curr_score = all_scores[i].overall_score
            drop = prev_score - curr_score
            
            if drop >= threshold:
                alerts.append({
                    "from_version": all_scores[i - 1].version_identifier,
                    "from_score": prev_score,
                    "to_version": all_scores[i].version_identifier,
                    "to_score": curr_score,
                    "drop": drop,
                    "percentage": (drop / prev_score * 100) if prev_score > 0 else 0,
                    "timestamp": all_scores[i].timestamp
                })
        
        logger.info(f"Found {len(alerts)} regressions")
        return alerts

    def get_last_n_days(self, days: int = 7) -> List[ScoreTrendPoint]:
        """
        Get scores from the last N days.
        
        Args:
            days: Number of days to look back (default 7)
        
        Returns:
            List of ScoreTrendPoint objects from last N days
        """
        logger.debug(f"Fetching scores from last {days} days")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.get_scores_by_date_range(start_date, end_date)

    def compute_average_score(
        self,
        scores: List[ScoreTrendPoint]
    ) -> float:
        """
        Compute average compliance score from a list of trends.
        
        Args:
            scores: List of ScoreTrendPoint objects
        
        Returns:
            Average overall_score (0.0 if list is empty)
        """
        if not scores:
            return 0.0
        
        total = sum(score.overall_score for score in scores)
        return total / len(scores)

    def compute_trend_direction(
        self,
        scores: List[ScoreTrendPoint]
    ) -> str:
        """
        Determine trend direction (improving, declining, stable).
        
        Args:
            scores: List of ScoreTrendPoint objects (should be sorted by time)
        
        Returns:
            "improving", "declining", or "stable"
        """
        if len(scores) < 2:
            return "stable"
        
        # Compare first third to last third
        cutoff = len(scores) // 3
        if cutoff == 0:
            cutoff = 1
        
        early_avg = self.compute_average_score(scores[:cutoff])
        recent_avg = self.compute_average_score(scores[-cutoff:])
        
        threshold = 0.01  # 1% difference threshold
        change = recent_avg - early_avg
        
        if change > threshold:
            return "improving"
        elif change < -threshold:
            return "declining"
        else:
            return "stable"

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse ISO 8601 timestamp string to datetime.
        
        Args:
            timestamp_str: ISO 8601 formatted timestamp
        
        Returns:
            datetime object
        """
        try:
            # Handle ISO 8601 format with Z suffix
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            
            # Try parsing with timezone
            try:
                return datetime.fromisoformat(timestamp_str)
            except ValueError:
                # Fallback: parse without timezone
                return datetime.fromisoformat(timestamp_str.split('+')[0].split('Z')[0])
        except Exception as e:
            logger.error(f"Error parsing timestamp {timestamp_str}: {e}")
            return datetime.now()

    def clear_cache(self) -> None:
        """Clear internal cache (useful for memory management)."""
        self._cache.clear()
        logger.debug("Query service cache cleared")
