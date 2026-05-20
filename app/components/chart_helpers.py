"""Chart helpers for Streamlit pages."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


PLOTLY_DARK_TEMPLATE = "plotly_dark"
CHART_BG = "#0e1621"
PAGE_BG = "#070b10"
TEXT = "#e8f0fb"
GRID = "rgba(232, 240, 251, 0.16)"


def apply_chart_theme(fig):
    """Force a dark Plotly style even when Streamlit Cloud injects its chart theme."""
    fig.update_layout(
        template=PLOTLY_DARK_TEMPLATE,
        paper_bgcolor=PAGE_BG,
        plot_bgcolor=CHART_BG,
        font_color=TEXT,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT)),
        margin=dict(l=72, r=36, t=64, b=64),
    )
    fig.update_xaxes(
        color=TEXT,
        gridcolor=GRID,
        zerolinecolor=GRID,
        linecolor="rgba(232, 240, 251, 0.35)",
    )
    fig.update_yaxes(
        color=TEXT,
        gridcolor=GRID,
        zerolinecolor=GRID,
        linecolor="rgba(232, 240, 251, 0.35)",
    )
    return fig


def bar_chart(df, x: str, y: str, title: str, color: str | None = None) -> None:
    """Render a Plotly bar chart if fields are available."""
    if df is None:
        return
    if x not in df.columns or y not in df.columns:
        st.warning(f"Cannot draw chart; missing `{x}` or `{y}`.")
        return
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color if color in df.columns else None,
        title=title,
        template=PLOTLY_DARK_TEMPLATE,
    )
    apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True, theme=None)


def scatter_chart(df, x: str, y: str, color: str | None = None, title: str = "") -> None:
    """Render a Plotly scatter chart if fields are available."""
    if df is None:
        return
    if x not in df.columns or y not in df.columns:
        st.warning(f"Cannot draw chart; missing `{x}` or `{y}`.")
        return
    fig = px.scatter(
        df,
        x=x,
        y=y,
        color=color if color in df.columns else None,
        title=title,
        template=PLOTLY_DARK_TEMPLATE,
    )
    apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True, theme=None)


def heatmap(df: pd.DataFrame, title: str = "Correlation Heatmap") -> None:
    """Render a numeric correlation heatmap."""
    if df is None or df.empty:
        return
    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        return
    corr = numeric.corr(numeric_only=True)
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="Tealrose", title=title)
    apply_chart_theme(fig)
    st.plotly_chart(fig, use_container_width=True, theme=None)
