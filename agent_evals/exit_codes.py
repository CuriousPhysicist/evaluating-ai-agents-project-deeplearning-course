"""Exit code definitions for CI/CD integration.

This module defines standardized exit codes for use by the compliance checking
and evaluation pipeline. These codes enable CI/CD systems to make automated
decisions about pipeline continuation based on specific failure modes.

Exit Code Contract:
    0 - SUCCESS: All tests pass and compliance is above configured threshold
    1 - COMPLIANCE_REGRESSION: Compliance scores dropped below threshold
    2 - CONFIGURATION_ERROR: Invalid configuration, missing files, or setup issues
    3 - TEST_FAILURE: Tests failed during execution (non-compliance failure)
    4 - MISSING_BASELINE: No baseline available for regression comparison

Each exit code corresponds to a specific category of failure that enables
CI/CD pipelines to respond appropriately (e.g., fail the build, notify team,
require manual review, etc.).
"""

from enum import IntEnum, Enum
from dataclasses import dataclass
from typing import Optional


class ExitCode(IntEnum):
    """
    Standard exit codes for compliance checking and evaluation pipeline.
    
    These codes are designed to be used with CI/CD systems and shell scripts
    to enable automated decision-making about pipeline continuation.
    """

    SUCCESS = 0
    """All tests passed and compliance meets or exceeds threshold."""

    COMPLIANCE_REGRESSION = 1
    """Compliance score dropped below configured threshold or baseline."""

    CONFIGURATION_ERROR = 2
    """Invalid configuration, missing files, or setup issues."""

    TEST_FAILURE = 3
    """Test execution failed (not a compliance issue, but a test issue)."""

    MISSING_BASELINE = 4
    """No baseline available for regression comparison."""


class ComplianceFailureReason(Enum):
    """Detailed reasons for compliance check failures."""

    # Success
    SUCCESS = "All tests passed and compliance met"

    # Regression types
    REGRESSION_OVERALL = "Overall compliance score below threshold"
    REGRESSION_REQUIREMENT = "Individual requirement score decreased"
    REGRESSION_MAGNITUDE = "Score regression exceeded allowed tolerance"

    # Configuration errors
    CONFIG_MISSING_THRESHOLD = "Threshold configuration file not found"
    CONFIG_INVALID_YAML = "Invalid threshold configuration YAML syntax"
    CONFIG_INVALID_THRESHOLD = "Invalid threshold value in configuration"
    CONFIG_MISSING_ENVIRONMENT = "Requested environment not found in configuration"
    CONFIG_MISSING_SPEC = "Specification file not found"

    # Test failures
    TEST_COLLECTION_FAILED = "Pytest test collection failed"
    TEST_EXECUTION_FAILED = "Tests failed during execution"
    TEST_RESULTS_MISSING = "Test results not found"

    # Baseline issues
    BASELINE_NOT_FOUND = "Specified baseline version not found"
    BASELINE_LOAD_ERROR = "Error loading baseline data"
    BASELINE_INVALID = "Baseline data is invalid or corrupted"

    # Other
    UNKNOWN_ERROR = "Unknown error occurred"


class ComplianceCheckException(Exception):
    """Base class for compliance check exceptions."""

    def __init__(
        self,
        message: str,
        reason: ComplianceFailureReason,
        exit_code: int,
    ):
        self.message = message
        self.reason = reason
        self.exit_code = exit_code
        super().__init__(self.message)


class ConfigurationError(ComplianceCheckException):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        reason: ComplianceFailureReason = ComplianceFailureReason.CONFIG_MISSING_THRESHOLD,
    ):
        super().__init__(message, reason, ExitCode.CONFIGURATION_ERROR)


class ComplianceRegressionError(ComplianceCheckException):
    """Raised when compliance score drops below threshold."""

    def __init__(
        self,
        message: str,
        reason: ComplianceFailureReason = ComplianceFailureReason.REGRESSION_OVERALL,
    ):
        super().__init__(message, reason, ExitCode.COMPLIANCE_REGRESSION)


class TestExecutionError(ComplianceCheckException):
    """Raised when test execution fails."""

    def __init__(
        self,
        message: str,
        reason: ComplianceFailureReason = ComplianceFailureReason.TEST_EXECUTION_FAILED,
    ):
        super().__init__(message, reason, ExitCode.TEST_FAILURE)


class MissingBaselineError(ComplianceCheckException):
    """Raised when baseline is missing for comparison."""

    def __init__(
        self,
        message: str,
        reason: ComplianceFailureReason = ComplianceFailureReason.BASELINE_NOT_FOUND,
    ):
        super().__init__(message, reason, ExitCode.MISSING_BASELINE)


@dataclass
class ComplianceCheckResult:
    """Result of a compliance check operation."""

    exit_code: int
    """Exit code (0-4) corresponding to result type."""

    reason: ComplianceFailureReason
    """Detailed reason for the exit code."""

    message: str
    """Human-readable message explaining the result."""

    overall_score: Optional[float] = None
    """Overall compliance score (0.0-1.0), if available."""

    threshold: Optional[float] = None
    """Configured threshold (0.0-1.0), if available."""

    regression_magnitude: Optional[float] = None
    """Magnitude of regression detected, if applicable."""

    details: Optional[dict] = None
    """Additional details (failed requirements, etc.)."""

    def __str__(self) -> str:
        """Return human-readable representation."""
        lines = [
            f"Exit Code: {self.exit_code}",
            f"Reason: {self.reason.value}",
            f"Message: {self.message}",
        ]

        if self.overall_score is not None:
            lines.append(f"Overall Score: {self.overall_score:.2%}")

        if self.threshold is not None:
            lines.append(f"Threshold: {self.threshold:.2%}")

        if self.regression_magnitude is not None:
            lines.append(f"Regression: {self.regression_magnitude:.2%}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "exit_code": self.exit_code,
            "reason": self.reason.value,
            "message": self.message,
            "overall_score": self.overall_score,
            "threshold": self.threshold,
            "regression_magnitude": self.regression_magnitude,
            "details": self.details,
        }


def exit_code_to_message(code: int) -> str:
    """Convert exit code to human-readable message."""
    messages = {
        ExitCode.SUCCESS: "Compliance check passed",
        ExitCode.COMPLIANCE_REGRESSION: "Compliance regression detected",
        ExitCode.CONFIGURATION_ERROR: "Configuration error",
        ExitCode.TEST_FAILURE: "Test execution failed",
        ExitCode.MISSING_BASELINE: "Missing baseline for comparison",
    }
    return messages.get(code, f"Unknown exit code: {code}")
