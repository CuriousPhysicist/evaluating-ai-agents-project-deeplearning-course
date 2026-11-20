"""
Dashboard Data Transformer

Transforms raw query results into visualization-optimized formats.
Handles aggregation, normalization, and structure conversion for various chart types.

This module handles:
- Converting query results to chart-friendly formats
- Aggregating data by time periods
- Normalizing scores for visualization
- Preparing heatmap data
- Structuring comparison data
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from agent_evals.dashboard.query_service import (
    DashboardQueryService,
    ScoreTrendPoint,
    PerRequirementSnapshot,
    VersionComparisonResult
)

logger = logging.getLogger(__name__)


class DashboardDataTransformer:
    """
    Transform query results into visualization-ready formats.
    
    Provides conversion methods for different chart types:
    - Line charts (trends)
    - Heatmaps (per-requirement matrix)
    - Bar charts (comparisons)
    - Tables (detailed data)
    
    Attributes:
        query_service: DashboardQueryService instance
    """

    def __init__(self, query_service: Optional[DashboardQueryService] = None):
        """
        Initialize transformer.
        
        Args:
            query_service: DashboardQueryService instance. If None, creates new instance.
        """
        self.query_service = query_service or DashboardQueryService()
        logger.info("Dashboard data transformer initialized")

    def transform_to_line_chart(
        self,
        scores: List[ScoreTrendPoint],
        title: str = "Compliance Score Trend"
    ) -> Dict[str, Any]:
        """
        Transform score trend to line chart format.
        
        Args:
            scores: List of ScoreTrendPoint objects (should be sorted by timestamp)
            title: Chart title
        
        Returns:
            Dictionary with chart data ready for Plotly/frontend
            Format: {
                'title': str,
                'x': [timestamps],
                'y': [scores],
                'versions': [version_ids],
                'branches': [branch_names],
                'hover_text': [formatted strings]
            }
        """
        logger.debug(f"Transforming {len(scores)} scores to line chart format")
        
        x_data = []
        y_data = []
        versions = []
        branches = []
        hover_text = []
        
        for score in scores:
            # Parse timestamp for display
            try:
                dt = datetime.fromisoformat(score.timestamp.replace('Z', '+00:00'))
                x_data.append(dt.strftime("%Y-%m-%d %H:%M"))
            except:
                x_data.append(score.timestamp)
            
            y_data.append(score.overall_score)
            versions.append(score.version_identifier)
            branches.append(score.git_branch)
            
            # Create hover text
            hover = (
                f"<b>Score:</b> {score.overall_score:.2%}<br>"
                f"<b>Version:</b> {score.version_identifier}<br>"
                f"<b>Branch:</b> {score.git_branch}<br>"
                f"<b>Commit:</b> {score.git_commit[:8]}"
            )
            hover_text.append(hover)
        
        result = {
            'title': title,
            'x': x_data,
            'y': y_data,
            'versions': versions,
            'branches': branches,
            'hover_text': hover_text,
            'min_score': min(y_data) if y_data else 0,
            'max_score': max(y_data) if y_data else 1,
            'avg_score': sum(y_data) / len(y_data) if y_data else 0,
            'latest_score': y_data[-1] if y_data else 0
        }
        
        logger.info(f"Transformed to line chart: avg={result['avg_score']:.2%}, latest={result['latest_score']:.2%}")
        return result

    def transform_to_heatmap(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        requirement_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Transform per-requirement data to heatmap format.
        
        Args:
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            requirement_ids: Optional list of requirements to include (default: all)
        
        Returns:
            Dictionary with heatmap data
            Format: {
                'x': [requirement_ids],
                'y': [timestamps],
                'z': [[scores]],  # matrix
                'versions': [version_ids],
                'title': str
            }
        """
        logger.debug("Transforming to heatmap format")
        
        # Get all scores in range
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                scores = self.query_service.get_scores_by_date_range(start, end)
            except:
                scores = self.query_service.get_all_scores()
        else:
            scores = self.query_service.get_all_scores()
        
        # Get requirements
        all_requirements = self.query_service.get_requirement_list()
        if requirement_ids:
            requirements = [r for r in all_requirements if r in requirement_ids]
        else:
            requirements = all_requirements
        
        # Build matrix
        y_data = []  # timestamps
        z_data = []  # scores matrix
        versions = []
        
        for score in scores:
            try:
                dt = datetime.fromisoformat(score.timestamp.replace('Z', '+00:00'))
                y_label = dt.strftime("%Y-%m-%d")
            except:
                y_label = score.timestamp
            
            y_data.append(y_label)
            versions.append(score.version_identifier)
            
            # Get per-requirement trends for this version
            row = []
            for req_id in requirements:
                trends = self.query_service.get_per_requirement_trend(
                    req_id,
                    start_date=None,
                    end_date=None
                )
                # Find score for this version
                score_for_req = 0.0
                for trend in trends:
                    if trend.version_identifier == score.version_identifier:
                        score_for_req = trend.score
                        break
                row.append(score_for_req)
            
            z_data.append(row)
        
        result = {
            'x': requirements,
            'y': y_data,
            'z': z_data,
            'versions': versions,
            'title': 'Per-Requirement Compliance Scores',
            'colorscale': 'RdYlGn',  # Red-Yellow-Green
            'zmin': 0,
            'zmax': 1
        }
        
        logger.info(f"Heatmap: {len(requirements)} requirements × {len(scores)} versions")
        return result

    def transform_version_comparison(
        self,
        comparison: VersionComparisonResult
    ) -> Dict[str, Any]:
        """
        Transform version comparison to visualization format.
        
        Args:
            comparison: VersionComparisonResult from query service
        
        Returns:
            Dictionary with comparison data
            Format: {
                'version_a': str,
                'version_b': str,
                'overall_scores': [score_a, score_b],
                'overall_change': float,
                'per_requirement': {req: change},
                'improved': [req_ids],
                'regressed': [req_ids],
                'stable': [req_ids]
            }
        """
        logger.debug(f"Transforming comparison: {comparison.version_a} vs {comparison.version_b}")
        
        result = {
            'version_a': comparison.version_a,
            'version_b': comparison.version_b,
            'overall_scores': {
                'a': comparison.overall_score_a,
                'b': comparison.overall_score_b
            },
            'overall_change': comparison.overall_score_change,
            'overall_change_percent': (
                (comparison.overall_score_change / comparison.overall_score_a * 100)
                if comparison.overall_score_a > 0 else 0
            ),
            'per_requirement': comparison.per_requirement_changes,
            'improved': comparison.improved_requirements,
            'regressed': comparison.regressed_requirements,
            'stable': comparison.stable_requirements,
            'summary': {
                'improved_count': len(comparison.improved_requirements),
                'regressed_count': len(comparison.regressed_requirements),
                'stable_count': len(comparison.stable_requirements)
            }
        }
        
        logger.info(
            f"Comparison: +{len(comparison.improved_requirements)} improved, "
            f"-{len(comparison.regressed_requirements)} regressed"
        )
        return result

    def transform_requirement_detail(
        self,
        requirement_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transform single requirement history to chart format.
        
        Args:
            requirement_id: Requirement ID to analyze
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            Dictionary with requirement detail data
        """
        logger.debug(f"Transforming detail for requirement: {requirement_id}")
        
        # Get trend
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                trends = self.query_service.get_per_requirement_trend(requirement_id, start, end)
            except:
                trends = self.query_service.get_per_requirement_trend(requirement_id)
        else:
            trends = self.query_service.get_per_requirement_trend(requirement_id)
        
        x_data = []
        y_data = []
        versions = []
        
        for trend in trends:
            try:
                dt = datetime.fromisoformat(trend.timestamp.replace('Z', '+00:00'))
                x_data.append(dt.strftime("%Y-%m-%d"))
            except:
                x_data.append(trend.timestamp)
            
            y_data.append(trend.score)
            versions.append(trend.version_identifier)
        
        result = {
            'requirement_id': requirement_id,
            'x': x_data,
            'y': y_data,
            'versions': versions,
            'title': f'Requirement {requirement_id} - Score Evolution',
            'min_score': min(y_data) if y_data else 0,
            'max_score': max(y_data) if y_data else 1,
            'avg_score': sum(y_data) / len(y_data) if y_data else 0,
            'latest_score': y_data[-1] if y_data else 0,
            'trend': self.query_service.compute_trend_direction(
                [ScoreTrendPoint(
                    timestamp=t.timestamp,
                    version_identifier=t.version_identifier,
                    overall_score=t.score,
                    git_branch="",
                    git_commit=""
                ) for t in trends]
            )
        }
        
        logger.info(f"Requirement detail: {len(trends)} data points, trend={result['trend']}")
        return result

    def transform_regression_alerts(
        self,
        threshold: float = 0.05
    ) -> Dict[str, Any]:
        """
        Transform regression detection to alert format.
        
        Args:
            threshold: Regression threshold (minimum score drop)
        
        Returns:
            Dictionary with regression alerts
        """
        logger.debug(f"Transforming regression alerts (threshold={threshold})")
        
        alerts = self.query_service.get_regression_alerts(threshold=threshold)
        
        # Categorize by severity
        critical = [a for a in alerts if a['drop'] >= 0.1]  # 10%+
        warning = [a for a in alerts if 0.05 <= a['drop'] < 0.1]  # 5-10%
        minor = [a for a in alerts if threshold <= a['drop'] < 0.05]  # threshold-5%
        
        result = {
            'total_regressions': len(alerts),
            'critical': critical,
            'warning': warning,
            'minor': minor,
            'alerts': alerts,
            'summary': {
                'critical_count': len(critical),
                'warning_count': len(warning),
                'minor_count': len(minor)
            }
        }
        
        logger.info(
            f"Regression alerts: {len(critical)} critical, "
            f"{len(warning)} warning, {len(minor)} minor"
        )
        return result

    def transform_summary_metrics(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Transform recent data to summary metrics.
        
        Args:
            days: Number of days to summarize (default 7)
        
        Returns:
            Dictionary with summary metrics
        """
        logger.debug(f"Transforming summary metrics for last {days} days")
        
        # Get recent scores
        recent_scores = self.query_service.get_last_n_days(days=days)
        
        if not recent_scores:
            logger.warning("No recent scores available")
            return {
                'period_days': days,
                'data_points': 0,
                'current_score': 0,
                'average_score': 0,
                'min_score': 0,
                'max_score': 0,
                'trend': 'stable'
            }
        
        # Compute metrics
        current = recent_scores[-1].overall_score
        avg = self.query_service.compute_average_score(recent_scores)
        min_score = min(s.overall_score for s in recent_scores)
        max_score = max(s.overall_score for s in recent_scores)
        trend = self.query_service.compute_trend_direction(recent_scores)
        
        # Compute change from first to last
        change = current - recent_scores[0].overall_score
        change_percent = (change / recent_scores[0].overall_score * 100) if recent_scores[0].overall_score > 0 else 0
        
        result = {
            'period_days': days,
            'data_points': len(recent_scores),
            'current_score': current,
            'average_score': avg,
            'min_score': min_score,
            'max_score': max_score,
            'change': change,
            'change_percent': change_percent,
            'trend': trend,
            'latest_version': recent_scores[-1].version_identifier,
            'latest_timestamp': recent_scores[-1].timestamp
        }
        
        logger.info(f"Summary metrics: current={current:.2%}, trend={trend}")
        return result

    def normalize_scores(self, scores: List[float]) -> List[float]:
        """
        Normalize scores to 0-1 range.
        
        Args:
            scores: List of scores (usually already 0-1, but can normalize if needed)
        
        Returns:
            List of normalized scores
        """
        if not scores or max(scores) == 0:
            return [0.0] * len(scores)
        
        min_score = min(scores)
        max_score = max(scores)
        range_val = max_score - min_score
        
        if range_val == 0:
            return [0.5] * len(scores)  # All same value
        
        return [(s - min_score) / range_val for s in scores]

    def compute_color_code(self, score: float) -> str:
        """
        Get color code for a score (for heatmaps).
        
        Args:
            score: Score value (0-1)
        
        Returns:
            RGB color code
        """
        # Green (high) to Red (low)
        if score >= 0.8:
            return 'rgb(76, 175, 80)'  # Green
        elif score >= 0.6:
            return 'rgb(255, 193, 7)'  # Amber
        elif score >= 0.4:
            return 'rgb(255, 152, 0)'  # Orange
        else:
            return 'rgb(244, 67, 54)'  # Red
