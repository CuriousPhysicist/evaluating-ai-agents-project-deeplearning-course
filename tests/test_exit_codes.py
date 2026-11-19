"""Tests for exit code contract and compliance check results."""

import pytest

from agent_evals.exit_codes import (
    ExitCode,
    ComplianceFailureReason,
    ConfigurationError,
    ComplianceRegressionError,
    TestExecutionError,
    MissingBaselineError,
    ComplianceCheckResult,
    exit_code_to_message,
)


class TestExitCodes:
    """Test exit code definitions."""

    def test_exit_code_values(self):
        """Verify exit code integer values."""
        assert ExitCode.SUCCESS == 0
        assert ExitCode.COMPLIANCE_REGRESSION == 1
        assert ExitCode.CONFIGURATION_ERROR == 2
        assert ExitCode.TEST_FAILURE == 3
        assert ExitCode.MISSING_BASELINE == 4

    def test_exit_code_is_int_enum(self):
        """Verify ExitCode is an IntEnum."""
        assert isinstance(ExitCode.SUCCESS, int)
        assert ExitCode.SUCCESS == 0
        # Can be used directly as exit code
        exit_code = ExitCode.SUCCESS
        assert exit_code == 0

    def test_all_exit_codes_unique(self):
        """Verify all exit codes have unique values."""
        codes = [
            ExitCode.SUCCESS,
            ExitCode.COMPLIANCE_REGRESSION,
            ExitCode.CONFIGURATION_ERROR,
            ExitCode.TEST_FAILURE,
            ExitCode.MISSING_BASELINE,
        ]
        assert len(codes) == len(set(codes))


class TestComplianceFailureReasons:
    """Test failure reason enumerations."""

    def test_success_reason_exists(self):
        """Verify success reason."""
        assert ComplianceFailureReason.SUCCESS.value == "All tests passed and compliance met"

    def test_regression_reasons(self):
        """Verify regression-related reasons."""
        reasons = [
            ComplianceFailureReason.REGRESSION_OVERALL,
            ComplianceFailureReason.REGRESSION_REQUIREMENT,
            ComplianceFailureReason.REGRESSION_MAGNITUDE,
        ]
        assert all(isinstance(r, ComplianceFailureReason) for r in reasons)

    def test_configuration_error_reasons(self):
        """Verify configuration error reasons."""
        reasons = [
            ComplianceFailureReason.CONFIG_MISSING_THRESHOLD,
            ComplianceFailureReason.CONFIG_INVALID_YAML,
            ComplianceFailureReason.CONFIG_INVALID_THRESHOLD,
            ComplianceFailureReason.CONFIG_MISSING_ENVIRONMENT,
            ComplianceFailureReason.CONFIG_MISSING_SPEC,
        ]
        assert all(isinstance(r, ComplianceFailureReason) for r in reasons)

    def test_all_reasons_have_values(self):
        """Verify all reasons have string values."""
        for reason in ComplianceFailureReason:
            assert isinstance(reason.value, str)
            assert len(reason.value) > 0


class TestConfigurationError:
    """Test ConfigurationError exception."""

    def test_configuration_error_basic(self):
        """Test basic ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Config file not found")

        assert exc_info.value.message == "Config file not found"
        assert exc_info.value.exit_code == ExitCode.CONFIGURATION_ERROR
        assert exc_info.value.reason == ComplianceFailureReason.CONFIG_MISSING_THRESHOLD

    def test_configuration_error_custom_reason(self):
        """Test ConfigurationError with custom reason."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError(
                "Invalid YAML",
                reason=ComplianceFailureReason.CONFIG_INVALID_YAML,
            )

        assert exc_info.value.reason == ComplianceFailureReason.CONFIG_INVALID_YAML
        assert exc_info.value.exit_code == ExitCode.CONFIGURATION_ERROR

    def test_configuration_error_string_representation(self):
        """Test ConfigurationError string representation."""
        error = ConfigurationError("Missing file")
        assert str(error) == "Missing file"


class TestComplianceRegressionError:
    """Test ComplianceRegressionError exception."""

    def test_compliance_regression_error_basic(self):
        """Test basic ComplianceRegressionError."""
        with pytest.raises(ComplianceRegressionError) as exc_info:
            raise ComplianceRegressionError("Score dropped from 0.90 to 0.75")

        assert exc_info.value.message == "Score dropped from 0.90 to 0.75"
        assert exc_info.value.exit_code == ExitCode.COMPLIANCE_REGRESSION

    def test_compliance_regression_error_reason(self):
        """Test ComplianceRegressionError reason."""
        with pytest.raises(ComplianceRegressionError) as exc_info:
            raise ComplianceRegressionError(
                "Score dropped",
                reason=ComplianceFailureReason.REGRESSION_REQUIREMENT,
            )

        assert exc_info.value.reason == ComplianceFailureReason.REGRESSION_REQUIREMENT


