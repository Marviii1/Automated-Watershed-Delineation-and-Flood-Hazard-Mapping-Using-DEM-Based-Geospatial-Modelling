"""Generate D8 flow direction and accumulation rasters."""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.config import load_config_bundle
from src.hydrology import flow_direction_and_accumulation
from src.logging_utils import setup_logging
from src.preflight import require_existing_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate flow direction and accumulation.")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    logger = setup_logging("04_generate_flow_direction_and_accumulation")
    configs = load_config_bundle(args.config_dir)
    data = configs["data"]["interim"]
    hyd = configs["hydrology"]
    require_existing_paths(
        {"hydrologically corrected DEM": data["corrected_dem"]},
        logger,
        "Run script 03_preprocess_dem.py first.",
    )
    flow_direction_and_accumulation(
        data["corrected_dem"],
        data["flow_direction"],
        data["flow_accumulation"],
        hyd["whitebox"]["working_dir"],
        logger,
    )
    logger.info("Flow modelling completed.")


if __name__ == "__main__":
    main()
