"""Validate configured project inputs."""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.config import load_config_bundle
from src.logging_utils import setup_logging
from src.study_area import validate_study_area_boundary
from src.validation import validate_optional_paths, validate_required_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate HydroMorpho project input paths.")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    logger = setup_logging("01_validate_project_inputs")
    configs = load_config_bundle(args.config_dir)
    raw = configs["data"]["raw"]
    required = {
        "study_area_boundary": raw["study_area_boundary"],
        "dem": raw["dem"],
    }
    optional = {key: raw.get(key) for key in raw if key not in required}
    validate_required_paths(required, logger)
    validate_study_area_boundary(raw["study_area_boundary"], logger)
    validate_optional_paths(optional, logger)
    logger.info("Input validation completed.")


if __name__ == "__main__":
    main()
