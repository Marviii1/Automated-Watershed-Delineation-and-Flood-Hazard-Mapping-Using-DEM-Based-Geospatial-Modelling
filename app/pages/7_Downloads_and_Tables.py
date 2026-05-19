"""Downloads and tables dashboard page."""

from __future__ import annotations

import streamlit as st

import _bootstrap  # noqa: F401
from app.components.ui_helpers import page_title, read_csv_or_message
from src.config import load_config_bundle, resolve_path

configs = load_config_bundle("config")
processed = configs["data"]["processed"]
page_title("Downloads and Tables")
for label, path_value in processed.items():
    path = resolve_path(path_value)
    if path and path.exists() and path.suffix.lower() == ".csv":
        st.subheader(label.replace("_", " ").title())
        df = read_csv_or_message(path_value, "")
        if df is not None:
            st.dataframe(df, use_container_width=True)
            st.download_button(f"Download {label}", df.to_csv(index=False), file_name=path.name)
    elif path and path.exists():
        st.write(f"**{label}:** `{path}`")
