"""Watershed and morphometry dashboard page."""

from __future__ import annotations

import streamlit as st

import _bootstrap  # noqa: F401
from app.components.chart_helpers import scatter_chart
from app.components.map_helpers import show_vector_layer
from app.components.ui_helpers import page_title, read_csv_or_message
from src.config import load_config_bundle

configs = load_config_bundle("config")
processed = configs["data"]["processed"]
page_title("Watershed and Morphometry")
show_vector_layer(processed["subbasins_vector"], "Sub-basins")
df = read_csv_or_message(
    processed["subbasin_morphometry_csv"],
    "Run script 07_compute_morphometric_parameters.py to generate morphometric results.",
)
if df is not None:
    st.dataframe(df, use_container_width=True)
    scatter_chart(df, "drainage_density_km_per_km2", "ruggedness_number", title="Drainage Density vs Ruggedness")
