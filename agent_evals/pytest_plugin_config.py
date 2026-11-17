"""Configuration schema for the compliance pytest plugin."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class CompliancePluginConfig(BaseModel):
    """Configuration for the compliance pytest plugin."""

    # Output settings
    report_output: str = Field(
        default=".compliance_results.json",
        description="Path to output compliance report JSON file",
    )
    
    # Behavior settings
    generate_report: bool = Field(
        default=True,
        description="Whether to generate compliance report after test run",
    )
    
    verbose: bool = Field(
        default=False,
        description="Enable verbose compliance tracking output",
    )
    
    # Filtering
    marker_patterns: list[str] = Field(
        default=["T*", "ASSURANCE*"],
        description="Glob patterns for markers to track (e.g., 'T*', 'ASSURANCE*')",
    )
    
    # CI/CD integration
    fail_below_threshold: Optional[float] = Field(
        default=None,
        description="Fail CI if compliance score drops below this percentage (0-100)",
    )
    
    @field_validator("fail_below_threshold")
    @classmethod
    def validate_threshold(cls, v):
        """Validate threshold is between 0 and 100 if set."""
        if v is not None and not (0 <= v <= 100):
            raise ValueError("fail_below_threshold must be between 0 and 100")
        return v
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "report_output": ".compliance_results.json",
                "generate_report": True,
                "verbose": False,
                "marker_patterns": ["T*", "ASSURANCE*"],
                "fail_below_threshold": 80.0,
            }
        }


class ComplianceReport(BaseModel):
    """Structure of a compliance report JSON file."""

    summary: dict = Field(description="Summary statistics")
    marker_results: dict = Field(description="Results per marker")
    test_results: dict = Field(description="Results per test")


def load_config_from_dict(data: dict) -> CompliancePluginConfig:
    """Load plugin configuration from dictionary."""
    return CompliancePluginConfig(**data)


def load_config_from_file(config_file: Path) -> CompliancePluginConfig:
    """Load plugin configuration from JSON file."""
    import json

    data = json.loads(config_file.read_text())
    return load_config_from_dict(data)
