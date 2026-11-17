"""Load and parse requirement specification files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

try:
    import yaml
except ImportError:
    yaml = None

from agent_evals.spec_assurance.validator import validate_spec, ValidationError


class Requirement(TypedDict, total=False):
    """Type definition for a requirement entry."""

    id: str
    description: str
    weight: float
    test_markers: list[str]
    evidence_sources: list[str]
    notes: str


class RequirementSpec(TypedDict, total=False):
    """Type definition for a complete requirement specification."""

    metadata: dict[str, Any]
    requirements: list[Requirement]
    weight_constraints: dict[str, Any]


def load_spec_from_dict(spec_dict: dict[str, Any]) -> RequirementSpec:
    """Load and validate a specification from a dictionary.

    Args:
        spec_dict: Dictionary containing specification

    Returns:
        Validated RequirementSpec

    Raises:
        ValidationError: If specification is invalid
    """
    validate_spec(spec_dict)
    return spec_dict  # type: ignore


def load_spec_from_yaml(yaml_path: str | Path) -> RequirementSpec:
    """Load a specification from a YAML file.

    Args:
        yaml_path: Path to YAML specification file

    Returns:
        Validated RequirementSpec

    Raises:
        FileNotFoundError: If file does not exist
        yaml.YAMLError: If YAML parsing fails
        ValidationError: If specification is invalid
    """
    if yaml is None:
        raise ImportError(
            "PyYAML is required to load YAML specs. Install with: pip install pyyaml"
        )

    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Specification file not found: {yaml_path}")

    with open(path) as f:
        spec_dict = yaml.safe_load(f)

    if spec_dict is None:
        raise ValidationError("YAML file is empty or contains only comments")

    return load_spec_from_dict(spec_dict)


def load_spec_from_json(json_path: str | Path) -> RequirementSpec:
    """Load a specification from a JSON file.

    Args:
        json_path: Path to JSON specification file

    Returns:
        Validated RequirementSpec

    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If JSON parsing fails
        ValidationError: If specification is invalid
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Specification file not found: {json_path}")

    with open(path) as f:
        spec_dict = json.load(f)

    return load_spec_from_dict(spec_dict)
