"""Generic compliance score calculation engine."""

from __future__ import annotations

from typing import Any, TypedDict

from agent_evals.spec_assurance.evidence_gatherer import (
    compute_score_from_test_outcomes,
    gather_evidence_from_markers,
)
from agent_evals.spec_assurance.spec_loader import RequirementSpec
from agent_evals.spec_assurance.validator import validate_spec, validate_weights


class RequirementResult(TypedDict, total=False):
    """Result for a single requirement."""

    requirement_id: str
    description: str
    score: float
    weight: float
    weighted_score: float
    test_outcomes: dict[str, str]
    test_counts: dict[str, int]
    evidence_source: str


class AggregateResult(TypedDict, total=False):
    """Aggregate statistics across all requirements."""

    total_weight: float
    total_score: float
    total_pass: int
    total_fail: int
    total_skip: int
    compliance_percentage: float


class ComplianceResult(TypedDict, total=False):
    """Complete compliance scoring result."""

    overall_score: float
    compliance_percentage: float
    per_requirement: dict[str, RequirementResult]
    aggregate: AggregateResult
    metadata: dict[str, Any]


def calculate_compliance_score(
    spec: RequirementSpec,
    test_results: dict[str, str],
) -> ComplianceResult:
    """Calculate compliance score for a specification against test results.

    Args:
        spec: RequirementSpec loaded from YAML/JSON/dict
        test_results: Dict mapping pytest marker names to outcomes
                     (e.g., {'T1_setup': 'pass', 'T10_limit': 'fail'})

    Returns:
        ComplianceResult with per-requirement and aggregate scores
    """
    # Validate inputs
    validate_spec(spec)
    validate_weights(spec["requirements"])

    requirements = spec["requirements"]
    per_requirement: dict[str, RequirementResult] = {}

    total_weighted_score = 0.0
    total_weight = 0.0
    total_pass = 0
    total_fail = 0
    total_skip = 0

    # Score each requirement
    for req in requirements:
        req_id = req["id"]
        description = req["description"]
        weight = float(req["weight"])

        # Gather evidence from test markers
        markers = req.get("test_markers", [])
        evidence = gather_evidence_from_markers(req_id, markers, test_results)

        # Compute score from test outcomes
        outcomes = evidence.get("test_outcomes", {})
        score, counts = compute_score_from_test_outcomes(outcomes)

        weighted_score = score * weight

        per_requirement[req_id] = {
            "requirement_id": req_id,
            "description": description,
            "score": score,
            "weight": weight,
            "weighted_score": weighted_score,
            "test_outcomes": outcomes,
            "test_counts": counts,
            "evidence_source": evidence.get("source", "unknown"),
        }

        total_weighted_score += weighted_score
        total_weight += weight
        total_pass += counts["pass"]
        total_fail += counts["fail"]
        total_skip += counts["skip"]

    # Calculate overall score
    overall_score = (
        total_weighted_score / total_weight if total_weight > 0 else 0.0
    )
    compliance_percentage = overall_score * 100.0

    return {
        "overall_score": overall_score,
        "compliance_percentage": compliance_percentage,
        "per_requirement": per_requirement,
        "aggregate": {
            "total_weight": total_weight,
            "total_score": total_weighted_score,
            "total_pass": total_pass,
            "total_fail": total_fail,
            "total_skip": total_skip,
            "compliance_percentage": compliance_percentage,
        },
        "metadata": spec.get("metadata", {}),
    }
