"""Chart helpers for Streamlit pages."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


PLOTLY_DARK_TEMPLATE = "plotly_dark"


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
    fig.update_layout(paper_bgcolor="#070b10", plot_bgcolor="#0e1621", font_color="#e8f0fb")
    st.plotly_chart(fig, use_container_width=True)


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
    fig.update_layout(paper_bgcolor="#070b10", plot_bgcolor="#0e1621", font_color="#e8f0fb")
    st.plotly_chart(fig, use_container_width=True)


def heatmap(df: pd.DataFrame, title: str = "Correlation Heatmap") -> None:
    """Render a numeric correlation heatmap."""
    if df is None or df.empty:
        return
    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        return
    corr = numeric.corr(numeric_only=True)
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="Tealrose", title=title)
    fig.update_layout(
        template=PLOTLY_DARK_TEMPLATE,
        paper_bgcolor="#070b10",
        plot_bgcolor="#0e1621",
        font_color="#e8f0fb",
    )
    st.plotly_chart(fig, use_container_width=True)
