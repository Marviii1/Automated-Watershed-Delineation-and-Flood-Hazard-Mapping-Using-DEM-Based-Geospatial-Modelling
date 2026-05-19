"""Sub-basin priority ranking utilities."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.config import resolve_path
from src.constants import PRIORITY_CLASS_LABELS


def minmax(series: pd.Series) -> pd.Series:
    """Scale numeric series to 0-1."""
    if series.max() == series.min():
        return pd.Series(0.0, index=series.index)
    return (series - series.min()) / (series.max() - series.min())


def rank_subbasins(
    subbasins_path: str | Path,
    morphometry_csv: str | Path,
    hazard_csv: str | Path,
    output_csv: str | Path,
    output_gpkg: str | Path,
    id_field: str = "subbasin_id",
    weights: dict[str, float] | None = None,
) -> tuple[Path, Path]:
    """Combine hazard and morphometric indicators into priority ranking outputs."""
    weights = weights or {
        "fhi_mean": 0.35,
        "drainage_density_km_per_km2": 0.2,
        "ruggedness_number": 0.15,
        "stream_frequency_no_per_km2": 0.15,
        "basin_relief_m": 0.15,
    }
    subbasins = gpd.read_file(resolve_path(subbasins_path))
    morph = pd.read_csv(resolve_path(morphometry_csv))
    hazard = pd.read_csv(resolve_path(hazard_csv))
    table = subbasins[[id_field, "geometry"]].merge(morph, on=id_field, how="left").merge(
        hazard, on=id_field, how="left"
    )
    score = pd.Series(0.0, index=table.index)
    for field, weight in weights.items():
        if field in table.columns:
            score += minmax(pd.to_numeric(table[field], errors="coerce").fillna(0)) * float(weight)
    table["priority_score"] = score
    table["priority_rank"] = table["priority_score"].rank(ascending=False, method="dense").astype(int)
    table["priority_class"] = pd.qcut(
        table["priority_score"].rank(method="first"),
        q=min(5, len(table)),
        labels=False,
        duplicates="drop",
    ) + 1 if len(table) > 1 else 3
    table["priority_label"] = table["priority_class"].map(PRIORITY_CLASS_LABELS)

    output_csv = resolve_path(output_csv)
    output_gpkg = resolve_path(output_gpkg)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_gpkg.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(table.drop(columns="geometry")).to_csv(output_csv, index=False)
    gpd.GeoDataFrame(table, geometry="geometry", crs=subbasins.crs).to_file(output_gpkg, driver="GPKG")
    return output_csv, output_gpkg

