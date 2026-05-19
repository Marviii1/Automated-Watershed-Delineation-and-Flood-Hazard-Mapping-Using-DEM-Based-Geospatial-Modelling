"""Morphometric formula functions and table builders."""

from __future__ import annotations

import math
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterstats import zonal_stats

from src.config import resolve_path


def drainage_density(total_stream_length_km: float, basin_area_km2: float) -> float:
    """Drainage density = total stream length / basin area."""
    return safe_divide(total_stream_length_km, basin_area_km2)


def stream_frequency(total_stream_count: float, basin_area_km2: float) -> float:
    """Stream frequency = total number of streams / basin area."""
    return safe_divide(total_stream_count, basin_area_km2)


def form_factor(basin_area_km2: float, basin_length_km: float) -> float:
    """Form factor = basin area / basin length squared."""
    return safe_divide(basin_area_km2, basin_length_km**2)


def circularity_ratio(basin_area_km2: float, basin_perimeter_km: float) -> float:
    """Circularity ratio = 4*pi*A / P squared."""
    return safe_divide(4 * math.pi * basin_area_km2, basin_perimeter_km**2)


def elongation_ratio(basin_area_km2: float, basin_length_km: float) -> float:
    """Elongation ratio = diameter of circle of same area / basin length."""
    equivalent_diameter = 2 * math.sqrt(basin_area_km2 / math.pi)
    return safe_divide(equivalent_diameter, basin_length_km)


def ruggedness_number(basin_relief_km: float, drainage_density_value: float) -> float:
    """Ruggedness number = basin relief * drainage density."""
    return basin_relief_km * drainage_density_value


def relief_ratio(basin_relief_km: float, basin_length_km: float) -> float:
    """Relief ratio = basin relief / basin length."""
    return safe_divide(basin_relief_km, basin_length_km)


def infiltration_number(drainage_density_value: float, stream_frequency_value: float) -> float:
    """Infiltration number = drainage density * stream frequency."""
    return drainage_density_value * stream_frequency_value


def safe_divide(numerator: float, denominator: float) -> float:
    """Divide safely and return NaN when denominator is zero or missing."""
    if denominator in (0, None) or np.isnan(denominator):
        return float("nan")
    return float(numerator) / float(denominator)


def estimate_basin_length_km(geometry) -> float:
    """Estimate basin length from the maximum dimension of the minimum rotated rectangle."""
    rect = geometry.minimum_rotated_rectangle
    coords = list(rect.exterior.coords)
    distances = [
        math.dist(coords[i], coords[i + 1]) / 1000.0
        for i in range(len(coords) - 1)
    ]
    return max(distances) if distances else float("nan")


def summarize_streams_by_basin(
    basins: gpd.GeoDataFrame,
    streams: gpd.GeoDataFrame,
    basin_id_field: str,
    order_field: str | None = None,
) -> pd.DataFrame:
    """Summarize stream count and length within basin polygons."""
    streams = streams.copy()
    if streams.crs is None and basins.crs is not None:
        streams = streams.set_crs(basins.crs, allow_override=True)
    if basins.crs and streams.crs and basins.crs != streams.crs:
        streams = streams.to_crs(basins.crs)
    joined = gpd.overlay(streams, basins[[basin_id_field, "geometry"]], how="intersection")
    if joined.empty:
        return pd.DataFrame(columns=[basin_id_field, "stream_count", "total_stream_length_km"])
    joined["length_km"] = joined.geometry.length / 1000.0
    group_fields = [basin_id_field] + ([order_field] if order_field and order_field in joined.columns else [])
    summary = joined.groupby(group_fields).agg(
        stream_count=("geometry", "count"),
        total_stream_length_km=("length_km", "sum"),
        mean_stream_length_km=("length_km", "mean"),
    ).reset_index()
    return summary


def elevation_stats_by_basin(
    basins_path: str | Path,
    dem_path: str | Path,
    basin_id_field: str,
) -> pd.DataFrame:
    """Calculate elevation min, max, mean, and range for each basin."""
    basins_path = resolve_path(basins_path)
    dem_path = resolve_path(dem_path)
    basins = gpd.read_file(basins_path)
    stats = zonal_stats(basins, dem_path, stats=["min", "max", "mean"], nodata=None)
    rows = []
    for basin_id, stat in zip(basins[basin_id_field], stats):
        elev_min = stat.get("min")
        elev_max = stat.get("max")
        rows.append(
            {
                basin_id_field: basin_id,
                "elev_min_m": elev_min,
                "elev_max_m": elev_max,
                "elev_mean_m": stat.get("mean"),
                "basin_relief_m": elev_max - elev_min if elev_min is not None and elev_max is not None else np.nan,
            }
        )
    return pd.DataFrame(rows)


