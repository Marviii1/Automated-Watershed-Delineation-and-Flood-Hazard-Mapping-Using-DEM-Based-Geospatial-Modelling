"""Reusable Streamlit UI helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import resolve_path


def page_title(title: str, caption: str | None = None) -> None:
    """Render a consistent page title."""
    st.title(title)
    if caption:
        st.caption(caption)


def read_csv_or_message(path_value: str, message: str) -> pd.DataFrame | None:
    """Read a CSV if it exists; otherwise show an informational message."""
    path = resolve_path(path_value)
    if path and path.exists():
        return pd.read_csv(path)
    st.info(message)
    return None


def file_status(label: str, path_value: str) -> None:
    """Show a compact generated/missing status row."""
    path = resolve_path(path_value)
    status = "Available" if path and path.exists() else "Missing"
    st.write(f"**{label}:** {status}")

