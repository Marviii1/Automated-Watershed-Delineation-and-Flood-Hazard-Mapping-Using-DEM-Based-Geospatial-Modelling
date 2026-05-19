"""Hydrologically correct DEM and generate terrain derivatives."""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.config import load_config_bundle
from src.hydrology import breach_or_fill_dem, terrain_derivatives
from src.logging_utils import setup_logging
from src.preflight import require_existing_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Hydrologically preprocess DEM.")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    logger = setup_logging("03_preprocess_dem")
    configs = load_config_bundle(args.config_dir)
    hyd = configs["hydrology"]
    data = configs["data"]
    require_existing_paths(
        {"projected DEM": data["interim"]["projected_dem"]},
        logger,
        "Run script 02_prepare_study_area_and_dem.py first.",
    )

    corrected = breach_or_fill_dem(
        data["interim"]["projected_dem"],
        data["interim"]["corrected_dem"],
        hyd["dem_preprocessing_method"],
        hyd["whitebox"]["working_dir"],
        logger,
    )
    terrain_derivatives(
        corrected,
        data["interim"]["terrain_dir"],
        hyd["whitebox"]["working_dir"],
        logger,
        hyd["terrain_derivatives"]["hillshade_azimuth"],
        hyd["terrain_derivatives"]["hillshade_altitude"],
        hyd["terrain_derivatives"].get("multi_hillshade_azimuths", []),
    )
    logger.info("DEM preprocessing completed.")


if __name__ == "__main__":
    main()
