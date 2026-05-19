"""Static map and chart creation helpers."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import rasterio
from rasterio.plot import show

from src.config import resolve_path


def raster_preview(raster_path: str | Path, output_png: str | Path, title: str, cmap: str = "viridis") -> Path:
    """Create a simple raster preview PNG."""
    output_png = resolve_path(output_png)
    output_png.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(resolve_path(raster_path)) as src:
        fig, ax = plt.subplots(figsize=(9, 7))
        show(src, ax=ax, cmap=cmap)
        ax.set_title(title)
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(output_png, dpi=180)
        plt.close(fig)
    return output_png


def vector_map(vector_path: str | Path, output_png: str | Path, title: str, column: str | None = None) -> Path:
    """Create a simple vector map PNG."""
    output_png = resolve_path(output_png)
    output_png.parent.mkdir(parents=True, exist_ok=True)
    gdf = gpd.read_file(resolve_path(vector_path))
    fig, ax = plt.subplots(figsize=(9, 7))
    gdf.plot(ax=ax, column=column, legend=bool(column), linewidth=0.8, edgecolor="black")
    ax.set_title(title)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output_png, dpi=180)
    plt.close(fig)
    return output_png


def bar_chart(csv_path: str | Path, x: str, y: str, output_png: str | Path, title: str) -> Path:
    """Create a bar chart from a CSV table."""
    output_png = resolve_path(output_png)
    output_png.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(resolve_path(csv_path))
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(df[x].astype(str), df[y])
    ax.set_title(title)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    fig.tight_layout()
    fig.savefig(output_png, dpi=180)
    plt.close(fig)
    return output_png

