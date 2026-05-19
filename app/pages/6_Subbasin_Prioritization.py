"""Sub-basin prioritization dashboard page."""

from __future__ import annotations

import streamlit as st

import _bootstrap  # noqa: F401
from app.components.chart_helpers import bar_chart
from app.components.map_helpers import show_vector_layer
from app.components.ui_helpers import page_title, read_csv_or_message
from src.config import load_config_bundle

configs = load_config_bundle("config")
processed = configs["data"]["processed"]
page_title("Sub-Basin Prioritization")
show_vector_layer(processed["subbasin_priority_gpkg"], "Priority ranked sub-basins")
df = read_csv_or_message(processed["subbasin_priority_csv"], "Run script 11_rank_subbasins.py to generate priority rankings.")
if df is not None:
    st.dataframe(df.sort_values("priority_rank"), use_container_width=True)
    bar_chart(df.sort_values("priority_rank"), "subbasin_id", "priority_score", "Priority Score by Sub-Basin")
