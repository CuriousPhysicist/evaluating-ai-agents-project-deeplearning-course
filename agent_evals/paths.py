from __future__ import annotations

from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def resolve_root(root: Path | None = None) -> Path:
    """Return the supplied project root, or the repository root by default."""
    return (DEFAULT_ROOT if root is None else root).resolve()


def runtime_input_path(root: Path, category: str, filename: str) -> Path:
    """Resolve an input in the new layout, requiring manual migration of old files."""
    legacy = root / category / filename
    destination = root / "inputs" / category / filename
    if legacy.exists():
        raise RuntimeError(
            f"Legacy runtime input found at {legacy}. Compare it with {destination}, "
            "then move or back up the old file before continuing; see README.md."
        )
    return destination
