"""Generate static maps, figures, and charts from processed outputs."""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.config import load_config_bundle, resolve_path
from src.logging_utils import setup_logging
from src.visualization import bar_chart, raster_preview, vector_map


def maybe(callable_obj, logger, *args, **kwargs):
    """Run a visualization call only when its main input exists."""
    first_path = resolve_path(args[0])
    if first_path.exists():
        return callable_obj(*args, **kwargs)
    logger.warning("Skipping missing visualization input: %s", first_path)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate maps and charts.")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    logger = setup_logging("12_generate_maps_charts_and_summary_outputs")
    configs = load_config_bundle(args.config_dir)
    data = configs["data"]
    interim = data["interim"]
    processed = data["processed"]
    outputs = data["outputs"]

    maybe(raster_preview, logger, interim["corrected_dem"], f"{outputs['figures_dir']}/dem_preview.png", "Corrected DEM", cmap="terrain")
    maybe(raster_preview, logger, f"{interim['terrain_dir']}/slope_degrees.tif", f"{outputs['figures_dir']}/slope_preview.png", "Slope", cmap="magma")
    maybe(raster_preview, logger, interim["flow_accumulation"], f"{outputs['figures_dir']}/flow_accumulation_preview.png", "Flow Accumulation", cmap="viridis")
    maybe(vector_map, logger, processed["streams_vector"], f"{outputs['maps_dir']}/stream_network.png", "Stream Network")
    maybe(vector_map, logger, processed["subbasins_vector"], f"{outputs['maps_dir']}/subbasins.png", "Sub-Basins")
    maybe(raster_preview, logger, processed["fhi_classified"], f"{outputs['maps_dir']}/flood_hazard_index.png", "Flood Hazard Index", cmap="RdYlBu_r")
    maybe(vector_map, logger, processed["subbasin_priority_gpkg"], f"{outputs['maps_dir']}/subbasin_priority.png", "Sub-Basin Priority", column="priority_class")
    maybe(bar_chart, logger, processed["hazard_area_summary_csv"], "hazard_label", "area_km2", f"{outputs['charts_dir']}/hazard_area_bar.png", "Hazard Class Area")
    logger.info("Map and chart generation completed.")


if __name__ == "__main__":
    main()
