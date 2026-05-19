"""Study-area boundary validation and preparation helpers."""

from __future__ import annotations

import logging
from pathlib import Path

import geopandas as gpd

from src.config import resolve_path


REQUIRED_SHAPEFILE_SIDECARS = (".shp", ".shx", ".dbf", ".prj")


def shapefile_sidecar_status(path: str | Path) -> dict[str, bool]:
    """Return required shapefile sidecar availability for a configured .shp path."""
    resolved = resolve_path(path)
    if not resolved or resolved.suffix.lower() != ".shp":
        return {}
    return {suffix: resolved.with_suffix(suffix).exists() for suffix in REQUIRED_SHAPEFILE_SIDECARS}


def validate_study_area_boundary(path: str | Path, logger: logging.Logger) -> Path:
    """Validate that a study-area file is readable, polygonal, and has a CRS."""
    resolved = resolve_path(path)
    if not resolved or not resolved.exists():
        raise FileNotFoundError(f"Study area boundary not found: {path}")

    sidecars = shapefile_sidecar_status(resolved)
    missing_sidecars = [suffix for suffix, exists in sidecars.items() if not exists]
    if missing_sidecars:
        missing = ", ".join(missing_sidecars)
        raise FileNotFoundError(
            f"Study area shapefile is incomplete: {resolved}. Missing sidecar(s): {missing}"
        )

    gdf = gpd.read_file(resolved)
    if gdf.empty:
        raise ValueError(f"Study area boundary has no features: {resolved}")
    if gdf.crs is None:
        raise ValueError(f"Study area boundary has no CRS. Define it before running: {resolved}")
    if not gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).all():
        raise ValueError("Study area boundary must contain only Polygon or MultiPolygon geometry.")

    logger.info(
        "Validated study area boundary: %s (%s feature(s), CRS=%s)",
        resolved,
        len(gdf),
        gdf.crs,
    )
    return resolved


def prepare_study_area_boundary(
    input_path: str | Path,
    output_path: str | Path,
    dst_crs: str,
    logger: logging.Logger,
) -> Path:
    """Dissolve, repair, project, and save the study-area polygon."""
    input_path = validate_study_area_boundary(input_path, logger)
    output_path = resolve_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_file(input_path)
    gdf["geometry"] = gdf.geometry.make_valid()
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    if gdf.empty:
        raise ValueError(f"Study area boundary has no valid geometry after repair: {input_path}")

    dissolved = gdf.dissolve().reset_index(drop=True)
    dissolved["study_area"] = "Ilaje LGA"
    dissolved = dissolved.to_crs(dst_crs)
    dissolved.to_file(output_path, driver="GPKG", layer="study_area")
    logger.info("Prepared projected study area boundary: %s", output_path)
    return output_path
