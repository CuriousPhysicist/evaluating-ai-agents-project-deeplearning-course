"""Tests for the generic spec_assurance scoring engine."""

from __future__ import annotations

import pytest

from agent_evals.spec_assurance.evidence_gatherer import (
    compute_score_from_test_outcomes,
    gather_evidence_from_manual_review,
    gather_evidence_from_markers,
)
from agent_evals.spec_assurance.scorer import calculate_compliance_score
from agent_evals.spec_assurance.spec_loader import (
    load_spec_from_dict,
    load_spec_from_json,
    load_spec_from_yaml,
)
from agent_evals.spec_assurance.validator import (
    ValidationError,
    validate_spec,
    validate_weights,
)


class TestValidator:
    """Test specification validation."""

    def test_validate_spec_requires_requirements_key(self):
        """Specification must have requirements key."""
        with pytest.raises(ValidationError, match="'requirements' key"):
            validate_spec({})

    def test_validate_spec_requires_requirements_list(self):
        """Requirements must be a list."""
        with pytest.raises(ValidationError, match="must be a list"):
            validate_spec({"requirements": "not a list"})

    def test_validate_spec_requires_non_empty_requirements(self):
        """Requirements list cannot be empty."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_spec({"requirements": []})

    def test_validate_spec_requires_id_description_weight(self):
        """Each requirement must have id, description, and weight."""
        spec = {
            "requirements": [
                {"id": "T1"}  # Missing description and weight
            ]
        }
        with pytest.raises(ValidationError, match="missing required field"):
            validate_spec(spec)

    def test_validate_spec_detects_duplicate_ids(self):
        """Duplicate requirement IDs are rejected."""
        spec = {
            "requirements": [
                {"id": "T1", "description": "First", "weight": 1.0},
                {"id": "T1", "description": "Second", "weight": 1.0},
            ]
        }
        with pytest.raises(ValidationError, match="Duplicate requirement id"):
            validate_spec(spec)

    def test_validate_spec_requires_positive_weight(self):
        """Weight must be positive."""
        spec = {
            "requirements": [
                {"id": "T1", "description": "Test", "weight": 0}
            ]
        }
        with pytest.raises(ValidationError, match="invalid weight"):
            validate_spec(spec)

    def test_validate_spec_accepts_valid_spec(self):
        """Valid specification passes validation."""
        spec = {
            "requirements": [
                {"id": "T1", "description": "First requirement", "weight": 1.0}
            ]
        }
        validate_spec(spec)  # Should not raise

    def test_validate_weights_enforces_min_ratio(self):
        """Weight ratio must meet minimum constraint."""
        requirements = [
            {"id": "T1", "weight": 1.0},
            {"id": "T2", "weight": 10.0},  # Ratio = 0.1 < 0.5
        ]
        with pytest.raises(ValidationError, match="Weight ratio violation"):
            validate_weights(requirements)

    def test_validate_weights_accepts_good_ratio(self):
        """Weights with good ratio pass validation."""
        requirements = [
            {"id": "T1", "weight": 0.5},
            {"id": "T2", "weight": 1.0},  # Ratio = 0.5, OK
        ]
        validate_weights(requirements)  # Should not raise

    def test_validate_weights_rejects_zero_weights(self):
        """Cannot have all zero weights."""
        requirements = [
            {"id": "T1", "weight": 0.0},
        ]
        with pytest.raises(ValidationError, match="all zero weights"):
            validate_weights(requirements)


class TestEvidenceGatherer:
    """Test evidence gathering from test results."""

    def test_gather_evidence_from_markers_all_pass(self):
        """Gather evidence when all tests pass."""
        markers = ["T1_setup", "T1_structure"]
        test_results = {"T1_setup": "pass", "T1_structure": "pass"}

        evidence = gather_evidence_from_markers("T1", markers, test_results)

        assert evidence["requirement_id"] == "T1"
        assert evidence["test_markers"] == markers
        assert evidence["test_outcomes"] == test_results
        assert evidence["source"] == "test_outcome"

    def test_gather_evidence_from_markers_partial_results(self):
        """Handle case where only some markers have results."""
        markers = ["T1_setup", "T1_structure", "T1_other"]
        test_results = {"T1_setup": "pass", "T1_structure": "pass"}

        evidence = gather_evidence_from_markers("T1", markers, test_results)

        assert evidence["test_outcomes"] == {"T1_setup": "pass", "T1_structure": "pass"}

    def test_gather_evidence_from_manual_review(self):
        """Create evidence from manual review score."""
        evidence = gather_evidence_from_manual_review("T1", 0.75)

        assert evidence["requirement_id"] == "T1"
        assert evidence["aggregated_score"] == 0.75
        assert evidence["source"] == "manual_review"

    def test_compute_score_all_pass(self):
        """Score when all tests pass."""
        outcomes = {"T1_a": "pass", "T1_b": "pass"}
        score, counts = compute_score_from_test_outcomes(outcomes)

        assert score == 1.0
        assert counts == {"pass": 2, "fail": 0, "skip": 0}

    def test_compute_score_all_fail(self):
        """Score when all tests fail."""
        outcomes = {"T1_a": "fail", "T1_b": "fail"}
        score, counts = compute_score_from_test_outcomes(outcomes)

        assert score == 0.0
        assert counts == {"pass": 0, "fail": 2, "skip": 0}

    def test_compute_score_mixed(self):
        """Score when tests are mixed pass/fail."""
        outcomes = {"T1_a": "pass", "T1_b": "fail"}
        score, counts = compute_score_from_test_outcomes(outcomes)

        assert score == 0.5
        assert counts == {"pass": 1, "fail": 1, "skip": 0}

    def test_compute_score_pass_and_skip(self):
        """Skipped tests don't reduce score."""
        outcomes = {"T1_a": "pass", "T1_b": "skip"}
        score, counts = compute_score_from_test_outcomes(outcomes)

        assert score == 1.0
        assert counts == {"pass": 1, "fail": 0, "skip": 1}

    def test_compute_score_no_outcomes(self):
        """Missing test outcomes gives zero score."""
        score, counts = compute_score_from_test_outcomes({})

        assert score == 0.0
        assert counts == {"pass": 0, "fail": 0, "skip": 0}


