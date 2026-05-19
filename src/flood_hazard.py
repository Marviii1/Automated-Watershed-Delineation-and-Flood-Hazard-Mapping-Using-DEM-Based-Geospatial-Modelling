"""Flood hazard factor preparation, weighted overlay, and summaries."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterstats import zonal_stats

from src.config import resolve_path
from src.constants import DEFAULT_NODATA, HAZARD_CLASS_LABELS
from src.raster_utils import (
    align_raster_to_reference,
    read_raster_array,
    reclassify_array,
    write_single_band_raster,
)


def prepare_factor_raster(
    factor_name: str,
    source_path: str | Path,
    reference_raster: str | Path,
    output_path: str | Path,
    reclass_rules: list[dict],
) -> Path:
    """Align and reclassify a flood conditioning factor."""
    aligned = resolve_path(output_path).with_name(f"{factor_name}_aligned.tif")
    align_raster_to_reference(source_path, reference_raster, aligned, logger=_NullLogger())
    data, profile = read_raster_array(aligned, masked=True)
    reclassified = reclassify_array(data, reclass_rules, nodata=profile.get("nodata"))
    return write_single_band_raster(output_path, reclassified, profile, dtype="float32", nodata=DEFAULT_NODATA)


def weighted_overlay(
    reclassified_factor_paths: dict[str, str | Path],
    weights: dict[str, float],
    output_path: str | Path,
) -> Path:
    """Calculate continuous Flood Hazard Index as weighted sum of 1-5 factor scores."""
    arrays = []
    total_weight = 0.0
    profile = None
    for factor, path in reclassified_factor_paths.items():
        weight = float(weights.get(factor, 0.0))
        if weight <= 0:
            continue
        array, factor_profile = read_raster_array(path, masked=False)
        mask = array == factor_profile.get("nodata", DEFAULT_NODATA)
        arrays.append(np.ma.array(array.astype("float32"), mask=mask) * weight)
        total_weight += weight
        profile = factor_profile
    if not arrays:
        raise ValueError("No valid reclassified factor rasters were supplied for weighted overlay.")
    fhi = sum(arrays) / total_weight if total_weight else sum(arrays)
    return write_single_band_raster(output_path, fhi, profile, dtype="float32", nodata=DEFAULT_NODATA)


def classify_hazard_index(
    fhi_path: str | Path,
    output_path: str | Path,
    breaks: list[dict],
) -> Path:
    """Classify a continuous FHI raster into hazard classes."""
    fhi, profile = read_raster_array(fhi_path, masked=True)
    classified = reclassify_array(fhi, breaks, nodata=profile.get("nodata"))
    classified[classified == DEFAULT_NODATA] = 0
    return write_single_band_raster(output_path, classified, profile, dtype="uint8", nodata=0)


def summarize_hazard_area(classified_raster: str | Path, output_csv: str | Path) -> Path:
    """Summarize classified hazard area by class."""
    classified_raster = resolve_path(classified_raster)
    output_csv = resolve_path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(classified_raster) as src:
        data = src.read(1)
        pixel_area_km2 = abs(src.transform.a * src.transform.e) / 1_000_000.0
        values, counts = np.unique(data[data > 0], return_counts=True)
    rows = [
        {
            "hazard_class": int(value),
            "hazard_label": HAZARD_CLASS_LABELS.get(int(value), str(value)),
            "area_km2": float(count * pixel_area_km2),
        }
        for value, count in zip(values, counts)
    ]
    pd.DataFrame(rows).to_csv(output_csv, index=False)
    return output_csv


def zonal_hazard_summary(
    subbasins_path: str | Path,
    fhi_path: str | Path,
    classified_path: str | Path,
    output_csv: str | Path,
    id_field: str = "subbasin_id",
) -> Path:
    """Calculate FHI mean/max and majority hazard class per sub-basin."""
    subbasins = gpd.read_file(resolve_path(subbasins_path))
    continuous = zonal_stats(subbasins, resolve_path(fhi_path), stats=["mean", "max"])
    categorical = zonal_stats(subbasins, resolve_path(classified_path), categorical=True)
    rows = []
    for basin_id, cont, cat in zip(subbasins[id_field], continuous, categorical):
        hazard_counts = {int(k): v for k, v in cat.items() if int(k) > 0}
        majority = max(hazard_counts, key=hazard_counts.get) if hazard_counts else np.nan
        rows.append(
            {
                id_field: basin_id,
                "fhi_mean": cont.get("mean"),
                "fhi_max": cont.get("max"),
                "majority_hazard_class": majority,
                "majority_hazard_label": HAZARD_CLASS_LABELS.get(majority, ""),
            }
        )
    output_csv = resolve_path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output_csv, index=False)
    return output_csv


def ahp_consistency_ratio(pairwise_matrix: np.ndarray) -> dict[str, float]:
    """Compute AHP consistency ratio for a pairwise comparison matrix."""
    n = pairwise_matrix.shape[0]
    eigvals, eigvecs = np.linalg.eig(pairwise_matrix)
    max_eig = float(np.max(eigvals.real))
    ci = (max_eig - n) / (n - 1) if n > 1 else 0.0
    random_index = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}
    ri = random_index.get(n, 1.49)
    cr = ci / ri if ri else 0.0
    return {"lambda_max": max_eig, "consistency_index": ci, "consistency_ratio": cr}


class _NullLogger:
    def info(self, *args, **kwargs):  # noqa: D401
        pass
