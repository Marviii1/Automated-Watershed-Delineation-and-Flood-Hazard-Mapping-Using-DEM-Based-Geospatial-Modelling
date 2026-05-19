"""Map helpers for lightweight dashboard display."""

from __future__ import annotations

import geopandas as gpd
import streamlit as st

from src.config import resolve_path


def show_vector_layer(path_value: str, label: str) -> None:
    """Display basic vector metadata and an interactive Streamlit map where possible."""
    path = resolve_path(path_value)
    if not path or not path.exists():
        st.info(f"Run the relevant processing script to generate {label}.")
        return
    gdf = gpd.read_file(path)
    st.write(f"**{label}:** {len(gdf)} features")
    try:
        display = gdf.to_crs("EPSG:4326")
        st.map(display)
    except Exception as exc:
        st.warning(f"Could not render map preview for {label}: {exc}")


def show_raster_status(path_value: str, label: str, script_hint: str) -> None:
    """Show raster availability; raster tile rendering can be added with leafmap if desired."""
    path = resolve_path(path_value)
    if path and path.exists():
        st.success(f"{label} is available: `{path}`")
    else:
        st.info(f"Run `{script_hint}` to generate this layer.")

