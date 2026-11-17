"""Validation for requirement specifications and scoring results."""

from __future__ import annotations

from typing import Any


class ValidationError(Exception):
    """Raised when a specification or score fails validation."""

    pass


def validate_spec(spec: dict[str, Any]) -> None:
    """Validate requirement specification structure and content.

    Args:
        spec: Loaded specification dictionary

    Raises:
        ValidationError: If spec is malformed or missing required fields
    """
    if not isinstance(spec, dict):
        raise ValidationError("Specification must be a dictionary")

    if "requirements" not in spec:
        raise ValidationError("Specification must contain 'requirements' key")

    if not isinstance(spec["requirements"], list):
        raise ValidationError("'requirements' must be a list")

    if len(spec["requirements"]) == 0:
        raise ValidationError("'requirements' cannot be empty")

    requirement_ids = set()
    for i, req in enumerate(spec["requirements"]):
        if not isinstance(req, dict):
            raise ValidationError(f"Requirement {i} must be a dictionary")

        # Check required fields
        for required_field in ["id", "description", "weight"]:
            if required_field not in req:
                raise ValidationError(
                    f"Requirement {i} missing required field: {required_field}"
                )

        req_id = req["id"]
        if not isinstance(req_id, str):
            raise ValidationError(f"Requirement {i} id must be a string")

        if req_id in requirement_ids:
            raise ValidationError(f"Duplicate requirement id: {req_id}")

        requirement_ids.add(req_id)

        # Validate weight
        try:
            weight = float(req["weight"])
            if weight <= 0:
                raise ValueError("weight must be positive")
            if not (weight < float("inf")):
                raise ValueError("weight cannot be infinite")
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Requirement {req_id} has invalid weight: {e}")

        # Validate description
        if not isinstance(req["description"], str) or not req["description"].strip():
            raise ValidationError(
                f"Requirement {req_id} description must be non-empty string"
            )

        # Optional fields validation
        if "test_markers" in req:
            if not isinstance(req["test_markers"], list):
                raise ValidationError(
                    f"Requirement {req_id} test_markers must be a list"
                )
            if not all(isinstance(m, str) for m in req["test_markers"]):
                raise ValidationError(
                    f"Requirement {req_id} test_markers must contain only strings"
                )

        if "evidence_sources" in req:
            if not isinstance(req["evidence_sources"], list):
                raise ValidationError(
                    f"Requirement {req_id} evidence_sources must be a list"
                )
            valid_sources = {"test_outcome", "manual_review"}
            for source in req["evidence_sources"]:
                if source not in valid_sources:
                    raise ValidationError(
                        f"Requirement {req_id} has invalid evidence_source: {source}"
                    )

    # Check weight constraints if specified
    if "weight_constraints" in spec:
        validate_weight_constraints(spec["weight_constraints"], spec["requirements"])


def validate_weights(requirements: list[dict[str, Any]]) -> None:
    """Validate weight ratios across requirements.

    Default constraint: min(weight) / max(weight) >= 0.5

    Args:
        requirements: List of requirement dictionaries

    Raises:
        ValidationError: If weight ratios violate constraints
    """
    if not requirements:
        raise ValidationError("Cannot validate empty requirements list")

    weights = [float(req["weight"]) for req in requirements]
    min_weight = min(weights)
    max_weight = max(weights)

    if max_weight == 0:
        raise ValidationError("Cannot have all zero weights")

    ratio = min_weight / max_weight
    min_ratio = 0.5

    if ratio < min_ratio:
        raise ValidationError(
            f"Weight ratio violation: min/max = {ratio:.3f}, "
            f"minimum required = {min_ratio}. "
            f"Adjust weights so smallest is at least {min_ratio} * largest."
        )


def validate_weight_constraints(
    constraints: dict[str, Any], requirements: list[dict[str, Any]]
) -> None:
    """Validate weight constraints from spec metadata.

    Args:
        constraints: Weight constraints from spec
        requirements: List of requirement dictionaries

    Raises:
        ValidationError: If constraints are violated
    """
    if "min_ratio" in constraints:
        min_ratio = float(constraints["min_ratio"])
        weights = [float(req["weight"]) for req in requirements]
        min_weight = min(weights)
        max_weight = max(weights)

        actual_ratio = min_weight / max_weight
        if actual_ratio < min_ratio:
            raise ValidationError(
                f"Weight ratio {actual_ratio:.3f} < {min_ratio} "
                f"specified in weight_constraints"
            )