class TestScorer:
    """Test the compliance score calculator."""

    @pytest.fixture
    def simple_spec(self):
        """Simple 3-requirement spec for testing."""
        return {
            "metadata": {"version": "1.0"},
            "requirements": [
                {
                    "id": "T1",
                    "description": "First requirement",
                    "weight": 1.0,
                    "test_markers": ["T1_a", "T1_b"],
                },
                {
                    "id": "T2",
                    "description": "Second requirement",
                    "weight": 1.0,
                    "test_markers": ["T2_a"],
                },
                {
                    "id": "T3",
                    "description": "Third requirement",
                    "weight": 1.0,
                    "test_markers": ["T3_a", "T3_b"],
                },
            ],
        }

    def test_score_all_pass(self, simple_spec):
        """Calculate score when all tests pass."""
        test_results = {
            "T1_a": "pass",
            "T1_b": "pass",
            "T2_a": "pass",
            "T3_a": "pass",
            "T3_b": "pass",
        }

        result = calculate_compliance_score(simple_spec, test_results)

        assert result["overall_score"] == 1.0
        assert result["compliance_percentage"] == 100.0
        assert result["aggregate"]["total_pass"] == 5
        assert result["aggregate"]["total_fail"] == 0

    def test_score_all_fail(self, simple_spec):
        """Calculate score when all tests fail."""
        test_results = {
            "T1_a": "fail",
            "T1_b": "fail",
            "T2_a": "fail",
            "T3_a": "fail",
            "T3_b": "fail",
        }

        result = calculate_compliance_score(simple_spec, test_results)

        assert result["overall_score"] == 0.0
        assert result["compliance_percentage"] == 0.0
        assert result["aggregate"]["total_pass"] == 0
        assert result["aggregate"]["total_fail"] == 5

    def test_score_partial_coverage(self, simple_spec):
        """Calculate score with partial test coverage."""
        test_results = {
            "T1_a": "pass",
            "T1_b": "pass",
            "T2_a": "fail",
            "T3_a": "pass",
            "T3_b": "skip",
        }

        result = calculate_compliance_score(simple_spec, test_results)

        # T1: 1.0 (both pass)
        # T2: 0.0 (all fail)
        # T3: 1.0 (pass+skip counts as full)
        # Average: (1.0 + 0.0 + 1.0) / 3 = 0.667
        assert abs(result["overall_score"] - 0.667) < 0.01
        assert result["per_requirement"]["T1"]["score"] == 1.0
        assert result["per_requirement"]["T2"]["score"] == 0.0
        assert result["per_requirement"]["T3"]["score"] == 1.0

    def test_score_missing_test_results(self, simple_spec):
        """Handle missing test results gracefully."""
        test_results = {
            "T1_a": "pass",
            # T1_b missing
            "T2_a": "pass",
            # T3 results missing entirely
        }

        result = calculate_compliance_score(simple_spec, test_results)

        # T1: has 1 pass, scores as 1.0 (not all fail)
        # T2: has 1 pass, scores as 1.0
        # T3: has no results, scores as 0.0
        assert result["per_requirement"]["T1"]["score"] == 1.0
        assert result["per_requirement"]["T2"]["score"] == 1.0
        assert result["per_requirement"]["T3"]["score"] == 0.0

    def test_score_with_weighted_requirements(self):
        """Score with different weights per requirement."""
        spec = {
            "requirements": [
                {
                    "id": "T1",
                    "description": "Critical",
                    "weight": 2.0,
                    "test_markers": ["T1_a"],
                },
                {
                    "id": "T2",
                    "description": "Important",
                    "weight": 1.0,
                    "test_markers": ["T2_a"],
                },
            ],
        }
        test_results = {
            "T1_a": "pass",   # Score 1.0, weight 2.0 -> 2.0
            "T2_a": "fail",   # Score 0.0, weight 1.0 -> 0.0
        }

        result = calculate_compliance_score(spec, test_results)

        # Weighted: (1.0*2 + 0.0*1) / (2 + 1) = 2.0 / 3 = 0.667
        assert abs(result["overall_score"] - 0.667) < 0.01

    def test_score_per_requirement_details(self, simple_spec):
        """Verify per-requirement details are correct."""
        test_results = {
            "T1_a": "pass",
            "T1_b": "pass",
            "T2_a": "fail",
            "T3_a": "pass",
            "T3_b": "fail",
        }

        result = calculate_compliance_score(simple_spec, test_results)

        # Check T1 details
        t1_result = result["per_requirement"]["T1"]
        assert t1_result["requirement_id"] == "T1"
        assert t1_result["description"] == "First requirement"
        assert t1_result["weight"] == 1.0
        assert t1_result["score"] == 1.0
        assert t1_result["weighted_score"] == 1.0
        assert t1_result["test_counts"]["pass"] == 2
        assert t1_result["test_counts"]["fail"] == 0

        # Check T2 details
        t2_result = result["per_requirement"]["T2"]
        assert t2_result["score"] == 0.0
        assert t2_result["weighted_score"] == 0.0
        assert t2_result["test_counts"]["fail"] == 1

        # Check T3 details (mixed)
        t3_result = result["per_requirement"]["T3"]
        assert t3_result["score"] == 0.5
        assert t3_result["test_counts"]["pass"] == 1
        assert t3_result["test_counts"]["fail"] == 1

    def test_score_aggregate_totals(self, simple_spec):
        """Verify aggregate statistics are correct."""
        test_results = {
            "T1_a": "pass",
            "T1_b": "pass",
            "T2_a": "fail",
            "T3_a": "skip",
            "T3_b": "pass",
        }

        result = calculate_compliance_score(simple_spec, test_results)

        agg = result["aggregate"]
        assert agg["total_weight"] == 3.0
        assert agg["total_pass"] == 3
        assert agg["total_fail"] == 1
        assert agg["total_skip"] == 1
        assert agg["compliance_percentage"] == result["compliance_percentage"]


