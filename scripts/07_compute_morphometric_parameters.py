"""Compute basin and sub-basin morphometric parameters."""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
import geopandas as gpd

from src.config import load_config_bundle, resolve_path
from src.logging_utils import setup_logging
from src.morphometry import build_morphometric_table, elevation_stats_by_basin, summarize_streams_by_basin
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
    streams = gpd.read_file(resolve_path(processed["streams_vector"]))
    stream_summary = summarize_streams_by_basin(basins, streams, id_field)
    elev_summary = elevation_stats_by_basin(
        processed["subbasins_vector"],
        data["interim"]["corrected_dem"],
        id_field,
    )
    table = build_morphometric_table(basins, stream_summary, elev_summary, id_field)
    output = resolve_path(processed["subbasin_morphometry_csv"])
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)
    logger.info("Sub-basin morphometric table written: %s", output)


if __name__ == "__main__":
    main()
