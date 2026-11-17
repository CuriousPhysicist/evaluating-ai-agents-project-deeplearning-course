"""Generic compliance scoring engine for specification requirements.

This module provides a framework-agnostic tool for measuring compliance with
arbitrary requirement specifications. Requirements are defined in YAML/JSON
configuration files, and evidence is gathered from test results to produce
per-requirement and aggregate compliance scores.

Key components:
- spec_loader: Parse and validate requirement specification files
- evidence_gatherer: Map test markers and results to requirement evidence
- scorer: Generic compliance score calculation engine
- validator: Validate spec format and score consistency
"""

from agent_evals.spec_assurance.spec_loader import (
    RequirementSpec,
    load_spec_from_yaml,
    load_spec_from_dict,
)
from agent_evals.spec_assurance.scorer import (
    ComplianceResult,
    calculate_compliance_score,
)
from agent_evals.spec_assurance.validator import (
    validate_spec,
    validate_weights,
    ValidationError as SpecValidationError,
)

__all__ = [
    "RequirementSpec",
    "load_spec_from_yaml",
    "load_spec_from_dict",
    "ComplianceResult",
    "calculate_compliance_score",
    "validate_spec",
    "validate_weights",
    "SpecValidationError",
]
