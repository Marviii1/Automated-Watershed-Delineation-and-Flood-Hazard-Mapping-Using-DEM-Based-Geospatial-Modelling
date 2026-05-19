"""Configuration loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def project_root() -> Path:
    """Return the repository root based on this file location."""
    return Path(__file__).resolve().parents[1]


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file and return an empty dictionary for empty files."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_config_bundle(config_dir: str | Path = "config") -> dict[str, dict[str, Any]]:
    """Load all standard project configuration files."""
    root = project_root()
    config_dir = (root / config_dir).resolve() if not Path(config_dir).is_absolute() else Path(config_dir)
    names = {
        "project": "project_config.yml",
        "data": "data_paths.yml",
        "hydrology": "hydrology_config.yml",
        "morphometry": "morphometry_config.yml",
        "flood": "flood_hazard_config.yml",
        "dashboard": "dashboard_config.yml",
    }
    return {key: load_yaml(config_dir / filename) for key, filename in names.items()}


def resolve_path(path_value: str | Path | None, base_dir: str | Path | None = None) -> Path | None:
    """Resolve a path relative to the repository root unless it is already absolute."""
    if path_value in (None, ""):
        return None
    path = Path(path_value)
    if path.is_absolute():
        return path
    return ((Path(base_dir) if base_dir else project_root()) / path).resolve()


def ensure_directories(paths: list[str | Path | None]) -> None:
    """Create configured output directories."""
    for path in paths:
        resolved = resolve_path(path)
        if resolved:
            resolved.mkdir(parents=True, exist_ok=True)