class TestSpecLoader:
    """Test specification loading and validation."""

    def test_load_spec_from_dict(self):
        """Load and validate spec from dictionary."""
        spec_dict = {
            "metadata": {"version": "1.0"},
            "requirements": [
                {"id": "T1", "description": "Test", "weight": 1.0}
            ],
        }

        spec = load_spec_from_dict(spec_dict)

        assert spec["metadata"]["version"] == "1.0"
        assert len(spec["requirements"]) == 1

    def test_load_spec_from_dict_invalid(self):
        """Invalid spec raises ValidationError."""
        spec_dict = {"requirements": []}  # Empty requirements

        with pytest.raises(ValidationError):
            load_spec_from_dict(spec_dict)

    def test_load_spec_from_yaml(self, tmp_path):
        """Load spec from YAML file."""
        yaml_file = tmp_path / "test_spec.yaml"
        yaml_file.write_text(
            """
metadata:
  version: "1.0"
requirements:
  - id: T1
    description: "Test requirement"
    weight: 1.0
"""
        )

        spec = load_spec_from_yaml(yaml_file)

        assert spec["metadata"]["version"] == "1.0"
        assert spec["requirements"][0]["id"] == "T1"

    def test_load_spec_from_yaml_missing_file(self):
        """Missing YAML file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_spec_from_yaml("/nonexistent/file.yaml")

    def test_load_spec_from_json(self, tmp_path):
        """Load spec from JSON file."""
        import json

        json_file = tmp_path / "test_spec.json"
        json_file.write_text(
            json.dumps({
                "metadata": {"version": "1.0"},
                "requirements": [
                    {"id": "T1", "description": "Test", "weight": 1.0}
                ],
            })
        )

        spec = load_spec_from_json(json_file)

        assert spec["metadata"]["version"] == "1.0"
