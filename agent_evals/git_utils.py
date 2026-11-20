"""Git utilities for capturing version and branch metadata.

Provides functions to retrieve git information for use in compliance tracking
and historical score recording. Supports both auto-detection from git and
explicit parameter passing.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_git_branch(explicit_branch: Optional[str] = None) -> str:
    """Get current git branch name, optionally from explicit parameter.

    Args:
        explicit_branch: If provided, return this directly (for testing/CI)

    Returns:
        Branch name (e.g., "main", "feat/historical-tracking")
        Returns "unknown" if git is unavailable or not in git repo

    Example:
        >>> branch = get_git_branch()
        >>> explicit = get_git_branch(explicit_branch="main")
        >>> explicit
        'main'
    """
    if explicit_branch:
        return explicit_branch

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        branch = result.stdout.strip()
        if branch:
            logger.debug(f"Detected git branch: {branch}")
            return branch
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.debug(f"Could not detect git branch: {e}")

    return "unknown"


def get_git_commit_hash(short: bool = False) -> str:
    """Get current git commit hash.

    Args:
        short: If True, return short hash (7 chars), else full hash

    Returns:
        Commit hash (or first 7 chars if short=True)
        Returns "unknown" if git is unavailable or not in git repo

    Example:
        >>> full_hash = get_git_commit_hash()
        >>> short_hash = get_git_commit_hash(short=True)
    """
    try:
        flag = "--short" if short else ""
        result = subprocess.run(
            ["git", "rev-parse", flag, "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        commit = result.stdout.strip()
        if commit:
            logger.debug(f"Detected git commit: {commit}")
            return commit
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.debug(f"Could not detect git commit: {e}")

    return "unknown"


def get_project_version(
    explicit_version: Optional[str] = None,
    version_file: Optional[Path] = None,
) -> str:
    """Get project version from pyproject.toml or explicit parameter.

    Args:
        explicit_version: If provided, return this directly (for testing/CI)
        version_file: Path to pyproject.toml or other version file
                     Default: looks for pyproject.toml in cwd and parents

    Returns:
        Version string (e.g., "0.1.0")
        Returns "unknown" if version cannot be determined

    Example:
        >>> version = get_project_version()
        >>> version
        '0.1.0'
        >>> explicit = get_project_version(explicit_version="1.2.3")
        >>> explicit
        '1.2.3'
    """
    if explicit_version:
        return explicit_version

    # Try to find and read pyproject.toml
    if version_file is None:
        # Search for pyproject.toml in cwd and parents
        current = Path.cwd()
        for _ in range(10):  # Limit search depth
            candidate = current / "pyproject.toml"
            if candidate.exists():
                version_file = candidate
                break
            parent = current.parent
            if parent == current:  # Reached root
                break
            current = parent

    if version_file and version_file.exists():
        try:
            # Simple parsing for version = "X.Y.Z" in pyproject.toml
            content = version_file.read_text()
            for line in content.split("\n"):
                if line.startswith("version"):
                    # Parse: version = "0.1.0"
                    if "=" in line and '"' in line:
                        version = line.split('"')[1]
                        logger.debug(f"Detected project version from {version_file}: {version}")
                        return version
        except Exception as e:
            logger.debug(f"Could not read version from {version_file}: {e}")

    logger.debug("Could not determine project version, using 'unknown'")
    return "unknown"


def get_baseline_version(
    explicit_baseline: Optional[str] = None,
) -> str:
    """Get baseline version for regression comparison.

    The baseline is the previous stable/released version for detecting regressions.
    Can be provided explicitly or derived from git tags.

    Args:
        explicit_baseline: If provided, return this directly (for testing/CI)

    Returns:
        Baseline version string
        Returns "unknown" if baseline cannot be determined

    Example:
        >>> baseline = get_baseline_version()
        >>> baseline
        '0.1.0'
        >>> explicit = get_baseline_version(explicit_baseline="0.0.9")
        >>> explicit
        '0.0.9'
    """
    if explicit_baseline:
        return explicit_baseline

    # Try to get latest git tag (simple approach)
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        baseline = result.stdout.strip()
        if baseline:
            logger.debug(f"Detected baseline version from git tag: {baseline}")
            return baseline
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: use current project version as baseline
    version = get_project_version()
    logger.debug(f"Using current version as baseline: {version}")
    return version


def build_version_identifier(
    explicit_version: Optional[str] = None,
    version_file: Optional[Path] = None,
) -> str:
    """Build a complete version identifier with semantic version and timestamp.

    Format: v<semver>-<date>-<time>
    Example: v0.1.0-20261120-143000

    Args:
        explicit_version: Explicit semantic version (e.g., "0.1.0")
        version_file: Path to version file for extraction

    Returns:
        Complete version identifier with timestamp

    Example:
        >>> vid = build_version_identifier()
        >>> vid.startswith("v0.1.0-")
        True
    """
    from datetime import datetime

    # Get semantic version
    sem_version = get_project_version(explicit_version, version_file)
    if not sem_version.startswith("v"):
        sem_version = f"v{sem_version}"

    # Add timestamp
    now = datetime.utcnow()
    timestamp = now.strftime("%Y%m%d-%H%M%S")

    version_id = f"{sem_version}-{timestamp}"
    logger.debug(f"Built version identifier: {version_id}")
    return version_id
