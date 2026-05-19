"""Run semi-automated lineament-drainage integration when lineaments are available."""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.config import load_config_bundle, resolve_path
from src.lineaments import calculate_lineament_density, drainage_lineament_intersections, lineament_length_stats
from src.logging_utils import setup_logging
from src.preflight import require_existing_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze lineament-drainage relationships.")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    logger = setup_logging("08_lineament_drainage_analysis")
    configs = load_config_bundle(args.config_dir)
    data = configs["data"]
    lineaments = resolve_path(data["raw"].get("lineaments"))
    if not lineaments or not lineaments.exists():
        logger.warning("No lineament vector found. Skipping lineament-drainage analysis.")
        return
    require_existing_paths(
        {"corrected DEM": data["interim"]["corrected_dem"]},
        logger,
        "Run script 03_preprocess_dem.py first before calculating lineament density.",
    )

    lineament_length_stats(lineaments, data["processed"]["lineament_stats_csv"])
    calculate_lineament_density(
        lineaments,
        data["interim"]["corrected_dem"],
        data["processed"]["lineament_density_raster"],
    )
    streams = resolve_path(data["processed"]["streams_vector"])
    if streams.exists():
        drainage_lineament_intersections(
            streams,
            lineaments,
            data["processed"]["drainage_lineament_intersections"],
        )
    logger.info("Lineament-drainage analysis completed. Interpret as structurally influenced drainage zones, not direct proof of recharge.")


if __name__ == "__main__":
    main()
