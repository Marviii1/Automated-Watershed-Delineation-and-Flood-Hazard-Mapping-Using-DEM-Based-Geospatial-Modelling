"""Export lightweight dashboard assets for Streamlit Cloud.

This creates PNG raster overlays plus JSON bounds metadata in
data/processed/dashboard_layers/ and converts uploadable vector layers to
GeoPackage where needed. It does not replace the analytical raster outputs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib import colormaps
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds

from src.config import load_config_bundle, resolve_path
from src.logging_utils import setup_logging


def raster_overlay_png(
    raster_path: str | Path,
    output_dir: str | Path,
    cmap: str,
    max_size: int = 1200,
) -> Path | None:
    """Write a transparent PNG overlay and JSON bounds for a raster."""
    raster_path = resolve_path(raster_path)
    if not raster_path or not raster_path.exists():
        return None
    output_dir = resolve_path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / f"{raster_path.stem}.png"
    json_path = output_dir / f"{raster_path.stem}.json"

    with rasterio.open(raster_path) as src:
        scale = max(src.width / max_size, src.height / max_size, 1)
        width = max(1, int(src.width / scale))
        height = max(1, int(src.height / scale))
        data = src.read(1, out_shape=(height, width), resampling=Resampling.nearest)
        bounds = transform_bounds(src.crs, "EPSG:4326", *src.bounds, densify_pts=21)
        nodata = src.nodata

    arr = data.astype("float32")
    mask = ~np.isfinite(arr)
    if nodata is not None:
        mask |= arr == nodata
    if "stream" in raster_path.stem:
        mask |= arr <= 0
    if "classified" in raster_path.stem:
        mask |= ~np.isin(arr, [1, 2, 3, 4, 5])

    valid = arr[~mask]
    if valid.size == 0:
        return None
    low, high = np.nanpercentile(valid, [2, 98])
    if high <= low:
        low, high = float(np.nanmin(valid)), float(np.nanmax(valid) or 1)
    normed = np.clip((arr - low) / (high - low if high != low else 1), 0, 1)
    rgba = colormaps.get_cmap(cmap)(normed)
    rgba[..., 3] = np.where(mask, 0, 0.72)
    plt.imsave(png_path, (rgba * 255).astype("uint8"))

    south, west, north, east = bounds[1], bounds[0], bounds[3], bounds[2]
    json_path.write_text(
        json.dumps({"bounds": [[south, west], [north, east]], "source": str(raster_path)}, indent=2),
        encoding="utf-8",
    )
    return png_path


def vector_to_gpkg(input_path: str | Path, output_path: str | Path, crs: str) -> Path | None:
    """Convert a vector layer to GeoPackage for Streamlit Cloud upload."""
    input_path = resolve_path(input_path)
    output_path = resolve_path(output_path)
    if not input_path or not input_path.exists():
        return None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf = gpd.read_file(input_path)
    if gdf.crs is None:
        gdf = gdf.set_crs(crs, allow_override=True)
    gdf.to_file(output_path, driver="GPKG")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Streamlit Cloud dashboard assets.")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    logger = setup_logging("14_export_streamlit_cloud_assets")
    configs = load_config_bundle(args.config_dir)
    data = configs["data"]
    project_crs = configs["project"]["default_crs_projected"]
    interim = data["interim"]
    processed = data["processed"]
    output_dir = processed["dashboard_layers_dir"]

    rasters = {
        interim["corrected_dem"]: "terrain",
        interim["flow_accumulation"]: "viridis",
        interim["stream_raster"]: "Blues",
        interim["strahler_order"]: "plasma",
        f"{interim['terrain_dir']}/slope_degrees.tif": "magma",
        processed["fhi_continuous"]: "inferno",
        processed["fhi_classified"]: "RdYlBu_r",
        "data/processed/rasters/factor_slope_score.tif": "magma",
        "data/processed/rasters/factor_elevation_score.tif": "terrain",
        "data/processed/rasters/factor_flow_accumulation_score.tif": "viridis",
        "data/processed/rasters/factor_lulc_score.tif": "YlGn",
    }
    for raster, cmap in rasters.items():
        output = raster_overlay_png(raster, output_dir, cmap)
        if output:
            logger.info("Wrote dashboard PNG overlay: %s", output)

    stream_path = resolve_path(processed["streams_vector"])
    if stream_path and stream_path.suffix.lower() == ".shp":
        output = vector_to_gpkg(stream_path, stream_path.with_suffix(".gpkg"), project_crs)
        if output:
            logger.info("Wrote stream network GeoPackage: %s", output)

    boundary = vector_to_gpkg(
        interim["study_area_projected"],
        "data/processed/vectors/ilaje_lga_boundary_projected.gpkg",
        project_crs,
    )
    if boundary:
        logger.info("Wrote boundary GeoPackage for dashboard upload: %s", boundary)


if __name__ == "__main__":
    main()
