"""Report asset generation helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import resolve_path


def table_markdown(path: str | Path, max_rows: int = 10) -> str:
    """Return a compact Markdown table if a CSV exists."""
    path = resolve_path(path)
    if not path or not path.exists():
        return f"_Missing table: {path}_"
    return pd.read_csv(path).head(max_rows).to_markdown(index=False)


def generate_markdown_report(configs: dict, output_path: str | Path) -> Path:
    """Assemble a report-friendly Markdown summary from generated outputs."""
    output_path = resolve_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    project = configs["project"]
    data = configs["data"]
    content = f"""# {project.get("project_name", "HydroMorpho-Flood Intelligence System")}

## Study Area

**Study area:** {project.get("study_area_name", "Not specified")}  
**Country:** {project.get("country", "Not specified")}  
**Description:** {project.get("basin_description", "Not specified")}

## Datasets Used

- DEM: `{data.get("raw", {}).get("dem")}`
- Boundary: `{data.get("raw", {}).get("study_area_boundary")}`
- Outlets: `{data.get("raw", {}).get("outlet_points")}`
- LULC: `{data.get("raw", {}).get("lulc")}`
- Soils: `{data.get("raw", {}).get("soils")}`

## Methodology

The workflow clips and projects the DEM, applies hydrological conditioning, derives D8 flow products, extracts streams, delineates watershed and sub-basins, computes morphometric indicators, integrates optional lineament information, creates flood hazard factor scores, and ranks sub-basins.

## Morphometric Summary

{table_markdown(data.get("processed", {}).get("subbasin_morphometry_csv"))}

## Flood Hazard Area Summary

{table_markdown(data.get("processed", {}).get("hazard_area_summary_csv"))}

## Sub-Basin Priority Ranking

{table_markdown(data.get("processed", {}).get("subbasin_priority_csv"))}

## Limitations

Flood hazard classes are susceptibility indicators derived from terrain and thematic factor overlay. They are not hydraulic inundation depths. Lineament-drainage outputs identify possible structurally influenced drainage zones and should be interpreted with geological context and field validation.
"""
    output_path.write_text(content, encoding="utf-8")
    return output_path

