"""Vector processing helpers."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from src.config import resolve_path


def read_vector(path: str | Path) -> gpd.GeoDataFrame:
    """Read a vector layer from disk."""
    return gpd.read_file(resolve_path(path))


def reproject_vector(input_path: str | Path, output_path: str | Path, dst_crs: str) -> Path:
    """Reproject a vector layer and write it to disk."""
    output_path = resolve_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf = gpd.read_file(resolve_path(input_path))
    gdf.to_crs(dst_crs).to_file(output_path, driver="GPKG")
    return output_path


def add_geometry_metrics(
    gdf: gpd.GeoDataFrame,
    id_field: str = "basin_id",
    area_field: str = "area_km2",
    perimeter_field: str = "perim_km",
) -> gpd.GeoDataFrame:
    """Add projected area and perimeter metrics to polygon features."""
    result = gdf.copy()
    if id_field not in result.columns:
        result[id_field] = range(1, len(result) + 1)
    result[area_field] = result.geometry.area / 1_000_000.0
    result[perimeter_field] = result.geometry.length / 1_000.0
    return result


def write_gpkg(gdf: gpd.GeoDataFrame, path: str | Path, layer: str | None = None) -> Path:
    """Write a GeoDataFrame as GeoPackage."""
    path = resolve_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {"driver": "GPKG"}
    if layer:
        kwargs["layer"] = layer
    gdf.to_file(path, **kwargs)
    return path

