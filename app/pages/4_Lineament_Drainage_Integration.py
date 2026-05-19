"""Lineament-drainage integration dashboard page."""

from __future__ import annotations

import streamlit as st

import _bootstrap  # noqa: F401
from app.components.map_helpers import show_raster_status, show_vector_layer
from app.components.ui_helpers import page_title, read_csv_or_message
from src.config import load_config_bundle

configs = load_config_bundle("config")
processed = configs["data"]["processed"]
page_title("Lineament-Drainage Integration")
st.caption("Outputs indicate structurally influenced drainage zones and potential fracture-controlled corridors; they do not directly prove groundwater recharge.")
show_raster_status(processed["lineament_density_raster"], "Lineament density", "scripts/08_lineament_drainage_analysis.py")
show_vector_layer(processed["drainage_lineament_intersections"], "Drainage-lineament intersections")
df = read_csv_or_message(processed["lineament_stats_csv"], "Run script 08_lineament_drainage_analysis.py to generate lineament statistics.")
if df is not None:
    st.dataframe(df, use_container_width=True)
