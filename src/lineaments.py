"""Lineament and drainage integration utilities."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from src.config import resolve_path
from src.raster_utils import rasterize_vectors, read_raster_array, write_single_band_raster


def lineament_length_stats(lineaments_path: str | Path, output_csv: str | Path) -> Path:
    """Calculate lineament length and orientation summary from imported lineament vectors."""
    lineaments_path = resolve_path(lineaments_path)
    output_csv = resolve_path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    gdf = gpd.read_file(lineaments_path)
    gdf["length_km"] = gdf.geometry.length / 1000.0
    gdf["orientation_deg"] = gdf.geometry.apply(estimate_line_orientation)
    summary = pd.DataFrame(
        {
            "metric": ["feature_count", "total_length_km", "mean_length_km"],
            "value": [len(gdf), gdf["length_km"].sum(), gdf["length_km"].mean()],
        }
    )
    orientation = gdf["orientation_deg"].describe().reset_index()
    orientation.columns = ["metric", "value"]
    pd.concat([summary, orientation], ignore_index=True).to_csv(output_csv, index=False)
    return output_csv


def estimate_line_orientation(geometry) -> float:
    """Estimate line orientation in degrees from first to last coordinate."""
    if geometry is None or geometry.is_empty:
        return np.nan
    line = max(geometry.geoms, key=lambda g: g.length) if geometry.geom_type == "MultiLineString" else geometry
    coords = list(line.coords)
    if len(coords) < 2:
        return np.nan
    x1, y1 = coords[0]
    x2, y2 = coords[-1]
    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
    return float(angle % 180)


def calculate_lineament_density(
    lineaments_path: str | Path,
    reference_raster: str | Path,
    output_raster: str | Path,
    kernel_pixels: int = 15,
) -> Path:
    """Create a simple local lineament density raster from lineament vectors.

    This is an interpretation layer for structurally influenced drainage zones,
    not proof of groundwater recharge or hydraulic connectivity.
    """
    temp_raster = resolve_path(output_raster).with_name("_lineaments_binary_tmp.tif")
    rasterize_vectors(lineaments_path, reference_raster, temp_raster, burn_value=1)
    binary, profile = read_raster_array(temp_raster, masked=False)
    try:
        from scipy.ndimage import uniform_filter
        density = uniform_filter(binary.astype("float32"), size=kernel_pixels) * 100.0
    except Exception:
        density = binary.astype("float32")
    output = write_single_band_raster(output_raster, density, profile, dtype="float32", nodata=0)
    temp_raster.unlink(missing_ok=True)
    return output


def drainage_lineament_intersections(
    streams_path: str | Path,
    lineaments_path: str | Path,
    output_path: str | Path,
) -> Path:
    """Create point features where streams intersect imported lineaments."""
    streams = gpd.read_file(resolve_path(streams_path))
    lineaments = gpd.read_file(resolve_path(lineaments_path))
    output_path = resolve_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if streams.crs and lineaments.crs and streams.crs != lineaments.crs:
        lineaments = lineaments.to_crs(streams.crs)
    intersections = gpd.overlay(streams, lineaments, how="intersection")
    intersections.to_file(output_path, driver="GPKG")
    return output_path

