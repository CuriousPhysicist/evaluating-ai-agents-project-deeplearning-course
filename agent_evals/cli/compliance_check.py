"""Compliance checking for CI/CD gating.

This module implements the core logic for compliance checking against
configured thresholds, including:
- Loading and validating threshold configurations
- Comparing compliance scores against thresholds
- Detecting regressions from baseline
- Generating compliance reports with appropriate exit codes
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import yaml

from agent_evals.exit_codes import (
    ExitCode,
    ComplianceFailureReason,
    ConfigurationError,
    ComplianceRegressionError,
    ComplianceCheckResult,
)


logger = logging.getLogger(__name__)


class ThresholdConfig:
    """Manages compliance threshold configuration."""

    def __init__(self, config_path: str):
        """Load and validate threshold configuration from YAML file.

        Args:
            config_path: Path to threshold.yaml configuration file

        Raises:
            ConfigurationError: If file not found or YAML is invalid
        """
        self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise ConfigurationError(
                f"Threshold configuration file not found: {config_path}",
                reason=ComplianceFailureReason.CONFIG_MISSING_THRESHOLD,
            )

        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML in threshold configuration: {e}",
                reason=ComplianceFailureReason.CONFIG_INVALID_YAML,
            )
        except Exception as e:
            raise ConfigurationError(
                f"Error reading threshold configuration: {e}",
                reason=ComplianceFailureReason.CONFIG_MISSING_THRESHOLD,
            )

        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration structure and values.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.config:
            raise ConfigurationError(
                "Configuration file is empty",
                reason=ComplianceFailureReason.CONFIG_INVALID_YAML,
            )

        if "defaults" not in self.config:
            raise ConfigurationError(
                "Configuration missing 'defaults' section",
                reason=ComplianceFailureReason.CONFIG_INVALID_YAML,
            )

        defaults = self.config["defaults"]
        required_keys = {"overall_score", "per_requirement", "regression_allowed"}

        if not all(key in defaults for key in required_keys):
            raise ConfigurationError(
                f"Defaults missing required keys: {required_keys}",
                reason=ComplianceFailureReason.CONFIG_INVALID_YAML,
            )

        # Validate threshold values are between 0 and 1
        for key in required_keys:
            value = defaults[key]
            if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
                raise ConfigurationError(
                    f"Invalid threshold value for {key}: {value}",
                    reason=ComplianceFailureReason.CONFIG_INVALID_THRESHOLD,
                )

    def get_thresholds(self, environment: str = "development") -> Dict[str, float]:
        """Get thresholds for specified environment.

        Args:
            environment: Environment name (development, staging, production)

        Returns:
            Dictionary with keys: overall_score, per_requirement, regression_allowed

        Raises:
            ConfigurationError: If environment not found in configuration
        """
        defaults = self.config.get("defaults", {})

        environments = self.config.get("environments", {})
        env_config = environments.get(environment, {})

        # Start with defaults, override with environment-specific values
        thresholds = {
            "overall_score": env_config.get(
                "overall_score", defaults.get("overall_score", 0.80)
            ),
            "per_requirement": env_config.get(
                "per_requirement", defaults.get("per_requirement", 0.50)
            ),
            "regression_allowed": env_config.get(
                "regression_allowed", defaults.get("regression_allowed", 0.05)
            ),
        }

        # Validate the final thresholds
        for key, value in thresholds.items():
            if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
                raise ConfigurationError(
                    f"Invalid threshold value for {key} in {environment}: {value}",
                    reason=ComplianceFailureReason.CONFIG_INVALID_THRESHOLD,
                )

        return thresholds

    def get_baseline(self, baseline_name: str = "current") -> Optional[Dict[str, Any]]:
        """Get baseline configuration.

        Args:
            baseline_name: Name of baseline (default: "current")

        Returns:
            Baseline configuration dict or None if not found
        """
        baselines = self.config.get("baselines", {})
        return baselines.get(baseline_name)


class RegressionDetector:
    """Detects compliance regressions from baseline."""

    def __init__(self, baseline_config: Optional[Dict[str, Any]] = None):
        """Initialize regression detector with optional baseline.

        Args:
            baseline_config: Baseline configuration from ThresholdConfig
        """
        self.baseline_config = baseline_config
        self.baseline_score = baseline_config.get("overall_score") if baseline_config else None

    def detect_regression(
        self, current_score: float, regression_allowed: float
    ) -> Optional[float]:
        """Detect if score has regressed beyond allowed threshold.

        Args:
            current_score: Current compliance score (0.0-1.0)
            regression_allowed: Maximum allowed regression (0.0-1.0)

        Returns:
            Regression magnitude if regression detected, None otherwise
        """
        if self.baseline_score is None:
            return None

        regression = self.baseline_score - current_score

        # Detect regression using >= to catch exact boundary cases
        # floating point tolerance handled naturally by slight overage
        if regression > (regression_allowed + 1e-9):
            return regression

        return None

    def get_baseline_score(self) -> Optional[float]:
        """Get baseline score for comparison."""
        return self.baseline_score


class ComplianceChecker:
    """Main compliance checking orchestrator."""

    def __init__(self, threshold_config: ThresholdConfig):
        """Initialize checker with threshold configuration.

        Args:
            threshold_config: ThresholdConfig instance
        """
        self.threshold_config = threshold_config
        self.logger = logging.getLogger(__name__)

    def check(
        self,
        overall_score: float,
        per_requirement_scores: Optional[Dict[str, float]] = None,
        environment: str = "development",
        baseline_name: str = "current",
    ) -> ComplianceCheckResult:
        """Check compliance scores against thresholds.

        Args:
            overall_score: Overall compliance score (0.0-1.0)
            per_requirement_scores: Optional dict of requirement scores
            environment: Environment name for threshold selection
            baseline_name: Baseline name for regression detection

        Returns:
            ComplianceCheckResult with exit code and details

        Raises:
            ComplianceRegressionError: If compliance has regressed
        """
        # Get thresholds for environment
        thresholds = self.threshold_config.get_thresholds(environment)

        # Validate overall score
        if not isinstance(overall_score, (int, float)) or not (0.0 <= overall_score <= 1.0):
            raise ConfigurationError(
                f"Invalid overall score: {overall_score}",
                reason=ComplianceFailureReason.TEST_RESULTS_MISSING,
            )

        # Check per-requirement scores if provided
        per_req_threshold = thresholds["per_requirement"]
        failed_requirements = []

        if per_requirement_scores:
            for req_id, score in per_requirement_scores.items():
                if score < per_req_threshold:
                    failed_requirements.append(req_id)

        # Check for regression from baseline FIRST
        # (must pass baseline check before overall threshold check)
        baseline_config = self.threshold_config.get_baseline(baseline_name)
        regression_detector = RegressionDetector(baseline_config)

        regression_allowed = thresholds["regression_allowed"]
        regression = regression_detector.detect_regression(overall_score, regression_allowed)

        if regression is not None:
            details = {}
            if failed_requirements:
                details["failed_requirements"] = failed_requirements

            return ComplianceCheckResult(
                exit_code=ExitCode.COMPLIANCE_REGRESSION,
                reason=ComplianceFailureReason.REGRESSION_MAGNITUDE,
                message=f"Compliance regression {regression:.2%} exceeds allowed {regression_allowed:.2%}",
                overall_score=overall_score,
                threshold=thresholds["overall_score"],
                regression_magnitude=regression,
                details=details if details else None,
            )

        # Check overall score against threshold
        overall_threshold = thresholds["overall_score"]

        if overall_score < overall_threshold:
            details = {}
            if failed_requirements:
                details["failed_requirements"] = failed_requirements

            return ComplianceCheckResult(
                exit_code=ExitCode.COMPLIANCE_REGRESSION,
                reason=ComplianceFailureReason.REGRESSION_OVERALL,
                message=f"Overall compliance score {overall_score:.2%} below threshold {overall_threshold:.2%}",
                overall_score=overall_score,
                threshold=overall_threshold,
                details=details if details else None,
            )

        # All checks passed
        return ComplianceCheckResult(
            exit_code=ExitCode.SUCCESS,
            reason=ComplianceFailureReason.SUCCESS,
            message="All compliance checks passed",
            overall_score=overall_score,
            threshold=overall_threshold,
        )


def load_compliance_results(results_file: str) -> Dict[str, Any]:
    """Load compliance results from JSON file.

    Args:
        results_file: Path to .compliance_results.json

    Returns:
        Parsed compliance results

    Raises:
        ConfigurationError: If file not found or invalid JSON
    """
    results_path = Path(results_file)

    if not results_path.exists():
        raise ConfigurationError(
            f"Compliance results file not found: {results_file}",
            reason=ComplianceFailureReason.TEST_RESULTS_MISSING,
        )

    try:
        with open(results_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigurationError(
            f"Invalid JSON in compliance results: {e}",
            reason=ComplianceFailureReason.TEST_RESULTS_MISSING,
        )
    except Exception as e:
        raise ConfigurationError(
            f"Error reading compliance results: {e}",
            reason=ComplianceFailureReason.TEST_RESULTS_MISSING,
        )
