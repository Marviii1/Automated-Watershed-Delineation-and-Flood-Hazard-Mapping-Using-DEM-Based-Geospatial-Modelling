"""Align and reclassify flood hazard conditioning factors."""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.config import load_config_bundle, resolve_path
from src.flood_hazard import prepare_factor_raster
from src.logging_utils import setup_logging
from src.preflight import require_existing_paths
from src.terrain_indices import distance_to_stream_raster, stream_power_index, topographic_wetness_index


def maybe_derive_factor(name: str, spec: dict, data: dict, logger) -> None:
    """Create optional derived terrain factors when enabled and missing."""
    source = resolve_path(spec["source"])
    if source.exists():
        return
    interim = data["interim"]
    if name == "distance_to_stream":
        stream_raster = resolve_path(interim["stream_raster"])
        if stream_raster.exists():
            distance_to_stream_raster(stream_raster, source)
            logger.info("Derived distance-to-stream raster: %s", source)
    elif name == "twi":
        flow_acc = resolve_path(interim["flow_accumulation"])
        slope = resolve_path(f"{interim['terrain_dir']}/slope_degrees.tif")
        if flow_acc.exists() and slope.exists():
            topographic_wetness_index(flow_acc, slope, source)
            logger.info("Derived TWI raster: %s", source)
    elif name == "spi":
        flow_acc = resolve_path(interim["flow_accumulation"])
        slope = resolve_path(f"{interim['terrain_dir']}/slope_degrees.tif")
        if flow_acc.exists() and slope.exists():
            stream_power_index(flow_acc, slope, source)
            logger.info("Derived SPI raster: %s", source)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare flood hazard factor rasters.")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    logger = setup_logging("09_prepare_flood_hazard_factors")
    configs = load_config_bundle(args.config_dir)
    data = configs["data"]
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
        maybe_derive_factor(name, spec, data, logger)
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
