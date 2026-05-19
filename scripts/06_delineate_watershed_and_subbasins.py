"""Delineate watershed and scaffold sub-basin outputs."""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
import geopandas as gpd

from src.config import load_config_bundle, resolve_path
from src.hydrology import delineate_watershed, snap_pour_points
from src.logging_utils import setup_logging
from src.preflight import require_existing_paths
from src.raster_utils import rasterize_vectors, vectorize_class_raster


def write_boundary_fallback(boundary_path, watershed_path, subbasins_path, logger) -> None:
    """Use the configured study-area polygon as initial watershed and sub-basin layers."""
    boundary_path = resolve_path(boundary_path)
    watershed_path = resolve_path(watershed_path)
    subbasins_path = resolve_path(subbasins_path)
    watershed_path.parent.mkdir(parents=True, exist_ok=True)
    subbasins_path.parent.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_file(boundary_path)
    if "watershed_id" not in gdf.columns:
        gdf["watershed_id"] = range(1, len(gdf) + 1)
    if "subbasin_id" not in gdf.columns:
        gdf["subbasin_id"] = gdf["watershed_id"]
    gdf.to_file(watershed_path, driver="GPKG", layer="watershed")
    gdf.to_file(subbasins_path, driver="GPKG", layer="subbasins")
    logger.warning(
        "Outlet-based watershed raster was not created. Used study-area boundary as "
        "initial watershed/sub-basin layer: %s",
        subbasins_path,
    )


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
        {"flow direction": interim["flow_direction"]},
        logger,
        "Run script 04_generate_flow_direction_and_accumulation.py first.",
    )
    outlet_points = resolve_path(raw.get("outlet_points"))
    if not outlet_points or not outlet_points.exists():
        write_boundary_fallback(
            interim.get("study_area_projected", raw["study_area_boundary"]),
            processed["watershed_vector"],
            processed["subbasins_vector"],
            logger,
        )
        logger.info("No outlet points found; created study-area watershed/sub-basin fallback.")
        return

    pour_points_raster = resolve_path(interim["watershed_raster"]).with_name("pour_points_raster.tif")
    rasterize_vectors(outlet_points, interim["flow_direction"], pour_points_raster, burn_value=1)
    pour_points_for_watershed = pour_points_raster
    if hyd.get("snap_pour_points", False):
        require_existing_paths(
            {"flow accumulation": interim["flow_accumulation"]},
            logger,
            "Run script 04_generate_flow_direction_and_accumulation.py before snapping pour points.",
        )
        pour_points_for_watershed = snap_pour_points(
            pour_points_raster,
            interim["flow_accumulation"],
            pour_points_raster.with_name("pour_points_snapped.tif"),
            hyd.get("snap_distance", 150),
            hyd["whitebox"]["working_dir"],
            logger,
        )
        if not resolve_path(pour_points_for_watershed).exists():
            logger.warning(
                "Snapped pour point raster was not created. Falling back to unsnapped pour points."
            )
            pour_points_for_watershed = pour_points_raster

    watershed_raster = delineate_watershed(
        interim["flow_direction"],
        pour_points_for_watershed,
        interim["watershed_raster"],
        hyd["whitebox"]["working_dir"],
        logger,
        esri_pointer=hyd["watershed"].get("esri_pointer", False),
    )
    watershed_raster_path = resolve_path(watershed_raster)
    if watershed_raster_path.exists() and hyd["watershed"].get("vectorize_watershed", True):
        vectorize_class_raster(watershed_raster, processed["watershed_vector"], class_field="watershed_id")
    elif not watershed_raster_path.exists():
        write_boundary_fallback(
            interim.get("study_area_projected", raw["study_area_boundary"]),
            processed["watershed_vector"],
            processed["subbasins_vector"],
            logger,
        )
        logger.info("Watershed and sub-basin delineation completed with study-area fallback.")
        return

    # Sub-basin delineation can be driven by junction-derived pour points or supplied pour points.
    # The default scaffold copies watershed polygons when separate sub-basin pour points are not configured.
    watershed_vector = resolve_path(processed["watershed_vector"])
    subbasins_vector = resolve_path(processed["subbasins_vector"])
    if watershed_vector.exists():
        watershed_gdf = gpd.read_file(watershed_vector)
        if "subbasin_id" not in watershed_gdf.columns:
            watershed_gdf["subbasin_id"] = watershed_gdf.get(
                "watershed_id",
                range(1, len(watershed_gdf) + 1),
            )
        subbasins_vector.parent.mkdir(parents=True, exist_ok=True)
        watershed_gdf.to_file(subbasins_vector, driver="GPKG", layer="subbasins")
        logger.warning("Sub-basin pour point extraction is project-specific; copied watershed as initial sub-basin layer.")
    logger.info("Watershed and sub-basin delineation completed.")


if __name__ == "__main__":
    main()
