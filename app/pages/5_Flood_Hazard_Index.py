"""Flood hazard dashboard page."""

from __future__ import annotations

import streamlit as st

import _bootstrap  # noqa: F401
from app.components.chart_helpers import bar_chart
from app.components.map_helpers import show_raster_status
from app.components.ui_helpers import page_title, read_csv_or_message
from src.config import load_config_bundle

configs = load_config_bundle("config")
processed = configs["data"]["processed"]
page_title("Flood Hazard Index")
show_raster_status(processed["fhi_classified"], "Classified flood hazard raster", "scripts/10_compute_flood_hazard_index.py")
df = read_csv_or_message(processed["hazard_area_summary_csv"], "Run script 10_compute_flood_hazard_index.py to generate hazard area statistics.")
if df is not None:
    st.dataframe(df, use_container_width=True)
    bar_chart(df, "hazard_label", "area_km2", "Hazard Area by Class")
