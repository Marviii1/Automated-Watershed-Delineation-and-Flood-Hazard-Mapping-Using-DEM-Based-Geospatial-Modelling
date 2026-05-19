"""Hydrological modelling wrappers, primarily around WhiteboxTools."""

from __future__ import annotations

import logging
from pathlib import Path

try:
    from whitebox.whitebox_tools import WhiteboxTools
except Exception:  # pragma: no cover - handled at runtime in GIS environment
    WhiteboxTools = None

from src.config import resolve_path


def get_whitebox(working_dir: str | Path, verbose: bool = False):
    """Create and configure a WhiteboxTools instance."""
    if WhiteboxTools is None:
        raise ImportError("whitebox is not available. Install/configure it in your GIS environment.")
    wbt = WhiteboxTools()
    workdir = resolve_path(working_dir)
    workdir.mkdir(parents=True, exist_ok=True)
    wbt.set_working_dir(str(workdir))
    wbt.verbose = verbose
    return wbt


def breach_or_fill_dem(
    dem_path: str | Path,
    output_path: str | Path,
    method: str,
    working_dir: str | Path,
    logger: logging.Logger,
) -> Path:
    """Hydrologically correct a DEM using breaching or sink filling."""
    dem_path = resolve_path(dem_path)
    output_path = resolve_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wbt = get_whitebox(working_dir)
    method = method.lower()
    if method == "breach":
        wbt.breach_depressions(str(dem_path), str(output_path))
    elif method == "fill":
        wbt.fill_depressions(str(dem_path), str(output_path))
    else:
        raise ValueError("dem_preprocessing_method must be 'breach' or 'fill'.")
    logger.info("Hydrologically corrected DEM written: %s", output_path)
    return output_path


def terrain_derivatives(
    dem_path: str | Path,
    output_dir: str | Path,
    working_dir: str | Path,
    logger: logging.Logger,
    hillshade_azimuth: float = 315.0,
    hillshade_altitude: float = 45.0,
    multi_hillshade_azimuths: list[float] | None = None,
) -> dict[str, Path]:
    """Generate slope, aspect, hillshade, and optional multi-azimuth hillshades."""
    dem_path = resolve_path(dem_path)
    output_dir = resolve_path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    wbt = get_whitebox(working_dir)
    outputs = {
        "slope": output_dir / "slope_degrees.tif",
        "aspect": output_dir / "aspect_degrees.tif",
        "hillshade": output_dir / "hillshade.tif",
    }
    wbt.slope(str(dem_path), str(outputs["slope"]), units="degrees")
    wbt.aspect(str(dem_path), str(outputs["aspect"]))
    wbt.hillshade(
        str(dem_path),
        str(outputs["hillshade"]),
        azimuth=hillshade_azimuth,
        altitude=hillshade_altitude,
    )
    for azimuth in multi_hillshade_azimuths or []:
        key = f"hillshade_{int(azimuth)}"
        outputs[key] = output_dir / f"hillshade_{int(azimuth)}.tif"
        wbt.hillshade(
            str(dem_path),
            str(outputs[key]),
            azimuth=float(azimuth),
            altitude=hillshade_altitude,
        )
    logger.info("Terrain derivatives written to %s", output_dir)
    return outputs


def flow_direction_and_accumulation(
    dem_path: str | Path,
    pointer_path: str | Path,
    accumulation_path: str | Path,
    working_dir: str | Path,
    logger: logging.Logger,
) -> tuple[Path, Path]:
    """Generate D8 pointer and flow accumulation rasters."""
    dem_path = resolve_path(dem_path)
    pointer_path = resolve_path(pointer_path)
    accumulation_path = resolve_path(accumulation_path)
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    accumulation_path.parent.mkdir(parents=True, exist_ok=True)
    wbt = get_whitebox(working_dir)
    wbt.d8_pointer(str(dem_path), str(pointer_path))
    wbt.d8_flow_accumulation(str(dem_path), str(accumulation_path), out_type="cells")
    logger.info("D8 pointer written: %s", pointer_path)
    logger.info("D8 accumulation written: %s", accumulation_path)
    return pointer_path, accumulation_path


