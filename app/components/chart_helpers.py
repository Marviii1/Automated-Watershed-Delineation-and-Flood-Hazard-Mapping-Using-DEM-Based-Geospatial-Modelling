"""Chart helpers for Streamlit pages."""

from __future__ import annotations

import plotly.express as px
import streamlit as st


def bar_chart(df, x: str, y: str, title: str) -> None:
    """Render a Plotly bar chart if fields are available."""
    if df is None:
        return
    if x not in df.columns or y not in df.columns:
        st.warning(f"Cannot draw chart; missing `{x}` or `{y}`.")
        return
    fig = px.bar(df, x=x, y=y, title=title)
    st.plotly_chart(fig, use_container_width=True)


def scatter_chart(df, x: str, y: str, color: str | None = None, title: str = "") -> None:
    """Render a Plotly scatter chart if fields are available."""
    if df is None:
        return
    if x not in df.columns or y not in df.columns:
        st.warning(f"Cannot draw chart; missing `{x}` or `{y}`.")
        return
    fig = px.scatter(df, x=x, y=y, color=color if color in df.columns else None, title=title)
    st.plotly_chart(fig, use_container_width=True)

