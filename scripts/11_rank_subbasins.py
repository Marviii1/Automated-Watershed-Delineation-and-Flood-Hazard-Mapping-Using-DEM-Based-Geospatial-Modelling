"""Rank sub-basins using hazard and morphometric indicators."""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.config import load_config_bundle
from src.logging_utils import setup_logging
from src.preflight import require_existing_paths
from src.ranking import rank_subbasins


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank sub-basins by flood priority.")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    logger = setup_logging("11_rank_subbasins")
    configs = load_config_bundle(args.config_dir)
    processed = configs["data"]["processed"]
    require_existing_paths(
        {
            "sub-basins": processed["subbasins_vector"],
            "sub-basin morphometry": processed["subbasin_morphometry_csv"],
            "sub-basin hazard summary": processed["hazard_subbasin_summary_csv"],
        },
        logger,
        "Run scripts 07_compute_morphometric_parameters.py and 10_compute_flood_hazard_index.py first.",
    )
    rank_subbasins(
        processed["subbasins_vector"],
        processed["subbasin_morphometry_csv"],
        processed["hazard_subbasin_summary_csv"],
        processed["subbasin_priority_csv"],
        processed["subbasin_priority_gpkg"],
    )
    logger.info("Sub-basin ranking completed.")


if __name__ == "__main__":
    main()