def extract_streams(
    accumulation_path: str | Path,
    stream_raster_path: str | Path,
    threshold_cells: int,
    working_dir: str | Path,
    logger: logging.Logger,
) -> Path:
    """Extract a stream raster from flow accumulation."""
    accumulation_path = resolve_path(accumulation_path)
    stream_raster_path = resolve_path(stream_raster_path)
    stream_raster_path.parent.mkdir(parents=True, exist_ok=True)
    wbt = get_whitebox(working_dir)
    wbt.extract_streams(str(accumulation_path), str(stream_raster_path), threshold_cells)
    logger.info("Stream raster written: %s", stream_raster_path)
    return stream_raster_path


def stream_to_vector(
    stream_raster: str | Path,
    pointer_raster: str | Path,
    output_vector: str | Path,
    working_dir: str | Path,
    logger: logging.Logger,
) -> Path:
    """Convert stream raster to vector polylines."""
    stream_raster = resolve_path(stream_raster)
    pointer_raster = resolve_path(pointer_raster)
    output_vector = resolve_path(output_vector)
    output_vector.parent.mkdir(parents=True, exist_ok=True)
    wbt = get_whitebox(working_dir)
    wbt.raster_streams_to_vector(str(stream_raster), str(pointer_raster), str(output_vector))
    logger.info("Stream vector written: %s", output_vector)
    return output_vector


def stream_order(
    stream_raster: str | Path,
    pointer_raster: str | Path,
    output_path: str | Path,
    method: str,
    working_dir: str | Path,
    logger: logging.Logger,
) -> Path:
    """Generate stream order raster using Strahler or Shreve ordering."""
    stream_raster = resolve_path(stream_raster)
    pointer_raster = resolve_path(pointer_raster)
    output_path = resolve_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wbt = get_whitebox(working_dir)
    method = method.lower()
    if method == "strahler":
        wbt.strahler_stream_order(str(pointer_raster), str(stream_raster), str(output_path))
    elif method == "shreve":
        wbt.shreve_stream_magnitude(str(pointer_raster), str(stream_raster), str(output_path))
    else:
        raise ValueError("stream order method must be 'strahler' or 'shreve'.")
    logger.info("%s stream order written: %s", method.title(), output_path)
    return output_path


def delineate_watershed(
    pointer_raster: str | Path,
    pour_points: str | Path,
    output_raster: str | Path,
    working_dir: str | Path,
    logger: logging.Logger,
    esri_pointer: bool = False,
) -> Path:
    """Delineate watershed raster from D8 pointer and pour points."""
    pointer_raster = resolve_path(pointer_raster)
    pour_points = resolve_path(pour_points)
    output_raster = resolve_path(output_raster)
    output_raster.parent.mkdir(parents=True, exist_ok=True)
    wbt = get_whitebox(working_dir)
    wbt.watershed(str(pointer_raster), str(pour_points), str(output_raster), esri_pntr=esri_pointer)
    logger.info("Watershed raster written: %s", output_raster)
    return output_raster


def snap_pour_points(
    pour_points_raster: str | Path,
    accumulation_raster: str | Path,
    output_raster: str | Path,
    snap_distance: float,
    working_dir: str | Path,
    logger: logging.Logger,
) -> Path:
    """Snap pour points to nearby high-flow-accumulation cells."""
    pour_points_raster = resolve_path(pour_points_raster)
    accumulation_raster = resolve_path(accumulation_raster)
    output_raster = resolve_path(output_raster)
    output_raster.parent.mkdir(parents=True, exist_ok=True)
    wbt = get_whitebox(working_dir)
    wbt.snap_pour_points(
        str(pour_points_raster),
        str(accumulation_raster),
        str(output_raster),
        snap_distance,
    )
    logger.info("Snapped pour point raster written: %s", output_raster)
    return output_raster
