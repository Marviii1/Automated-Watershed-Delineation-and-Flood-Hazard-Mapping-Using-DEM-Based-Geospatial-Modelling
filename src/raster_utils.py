"""Raster processing helpers built around rasterio and WhiteboxTools-compatible files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize, shapes
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject
from shapely.geometry import shape

from src.config import resolve_path
from src.constants import DEFAULT_NODATA


def clip_raster_to_vector(
    raster_path: str | Path,
    vector_path: str | Path,
    output_path: str | Path,
    logger: logging.Logger,
) -> Path:
    """Clip a raster to a vector boundary."""
    raster_path = resolve_path(raster_path)
    vector_path = resolve_path(vector_path)
    output_path = resolve_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    boundary = gpd.read_file(vector_path)
    with rasterio.open(raster_path) as src:
        if boundary.crs and src.crs and boundary.crs != src.crs:
            boundary = boundary.to_crs(src.crs)
        geometries = [geom for geom in boundary.geometry if geom is not None]
        data, transform = mask(src, geometries, crop=True)
        profile = src.profile.copy()
        profile.update(height=data.shape[1], width=data.shape[2], transform=transform)
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(data)
    logger.info("Clipped raster written: %s", output_path)
    return output_path


def reproject_raster(
    input_path: str | Path,
    output_path: str | Path,
    dst_crs: str,
    logger: logging.Logger,
    resampling: Resampling = Resampling.bilinear,
) -> Path:
    """Reproject a raster to a target CRS."""
    input_path = resolve_path(input_path)
    output_path = resolve_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(input_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )
        profile = src.profile.copy()
        profile.update(crs=dst_crs, transform=transform, width=width, height=height)
        with rasterio.open(output_path, "w", **profile) as dst:
            for band in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, band),
                    destination=rasterio.band(dst, band),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=resampling,
                )
    logger.info("Reprojected raster written: %s", output_path)
    return output_path


def align_raster_to_reference(
    input_path: str | Path,
    reference_path: str | Path,
    output_path: str | Path,
    logger: logging.Logger,
    resampling: Resampling = Resampling.nearest,
) -> Path:
    """Align an input raster to the transform, CRS, dimensions, and extent of a reference raster."""
    input_path = resolve_path(input_path)
    reference_path = resolve_path(reference_path)
    output_path = resolve_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(reference_path) as ref, rasterio.open(input_path) as src:
        profile = ref.profile.copy()
        profile.update(dtype=src.dtypes[0], count=src.count, nodata=src.nodata)
        with rasterio.open(output_path, "w", **profile) as dst:
            for band in range(1, src.count + 1):
                reproject(
                    rasterio.band(src, band),
                    rasterio.band(dst, band),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=ref.transform,
                    dst_crs=ref.crs,
                    resampling=resampling,
                )
    logger.info("Aligned raster written: %s", output_path)
    return output_path


def read_raster_array(path: str | Path, masked: bool = True) -> tuple[np.ndarray, dict]:
    """Read the first raster band and profile."""
    path = resolve_path(path)
    with rasterio.open(path) as src:
        return src.read(1, masked=masked), src.profile.copy()


def write_single_band_raster(
    output_path: str | Path,
    array: np.ndarray,
    profile: dict,
    dtype: str | None = None,
    nodata: float | int | None = DEFAULT_NODATA,
) -> Path:
    """Write a single-band raster while preserving georeferencing from a source profile."""
    output_path = resolve_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    profile = profile.copy()
    profile.update(count=1, dtype=dtype or str(array.dtype), nodata=nodata, compress="deflate")
    data = np.ma.filled(array, nodata) if np.ma.isMaskedArray(array) else array
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(data.astype(profile["dtype"]), 1)
    return output_path


def reclassify_array(array: np.ndarray, rules: list[dict], nodata: float | int | None = None) -> np.ndarray:
    """Reclassify a continuous or categorical array using ordered YAML rules."""
    result = np.full(array.shape, DEFAULT_NODATA, dtype="float32")
    data = np.ma.filled(array, np.nan) if np.ma.isMaskedArray(array) else array.astype("float32")

    for rule in rules:
        score = float(rule["score"])
        if "values" in rule:
            mask_rule = np.isin(data, rule["values"])
        else:
            low = rule.get("min", -np.inf)
            high = rule.get("max", np.inf)
            include_high = rule.get("include_max", True)
            mask_rule = (data >= low) & (data <= high if include_high else data < high)
        result[mask_rule] = score

    if nodata is not None:
        result[data == nodata] = DEFAULT_NODATA
    result[np.isnan(data)] = DEFAULT_NODATA
    return result


def rasterize_vectors(
    vector_path: str | Path,
    reference_raster: str | Path,
    output_path: str | Path,
    value_field: str | None = None,
    burn_value: int = 1,
) -> Path:
    """Rasterize vector geometries to match a reference raster."""
    vector_path = resolve_path(vector_path)
    reference_raster = resolve_path(reference_raster)
    output_path = resolve_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf = gpd.read_file(vector_path)
    with rasterio.open(reference_raster) as ref:
        if gdf.crs and ref.crs and gdf.crs != ref.crs:
            gdf = gdf.to_crs(ref.crs)
        shapes_iter: Iterable[tuple] = (
            (geom, row[value_field] if value_field else burn_value)
            for _, row in gdf.iterrows()
            for geom in [row.geometry]
            if geom is not None
        )
        burned = rasterize(
            shapes_iter,
            out_shape=(ref.height, ref.width),
            transform=ref.transform,
            fill=0,
            dtype="float32",
        )
        profile = ref.profile.copy()
        profile.update(dtype="float32", count=1, nodata=0)
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(burned, 1)
    return output_path


def vectorize_class_raster(
    raster_path: str | Path,
    output_path: str | Path,
    class_field: str = "class_id",
) -> Path:
    """Convert a classified raster to polygons."""
    raster_path = resolve_path(raster_path)
    output_path = resolve_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(raster_path) as src:
        data = src.read(1)
        mask_valid = data != src.nodata if src.nodata is not None else np.ones(data.shape, dtype=bool)
        records = [
            {class_field: int(value), "geometry": shape(geom)}
            for geom, value in shapes(data, mask=mask_valid, transform=src.transform)
            if value != src.nodata
        ]
        gdf = gpd.GeoDataFrame(records, crs=src.crs)
        gdf.to_file(output_path, driver="GPKG")
    return output_path

