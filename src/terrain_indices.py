"""Derived raster factors for flood-susceptibility modelling."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio

from src.config import resolve_path
from src.raster_utils import read_raster_array, write_single_band_raster


def distance_to_stream_raster(stream_raster: str | Path, output_path: str | Path) -> Path:
    """Create a distance-to-stream raster in map units from a binary stream raster."""
    stream_raster = resolve_path(stream_raster)
    with rasterio.open(stream_raster) as src:
        streams = src.read(1)
        profile = src.profile.copy()
        pixel_size = float(abs(src.transform.a))

    try:
        from scipy.ndimage import distance_transform_edt
    except Exception as exc:  # pragma: no cover - optional dependency in user's GIS env
        raise ImportError("scipy is required to derive distance_to_stream raster.") from exc

    distance = distance_transform_edt(streams <= 0) * pixel_size
    return write_single_band_raster(output_path, distance.astype("float32"), profile, dtype="float32", nodata=-9999)


def topographic_wetness_index(
    flow_accumulation: str | Path,
    slope_degrees: str | Path,
    output_path: str | Path,
) -> Path:
    """Compute TWI = ln(specific catchment area / tan(slope))."""
    accumulation, profile = read_raster_array(flow_accumulation, masked=True)
    slope, _ = read_raster_array(slope_degrees, masked=True)
    cell_size = abs(float(profile["transform"].a))
    slope_rad = np.deg2rad(np.maximum(np.ma.filled(slope, np.nan), 0.001))
    sca = (np.ma.filled(accumulation, np.nan) + 1.0) * cell_size
    twi = np.log(sca / np.tan(slope_rad))
    return write_single_band_raster(output_path, twi.astype("float32"), profile, dtype="float32", nodata=-9999)


def stream_power_index(
    flow_accumulation: str | Path,
    slope_degrees: str | Path,
    output_path: str | Path,
) -> Path:
    """Compute SPI = flow accumulation * tan(slope)."""
    accumulation, profile = read_raster_array(flow_accumulation, masked=True)
    slope, _ = read_raster_array(slope_degrees, masked=True)
    slope_rad = np.deg2rad(np.maximum(np.ma.filled(slope, np.nan), 0.001))
    spi = np.ma.filled(accumulation, np.nan) * np.tan(slope_rad)
    return write_single_band_raster(output_path, spi.astype("float32"), profile, dtype="float32", nodata=-9999)