class TestTestExecutionError:
    """Test TestExecutionError exception."""

    def test_test_execution_error_basic(self):
        """Test basic TestExecutionError."""
        with pytest.raises(TestExecutionError) as exc_info:
            raise TestExecutionError("5 tests failed")

        assert exc_info.value.message == "5 tests failed"
        assert exc_info.value.exit_code == ExitCode.TEST_FAILURE


class TestMissingBaselineError:
    """Test MissingBaselineError exception."""

    def test_missing_baseline_error_basic(self):
        """Test basic MissingBaselineError."""
        with pytest.raises(MissingBaselineError) as exc_info:
            raise MissingBaselineError("Baseline 'v1.0' not found")

        assert exc_info.value.message == "Baseline 'v1.0' not found"
        assert exc_info.value.exit_code == ExitCode.MISSING_BASELINE


class TestComplianceCheckResult:
    """Test ComplianceCheckResult dataclass."""

    def test_result_creation_success(self):
        """Test creating a success result."""
        result = ComplianceCheckResult(
            exit_code=ExitCode.SUCCESS,
            reason=ComplianceFailureReason.SUCCESS,
            message="All checks passed",
            overall_score=0.95,
            threshold=0.80,
        )

        assert result.exit_code == 0
        assert result.overall_score == 0.95
        assert result.threshold == 0.80
        assert result.regression_magnitude is None

    def test_result_creation_regression(self):
        """Test creating a regression result."""
        result = ComplianceCheckResult(
            exit_code=ExitCode.COMPLIANCE_REGRESSION,
            reason=ComplianceFailureReason.REGRESSION_OVERALL,
            message="Score below threshold",
            overall_score=0.70,
            threshold=0.80,
            regression_magnitude=0.10,
        )

        assert result.exit_code == 1
        assert result.regression_magnitude == 0.10

    def test_result_string_representation(self):
        """Test result string representation."""
        result = ComplianceCheckResult(
            exit_code=ExitCode.SUCCESS,
            reason=ComplianceFailureReason.SUCCESS,
            message="All checks passed",
            overall_score=0.95,
            threshold=0.80,
        )

        result_str = str(result)
        assert "Exit Code: 0" in result_str
        assert "Overall Score: 95.00%" in result_str
        assert "Threshold: 80.00%" in result_str

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = ComplianceCheckResult(
            exit_code=ExitCode.SUCCESS,
            reason=ComplianceFailureReason.SUCCESS,
            message="All checks passed",
            overall_score=0.95,
            threshold=0.80,
        )

        result_dict = result.to_dict()
        assert result_dict["exit_code"] == 0
        assert result_dict["reason"] == "All tests passed and compliance met"
        assert result_dict["overall_score"] == 0.95
        assert result_dict["threshold"] == 0.80

    def test_result_with_details(self):
        """Test result with additional details."""
        details = {
            "failed_requirements": ["T5", "T12"],
            "environment": "staging",
        }
        result = ComplianceCheckResult(
            exit_code=ExitCode.COMPLIANCE_REGRESSION,
            reason=ComplianceFailureReason.REGRESSION_REQUIREMENT,
            message="Some requirements below threshold",
            details=details,
        )

        assert result.details == details
        result_dict = result.to_dict()
        assert result_dict["details"] == details


class TestExitCodeToMessage:
    """Test exit code to message conversion."""

    def test_all_exit_codes_have_messages(self):
        """Verify all exit codes have messages."""
        for code in ExitCode:
            message = exit_code_to_message(code)
            assert isinstance(message, str)
            assert len(message) > 0

    def test_specific_messages(self):
        """Test specific exit code messages."""
        assert "passed" in exit_code_to_message(ExitCode.SUCCESS).lower()
        assert "regression" in exit_code_to_message(ExitCode.COMPLIANCE_REGRESSION).lower()
        assert "configuration" in exit_code_to_message(ExitCode.CONFIGURATION_ERROR).lower()
        assert "test" in exit_code_to_message(ExitCode.TEST_FAILURE).lower()
        assert "baseline" in exit_code_to_message(ExitCode.MISSING_BASELINE).lower()

    def test_unknown_exit_code(self):
        """Test unknown exit code handling."""
        message = exit_code_to_message(999)
        assert "Unknown" in message
        assert "999" in message
