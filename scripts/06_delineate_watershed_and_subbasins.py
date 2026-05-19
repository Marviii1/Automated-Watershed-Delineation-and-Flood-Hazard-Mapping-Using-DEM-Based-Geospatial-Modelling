"""Delineate watershed and scaffold sub-basin outputs."""

from __future__ import annotations

import argparse
import shutil

import _bootstrap  # noqa: F401
from src.config import load_config_bundle, resolve_path
from src.hydrology import delineate_watershed
from src.logging_utils import setup_logging
from src.preflight import require_existing_paths
from src.raster_utils import rasterize_vectors, vectorize_class_raster


def main() -> None:
    parser = argparse.ArgumentParser(description="Delineate watershed and sub-basins.")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    logger = setup_logging("06_delineate_watershed_and_subbasins")
    configs = load_config_bundle(args.config_dir)
    data = configs["data"]
    hyd = configs["hydrology"]
    raw = data["raw"]
    interim = data["interim"]
    processed = data["processed"]
    require_existing_paths(
        {"flow direction": interim["flow_direction"], "outlet points": raw["outlet_points"]},
        logger,
        "Run scripts 01 and 04 first, and confirm outlet points in config/data_paths.yml.",
    )
    pour_points_raster = resolve_path(interim["watershed_raster"]).with_name("pour_points_raster.tif")
    rasterize_vectors(raw["outlet_points"], interim["flow_direction"], pour_points_raster, burn_value=1)

    watershed_raster = delineate_watershed(
        interim["flow_direction"],
        pour_points_raster,
        interim["watershed_raster"],
        hyd["whitebox"]["working_dir"],
        logger,
        esri_pointer=hyd["watershed"].get("esri_pointer", False),
    )
    if hyd["watershed"].get("vectorize_watershed", True):
        vectorize_class_raster(watershed_raster, processed["watershed_vector"], class_field="watershed_id")

    # Sub-basin delineation can be driven by junction-derived pour points or supplied pour points.
    # The default scaffold copies watershed polygons when separate sub-basin pour points are not configured.
    watershed_vector = resolve_path(processed["watershed_vector"])
    subbasins_vector = resolve_path(processed["subbasins_vector"])
    if watershed_vector.exists():
        subbasins_vector.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(watershed_vector, subbasins_vector)
        logger.warning("Sub-basin pour point extraction is project-specific; copied watershed as initial sub-basin layer.")
    logger.info("Watershed and sub-basin delineation completed.")


if __name__ == "__main__":
    main()
