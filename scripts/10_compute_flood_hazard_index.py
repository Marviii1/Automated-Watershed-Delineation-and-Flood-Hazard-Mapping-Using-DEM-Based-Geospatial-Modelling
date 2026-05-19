"""Compute continuous and classified Flood Hazard Index outputs."""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.config import load_config_bundle, resolve_path
from src.flood_hazard import classify_hazard_index, summarize_hazard_area, weighted_overlay, zonal_hazard_summary
from src.logging_utils import setup_logging
from src.raster_utils import vectorize_class_raster


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute flood hazard index.")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    logger = setup_logging("10_compute_flood_hazard_index")
    configs = load_config_bundle(args.config_dir)
    flood = configs["flood"]
    data = configs["data"]
    processed = data["processed"]

    factor_paths = {}
    weights = {}
    for name, spec in flood["factors"].items():
        path = resolve_path(spec["reclassified_output"])
        if spec.get("enabled", False) and path.exists():
            factor_paths[name] = path
            weights[name] = spec.get("weight", 0)
        elif spec.get("enabled", False):
            logger.warning("Reclassified factor missing; run script 09 first or disable factor: %s", name)
    if not factor_paths:
        message = (
            "No enabled reclassified flood factors were found. "
            "Run script 09_prepare_flood_hazard_factors.py first or update config/flood_hazard_config.yml."
        )
        logger.error(message)
        raise FileNotFoundError(message)

    weighted_overlay(factor_paths, weights, processed["fhi_continuous"])
    classify_hazard_index(
        processed["fhi_continuous"],
        processed["fhi_classified"],
        flood["hazard_classification_breaks"],
    )
    summarize_hazard_area(processed["fhi_classified"], processed["hazard_area_summary_csv"])
    subbasins = resolve_path(processed["subbasins_vector"])
    if subbasins.exists():
        zonal_hazard_summary(
            subbasins,
            processed["fhi_continuous"],
            processed["fhi_classified"],
            processed["hazard_subbasin_summary_csv"],
        )
    else:
        logger.warning("Sub-basin layer missing; skipping sub-basin hazard summary.")
    vectorize_class_raster(processed["fhi_classified"], processed["fhi_zones_vector"], class_field="hazard_cls")
    logger.info("Flood hazard index processing completed.")


if __name__ == "__main__":
    main()
