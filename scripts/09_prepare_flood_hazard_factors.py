"""Align and reclassify flood hazard conditioning factors."""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.config import load_config_bundle, resolve_path
from src.flood_hazard import prepare_factor_raster
from src.logging_utils import setup_logging
from src.preflight import require_existing_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare flood hazard factor rasters.")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    logger = setup_logging("09_prepare_flood_hazard_factors")
    configs = load_config_bundle(args.config_dir)
    flood = configs["flood"]
    reference = flood["reference_raster"]
    require_existing_paths(
        {"flood factor reference raster": reference},
        logger,
        "Run script 03_preprocess_dem.py first or update flood_hazard_config.yml.",
    )

    for name, spec in flood["factors"].items():
        if not spec.get("enabled", False):
            logger.info("Skipping disabled factor: %s", name)
            continue
        source = resolve_path(spec["source"])
        if not source.exists():
            logger.warning("Enabled factor source missing; skipping %s: %s", name, source)
            continue
        prepare_factor_raster(
            name,
            source,
            reference,
            spec["reclassified_output"],
            spec["rules"],
        )
        logger.info("Prepared flood factor: %s", name)
    logger.info("Flood factor preparation completed.")


if __name__ == "__main__":
    main()
