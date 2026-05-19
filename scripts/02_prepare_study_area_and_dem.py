"""Clip and reproject DEM for the configured study area."""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.config import load_config_bundle
from src.logging_utils import setup_logging
from src.preflight import require_existing_paths
from src.raster_utils import clip_raster_to_vector, reproject_raster


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare study area DEM.")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    logger = setup_logging("02_prepare_study_area_and_dem")
    configs = load_config_bundle(args.config_dir)
    raw = configs["data"]["raw"]
    interim = configs["data"]["interim"]
    project = configs["project"]
    require_existing_paths(
        {"DEM": raw["dem"], "study area boundary": raw["study_area_boundary"]},
        logger,
        "Run script 01_validate_project_inputs.py and update config/data_paths.yml.",
    )

    clipped = clip_raster_to_vector(raw["dem"], raw["study_area_boundary"], interim["clipped_dem"], logger)
    reproject_raster(clipped, interim["projected_dem"], project["default_crs_projected"], logger)
    logger.info("Study area DEM preparation completed.")


if __name__ == "__main__":
    main()
