"""Compute basin and sub-basin morphometric parameters."""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
import geopandas as gpd
from pyogrio.errors import DataSourceError

from src.config import load_config_bundle, resolve_path
from src.logging_utils import setup_logging
from src.morphometry import (
    build_morphometric_table,
    elevation_stats_by_basin,
    slope_stats_by_basin,
    summarize_streams_by_basin,
)
from src.preflight import require_existing_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute morphometric parameters.")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    logger = setup_logging("07_compute_morphometric_parameters")
    configs = load_config_bundle(args.config_dir)
    data = configs["data"]
    morph = configs["morphometry"]
    processed = data["processed"]
    id_field = morph.get("basin_id_field", "subbasin_id")
    require_existing_paths(
        {
            "sub-basins": processed["subbasins_vector"],
            "streams": processed["streams_vector"],
            "corrected DEM": data["interim"]["corrected_dem"],
        },
        logger,
        "Run scripts 03, 05, and 06 first.",
    )

    basins = gpd.read_file(resolve_path(processed["subbasins_vector"]))
    if id_field not in basins.columns:
        basins[id_field] = range(1, len(basins) + 1)
    streams_path = resolve_path(processed["streams_vector"])
    try:
        streams = gpd.read_file(streams_path)
    except DataSourceError as exc:
        raise DataSourceError(
            f"Could not read stream network vector: {streams_path}. "
            "WhiteboxTools writes stream vectors as shapefiles, so rerun "
            "scripts/05_extract_stream_network.py after confirming "
            "config/data_paths.yml uses data/processed/vectors/stream_network.shp."
        ) from exc
    stream_summary = summarize_streams_by_basin(basins, streams, id_field)
    elev_summary = elevation_stats_by_basin(
        processed["subbasins_vector"],
        data["interim"]["corrected_dem"],
        id_field,
    )
    slope_path = resolve_path(f"{data['interim']['terrain_dir']}/slope_degrees.tif")
    slope_summary = (
        slope_stats_by_basin(processed["subbasins_vector"], slope_path, id_field)
        if slope_path.exists()
        else None
    )
    table = build_morphometric_table(basins, stream_summary, elev_summary, slope_summary, id_field)
    output = resolve_path(processed["subbasin_morphometry_csv"])
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)
    logger.info("Sub-basin morphometric table written: %s", output)

    basin_table = table.copy()
    numeric_cols = basin_table.select_dtypes(include="number").columns
    basin_summary = basin_table[numeric_cols].mean(numeric_only=True).to_frame().T
    basin_summary["basin_id"] = 1
    basin_output = resolve_path(processed["basin_morphometry_csv"])
    basin_output.parent.mkdir(parents=True, exist_ok=True)
    basin_summary.to_csv(basin_output, index=False)
    logger.info("Basin-level morphometric summary written: %s", basin_output)


if __name__ == "__main__":
    main()
