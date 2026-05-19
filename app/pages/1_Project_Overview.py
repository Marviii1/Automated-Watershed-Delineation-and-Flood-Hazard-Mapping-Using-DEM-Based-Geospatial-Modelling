"""Project overview dashboard page."""

from __future__ import annotations

import streamlit as st

import _bootstrap  # noqa: F401
from app.components.ui_helpers import file_status, page_title
from src.config import load_config_bundle

configs = load_config_bundle("config")
page_title("Project Overview", configs["dashboard"].get("subtitle"))
project = configs["project"]
st.write(project.get("basin_description", ""))
st.subheader("Configured Outputs")
for label, path in configs["data"]["processed"].items():
    file_status(label, path)
