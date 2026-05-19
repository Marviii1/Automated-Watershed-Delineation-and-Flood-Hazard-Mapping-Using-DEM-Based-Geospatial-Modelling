"""Streamlit dashboard entry point."""

from __future__ import annotations

import streamlit as st

import _bootstrap  # noqa: F401
from src.config import load_config_bundle

configs = load_config_bundle("config")
dashboard = configs["dashboard"]

st.set_page_config(page_title=dashboard["title"], layout="wide")
st.title(dashboard["title"])
st.caption(dashboard.get("subtitle", ""))
st.write(dashboard.get("project_text", {}).get("home_summary", ""))

st.subheader("Workflow Status")
for label, path in dashboard.get("layers", {}).items():
    st.write(f"- **{label.replace('_', ' ').title()}**: `{path}`")

st.info("Use the pages in the sidebar to inspect generated outputs. The dashboard reads outputs only and does not run heavy GIS processing.")
