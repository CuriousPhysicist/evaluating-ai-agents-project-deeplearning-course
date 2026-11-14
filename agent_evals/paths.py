from __future__ import annotations

from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def resolve_root(root: Path | None = None) -> Path:
    """Return the supplied project root, or the repository root by default."""
    return (DEFAULT_ROOT if root is None else root).resolve()
