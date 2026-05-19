"""Input validation helpers."""

from __future__ import annotations

import logging
from pathlib import Path

from src.config import resolve_path


def path_exists(path_value: str | Path | None) -> bool:
    """Return True when a configured path is present and exists."""
    path = resolve_path(path_value)
    return bool(path and path.exists())


def validate_required_paths(paths: dict[str, str], logger: logging.Logger) -> list[Path]:
    """Validate required paths and raise one useful error listing missing inputs."""
    missing: list[str] = []
    resolved: list[Path] = []
    for label, value in paths.items():
        path = resolve_path(value)
        if not path or not path.exists():
            missing.append(f"{label}: {value}")
        else:
            resolved.append(path)
            logger.info("Found required input: %s -> %s", label, path)
    if missing:
        message = "Missing required input files:\n" + "\n".join(f"- {item}" for item in missing)
        raise FileNotFoundError(message)
    return resolved


def validate_optional_paths(paths: dict[str, str | None], logger: logging.Logger) -> dict[str, Path]:
    """Return existing optional paths and log warnings for absent optional inputs."""
    existing: dict[str, Path] = {}
    for label, value in paths.items():
        path = resolve_path(value)
        if path and path.exists():
            existing[label] = path
            logger.info("Found optional input: %s -> %s", label, path)
        else:
            logger.warning("Optional input not found or not configured: %s", label)
    return existing

