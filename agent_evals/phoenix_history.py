"""Historical compliance score tracking in Phoenix.

This module provides persistent storage and retrieval of compliance scores
using the Phoenix tracing/analytics platform. It enables tracking of compliance
scores across multiple experiment runs and agent versions.

Key features:
- Store compliance scores with version and git metadata
- Query historical scores by version, date range, or requirement
- Compare compliance across versions to detect regressions
- Fail gracefully - storage errors don't block evaluation pipeline
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Any

from phoenix.client import Client

from agent_evals.spec_assurance.scorer import ComplianceResult, RequirementResult

logger = logging.getLogger(__name__)


class HistoricalScoreTracker:
    """Manage historical compliance score tracking in Phoenix.

    Stores compliance scores alongside git metadata (version, branch, baseline)
    to enable tracking and comparison across experiment runs. Each compliance
    result is stored as a separate Phoenix record per requirement.

    Data format: Scores are stored with version identifier (semantic + timestamp)
    and queryable by requirement_id, version, timestamp, and git metadata.

    Example versioning: v1.2.3-20261120-143000
        v1.2.3: semantic version
        20261120: date (YYYYMMDD)
        143000: time (HHMMSS)
    """

    # Phoenix project namespace for historical scores
    PROJECT_NAME = "agent-compliance-history"

    # Attributes used for historical score records in Phoenix
    SCORE_RECORD_TYPE = "compliance_score"
    ATTRIBUTE_VERSION = "compliance_version"
    ATTRIBUTE_REQUIREMENT_ID = "requirement_id"
    ATTRIBUTE_SCORE = "score"
    ATTRIBUTE_WEIGHT = "weight"
    ATTRIBUTE_WEIGHTED_SCORE = "weighted_score"
    ATTRIBUTE_BRANCH = "git_branch"
    ATTRIBUTE_BASELINE = "baseline_version"
    ATTRIBUTE_TIMESTAMP = "evaluation_timestamp"

    def __init__(
        self,
        phoenix_client: Client,
        version: str,
        branch: str = "unknown",
        baseline_version: str = "unknown",
    ):
        """Initialize the historical score tracker.

        Args:
            phoenix_client: Phoenix Client instance for storage operations
            version: Version identifier (e.g., "v1.2.3-20261120-143000")
            branch: Git branch name (default: "unknown")
            baseline_version: Baseline version for regression comparison (default: "unknown")

        Raises:
            ValueError: If version is empty or invalid
        """
        if not version or not isinstance(version, str):
            raise ValueError(f"Invalid version: {version}")

        self.client = phoenix_client
        self.version = version
        self.branch = branch
        self.baseline_version = baseline_version
        self.timestamp = datetime.utcnow().isoformat()

    def store_evaluation_results(
        self,
        compliance_result: ComplianceResult,
    ) -> bool:
        """Store compliance evaluation results in Phoenix.

        Stores one Phoenix record per requirement in the compliance result,
        including the score, weight, metadata, and git information.

        Args:
            compliance_result: ComplianceResult from scoring engine

        Returns:
            True if all records stored successfully, False if any storage failed
            (storage failure does not raise - returns False and logs error)
        """
        if not compliance_result or not isinstance(compliance_result, dict):
            logger.error("Invalid compliance_result provided to store_evaluation_results")
            return False

        per_requirement = compliance_result.get("per_requirement", {})
        if not per_requirement:
            logger.warning("No per-requirement results to store")
            return False

        all_stored = True

        for req_id, req_result in per_requirement.items():
            try:
                if not self._store_requirement_score(req_id, req_result):
                    all_stored = False
                    logger.warning(f"Failed to store score for requirement {req_id}")
            except Exception as e:
                # Fail gracefully - don't let storage errors block evaluation
                logger.error(
                    f"Exception storing requirement {req_id}: {e}",
                    exc_info=True,
                )
                all_stored = False

        return all_stored

    def _store_requirement_score(
        self,
        requirement_id: str,
        requirement_result: RequirementResult,
    ) -> bool:
        """Store a single requirement's score in Phoenix.

        Args:
            requirement_id: ID of the requirement
            requirement_result: RequirementResult with score and metadata

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Extract score data
            score = float(requirement_result.get("score", 0.0))
            weight = float(requirement_result.get("weight", 1.0))
            weighted_score = float(requirement_result.get("weighted_score", 0.0))

            # Build attributes for Phoenix record
            attributes = {
                self.ATTRIBUTE_VERSION: self.version,
                self.ATTRIBUTE_REQUIREMENT_ID: requirement_id,
                self.ATTRIBUTE_SCORE: score,
                self.ATTRIBUTE_WEIGHT: weight,
                self.ATTRIBUTE_WEIGHTED_SCORE: weighted_score,
                self.ATTRIBUTE_BRANCH: self.branch,
                self.ATTRIBUTE_BASELINE: self.baseline_version,
                self.ATTRIBUTE_TIMESTAMP: self.timestamp,
                "test_outcomes": json.dumps(requirement_result.get("test_outcomes", {})),
                "test_counts": json.dumps(requirement_result.get("test_counts", {})),
                "evidence_source": requirement_result.get("evidence_source", "unknown"),
            }

            # Store in Phoenix - create a document/record per requirement
            # This allows querying and filtering by requirement and version
            self.client.log_traces(
                documents=[
                    {
                        "name": f"{self.SCORE_RECORD_TYPE}_{requirement_id}_{self.version}",
                        "attributes": attributes,
                        "timestamp": self.timestamp,
                    }
                ]
            )

            logger.debug(
                f"Stored score for {requirement_id}: {score:.3f} "
                f"(weight: {weight:.3f}, version: {self.version})"
            )
            return True

        except (ValueError, TypeError, KeyError) as e:
            logger.error(
                f"Error storing requirement score for {requirement_id}: {e}",
                exc_info=True,
            )
            return False
        except Exception as e:
            # Catch Phoenix client errors
            logger.error(
                f"Phoenix storage error for {requirement_id}: {e}",
                exc_info=True,
            )
            return False

    def get_scores_for_version(
        self,
        version: Optional[str] = None,
    ) -> dict[str, RequirementResult]:
        """Retrieve compliance scores for a specific version.

        Queries Phoenix for all score records matching the given version.
        If no version specified, uses the tracker's current version.

        Args:
            version: Version identifier to retrieve (default: current tracker version)

        Returns:
            Dictionary mapping requirement_id to RequirementResult scores
            Returns empty dict if no scores found or query fails
        """
        if version is None:
            version = self.version

        if not version:
            logger.error("No version specified for score retrieval")
            return {}

        try:
            # Query Phoenix for all scores with this version
            # Note: Actual implementation depends on Phoenix query API available
            # This is a placeholder for the actual query implementation
            results = self._query_phoenix_by_version(version)
            return results

        except Exception as e:
            logger.error(f"Error retrieving scores for version {version}: {e}", exc_info=True)
            return {}

    def _query_phoenix_by_version(
        self,
        version: str,
    ) -> dict[str, RequirementResult]:
        """Execute Phoenix query for all scores matching a version.

        Args:
            version: Version identifier to query

        Returns:
            Dictionary mapping requirement_id to RequirementResult
        """
        results: dict[str, RequirementResult] = {}

        try:
            # Query Phoenix for documents with matching version attribute
            # This is a placeholder implementation that would use the Phoenix SDK
            # to query stored records by attribute values

            # For now, return empty dict - full implementation in Phase 2/3
            # when Phoenix query API integration is complete
            logger.debug(f"Querying Phoenix for version {version}")
            return results

        except Exception as e:
            logger.error(f"Phoenix query error: {e}", exc_info=True)
            return {}

    def get_scores_by_date_range(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        requirement_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Retrieve compliance scores within a date range.

        Queries Phoenix for all score records within the specified date range.
        Optionally filters by specific requirement.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive), defaults to now
            requirement_id: Optional requirement_id to filter results

        Returns:
            List of score records with metadata
            Returns empty list if no scores found or query fails
        """
        if end_date is None:
            end_date = datetime.utcnow()

        if start_date > end_date:
            logger.error("start_date cannot be after end_date")
            return []

        try:
            results = self._query_phoenix_by_date_range(start_date, end_date, requirement_id)
            return results

        except Exception as e:
            logger.error(
                f"Error retrieving scores for date range {start_date} to {end_date}: {e}",
                exc_info=True,
            )
            return []

    def _query_phoenix_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        requirement_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Execute Phoenix query for scores in date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            requirement_id: Optional requirement filter

        Returns:
            List of matching score records
        """
        results: list[dict[str, Any]] = []

        try:
            # Query Phoenix for documents with timestamps in range
            # Optionally filter by requirement_id attribute

            logger.debug(
                f"Querying Phoenix for scores from {start_date} to {end_date}"
                + (f" (requirement: {requirement_id})" if requirement_id else "")
            )
            return results

        except Exception as e:
            logger.error(f"Phoenix date range query error: {e}", exc_info=True)
            return []

    def compare_versions(
        self,
        version1: str,
        version2: str,
    ) -> Optional[dict[str, Any]]:
        """Compare compliance scores between two versions.

        Retrieves scores for both versions and computes delta (improvement/regression).
        Used to detect regressions or track improvements across experiment runs.

        Args:
            version1: First version to compare
            version2: Second version to compare

        Returns:
            Dictionary with comparison results:
            {
                "version1": version1,
                "version2": version2,
                "version1_scores": {...},
                "version2_scores": {...},
                "deltas": {...},  # score_v2 - score_v1
                "regressions": [...],  # requirements where score decreased
                "improvements": [...],  # requirements where score increased
            }
            Returns None if comparison fails
        """
        try:
            scores1 = self.get_scores_for_version(version1)
            scores2 = self.get_scores_for_version(version2)

            if not scores1 or not scores2:
                logger.warning(
                    f"Could not retrieve scores for comparison: "
                    f"v1={len(scores1)} scores, v2={len(scores2)} scores"
                )
                return None

            return self._compute_version_comparison(version1, version2, scores1, scores2)

        except Exception as e:
            logger.error(f"Error comparing versions {version1} and {version2}: {e}", exc_info=True)
            return None

    def _compute_version_comparison(
        self,
        version1: str,
        version2: str,
        scores1: dict[str, RequirementResult],
        scores2: dict[str, RequirementResult],
    ) -> dict[str, Any]:
        """Compute deltas and regression detection between two versions.

        Args:
            version1: First version identifier
            version2: Second version identifier
            scores1: Scores from version 1
            scores2: Scores from version 2

        Returns:
            Comparison result with deltas and regression info
        """
        deltas: dict[str, float] = {}
        regressions: list[str] = []
        improvements: list[str] = []

        # Compare scores for requirements present in both versions
        for req_id in scores1:
            if req_id not in scores2:
                continue

            score1 = float(scores1[req_id].get("score", 0.0))
            score2 = float(scores2[req_id].get("score", 0.0))
            delta = score2 - score1

            deltas[req_id] = delta

            if delta < 0:
                regressions.append(req_id)
            elif delta > 0:
                improvements.append(req_id)

        return {
            "version1": version1,
            "version2": version2,
            "version1_scores": scores1,
            "version2_scores": scores2,
            "deltas": deltas,
            "regressions": regressions,
            "improvements": improvements,
            "comparison_timestamp": datetime.utcnow().isoformat(),
        }

    def detect_regression(
        self,
        version1: str,
        version2: str,
        regression_threshold: float = 0.05,
    ) -> Optional[tuple[bool, list[str]]]:
        """Detect if version2 has regression relative to version1.

        A regression is detected if any requirement's score decreased by more
        than the regression_threshold (default 5%).

        Args:
            version1: Baseline version for comparison
            version2: Version to check for regression
            regression_threshold: Maximum allowed decrease in score (0.0-1.0)

        Returns:
            Tuple of (has_regression: bool, regression_requirements: list[str])
            Returns None if comparison fails
        """
        comparison = self.compare_versions(version1, version2)
        if comparison is None:
            return None

        regressions_above_threshold = []
        for req_id, delta in comparison.get("deltas", {}).items():
            if delta < -regression_threshold:
                regressions_above_threshold.append(req_id)

        has_regression = len(regressions_above_threshold) > 0

        logger.info(
            f"Regression detection: {version1} → {version2} = "
            f"{'HAS REGRESSION' if has_regression else 'OK'} "
            f"(threshold: {regression_threshold:.1%})"
        )
        if regressions_above_threshold:
            logger.warning(f"Regressions in requirements: {regressions_above_threshold}")

        return has_regression, regressions_above_threshold