def slope_stats_by_basin(
    basins_path: str | Path,
    slope_path: str | Path,
    basin_id_field: str,
) -> pd.DataFrame:
    """Calculate average slope for each basin."""
    basins_path = resolve_path(basins_path)
    slope_path = resolve_path(slope_path)
    basins = gpd.read_file(basins_path)
    stats = zonal_stats(basins, slope_path, stats=["mean"], nodata=None)
    return pd.DataFrame(
        [
            {basin_id_field: basin_id, "average_slope_degrees": stat.get("mean")}
            for basin_id, stat in zip(basins[basin_id_field], stats)
        ]
    )


def build_morphometric_table(
    basins: gpd.GeoDataFrame,
    stream_summary: pd.DataFrame,
    elevation_summary: pd.DataFrame,
    slope_summary: pd.DataFrame | None = None,
    basin_id_field: str = "subbasin_id",
) -> pd.DataFrame:
    """Build a basin-level morphometric table from geometry, stream, and relief summaries."""
    rows = []
    stream_totals = stream_summary.groupby(basin_id_field).agg(
        stream_count=("stream_count", "sum"),
        total_stream_length_km=("total_stream_length_km", "sum"),
        mean_stream_length_km=("mean_stream_length_km", "mean"),
    ).reset_index() if not stream_summary.empty else pd.DataFrame(columns=[basin_id_field])

    elev_lookup = elevation_summary.set_index(basin_id_field).to_dict("index") if not elevation_summary.empty else {}
    slope_lookup = (
        slope_summary.set_index(basin_id_field).to_dict("index")
        if slope_summary is not None and not slope_summary.empty
        else {}
    )
    stream_lookup = stream_totals.set_index(basin_id_field).to_dict("index") if not stream_totals.empty else {}

    for _, row in basins.iterrows():
        basin_id = row[basin_id_field]
        area_km2 = row.geometry.area / 1_000_000.0
        perimeter_km = row.geometry.length / 1000.0
        length_km = estimate_basin_length_km(row.geometry)
        stream_info = stream_lookup.get(basin_id, {})
        elev_info = elev_lookup.get(basin_id, {})
        slope_info = slope_lookup.get(basin_id, {})
        total_length = float(stream_info.get("total_stream_length_km", 0.0) or 0.0)
        stream_count = float(stream_info.get("stream_count", 0.0) or 0.0)
        dd = drainage_density(total_length, area_km2)
        sf = stream_frequency(stream_count, area_km2)
        relief_m = elev_info.get("basin_relief_m", np.nan)
        relief_km = relief_m / 1000.0 if pd.notna(relief_m) else np.nan
        rows.append(
            {
                basin_id_field: basin_id,
                "area_km2": area_km2,
                "perimeter_km": perimeter_km,
                "basin_length_km": length_km,
                "stream_count": stream_count,
                "total_stream_length_km": total_length,
                "mean_stream_length_km": stream_info.get("mean_stream_length_km", np.nan),
                "drainage_density_km_per_km2": dd,
                "stream_frequency_no_per_km2": sf,
                "drainage_texture": safe_divide(stream_count, perimeter_km),
                "form_factor": form_factor(area_km2, length_km),
                "circularity_ratio": circularity_ratio(area_km2, perimeter_km),
                "elongation_ratio": elongation_ratio(area_km2, length_km),
                "infiltration_number": infiltration_number(dd, sf),
                "elev_min_m": elev_info.get("elev_min_m", np.nan),
                "elev_max_m": elev_info.get("elev_max_m", np.nan),
                "elev_mean_m": elev_info.get("elev_mean_m", np.nan),
                "basin_relief_m": relief_m,
                "relief_ratio": relief_ratio(relief_km, length_km),
                "relative_relief": safe_divide(relief_m, perimeter_km * 1000.0),
                "ruggedness_number": ruggedness_number(relief_km, dd),
                "average_slope_degrees": slope_info.get("average_slope_degrees", np.nan),
            }
        )
    table = pd.DataFrame(rows)
    table["fast_runoff_tendency"] = pd.qcut(
        table["drainage_density_km_per_km2"].rank(method="first"),
        q=min(5, len(table)),
        labels=False,
        duplicates="drop",
    ) + 1 if len(table) > 1 else 1
    return table


def bifurcation_ratio_by_order(stream_order_summary: pd.DataFrame, order_field: str = "stream_order") -> pd.DataFrame:
    """Estimate bifurcation ratio as N_u / N_(u+1) from stream counts by order."""
    if stream_order_summary.empty or order_field not in stream_order_summary.columns:
        return pd.DataFrame(columns=[order_field, "next_order", "bifurcation_ratio"])
    order_counts = stream_order_summary.groupby(order_field)["stream_count"].sum().sort_index()
    rows = []
    for order, count in order_counts.items():
        next_count = order_counts.get(order + 1, np.nan)
        rows.append(
            {
                order_field: order,
                "next_order": order + 1,
                "stream_count": count,
                "next_order_stream_count": next_count,
                "bifurcation_ratio": safe_divide(count, next_count),
            }
        )
    return pd.DataFrame(rows)
