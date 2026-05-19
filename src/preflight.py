"""Small preflight checks for script prerequisites."""

from __future__ import annotations

import logging
from pathlib import Path

from src.config import resolve_path


def require_existing_paths(paths: dict[str, str | Path], logger: logging.Logger, hint: str | None = None) -> None:
    """Raise a clear error when required input or prerequisite output paths are missing."""
    missing: list[str] = []
    for label, value in paths.items():
        path = resolve_path(value)
        if not path or not path.exists():
            missing.append(f"{label}: {path or value}")
    if missing:
        message = "Missing required files:\n" + "\n".join(f"- {item}" for item in missing)
        if hint:
            message += f"\n\nSuggested next step: {hint}"
        logger.error(message)
        raise FileNotFoundError(message)


def existing_paths(paths: dict[str, str | Path], logger: logging.Logger) -> dict[str, Path]:
    """Return only paths that exist, logging a warning for each missing optional path."""
    found: dict[str, Path] = {}
    for label, value in paths.items():
        path = resolve_path(value)
        if path and path.exists():
            found[label] = path
        else:
            logger.warning("Optional file missing; skipping %s: %s", label, path or value)
    return found

