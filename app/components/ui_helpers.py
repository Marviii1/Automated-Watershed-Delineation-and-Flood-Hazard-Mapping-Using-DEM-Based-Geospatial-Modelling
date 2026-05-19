"""Reusable Streamlit UI helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import resolve_path


def apply_dark_theme() -> None:
    """Apply a compact dark analytical dashboard style."""
    st.markdown(
        """
        <style>
        :root {
            --bg: #070b10;
            --panel: #0e1621;
            --panel-2: #111c2a;
            --border: #223248;
            --text: #e8f0fb;
            --muted: #91a3b8;
            --accent: #2dd4bf;
            --accent-2: #38bdf8;
        }
        .stApp { background: var(--bg); color: var(--text); }
        [data-testid="stSidebar"] { background: #0a1018; border-right: 1px solid var(--border); }
        [data-testid="stSidebarNav"] { display: none; }
        [data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p:first-child {
            color: var(--text);
        }
        [data-testid="stHeader"] { background: rgba(7, 11, 16, 0.88); }
        h1, h2, h3 { color: var(--text); letter-spacing: 0; }
        p, li, .stMarkdown, label { color: var(--text); }
        .muted { color: var(--muted); }
        .hero {
            padding: 1.4rem 1.6rem;
            border: 1px solid var(--border);
            background: linear-gradient(135deg, #0d1825 0%, #101827 55%, #0d1f1d 100%);
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        .metric-card {
            padding: 1rem;
            border: 1px solid var(--border);
            background: var(--panel);
            border-radius: 8px;
            min-height: 96px;
        }
        .metric-label { color: var(--muted); font-size: 0.85rem; }
        .metric-value { color: var(--text); font-size: 1.45rem; font-weight: 700; margin-top: 0.2rem; }
        .metric-note { color: var(--muted); font-size: 0.78rem; margin-top: 0.2rem; }
        .status-ok { color: #86efac; }
        .status-missing { color: #fca5a5; }
        div[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 8px; }
        .stAlert { background: var(--panel-2); border: 1px solid var(--border); color: var(--text); }
        code { color: #7dd3fc; background: #0b1220; border: 1px solid #1e293b; border-radius: 4px; }
        hr { border-color: var(--border); margin: 1.5rem 0; }
        div[data-baseweb="select"] > div,
        div[data-baseweb="radio"] label {
            background: #0e1621;
            border-color: var(--border);
            color: var(--text);
        }
        .sidebar-title {
            font-size: 1.35rem;
            line-height: 1.2;
            font-weight: 800;
            color: var(--text);
            margin-bottom: 0.25rem;
        }
        .sidebar-subtitle {
            color: var(--muted);
            font-style: italic;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
        }
        .eyebrow {
            color: #9dd7ff;
            font-weight: 700;
            font-size: 0.9rem;
        }
        .section-panel {
            padding: 1rem 1.2rem;
            border: 1px solid var(--border);
            background: var(--panel);
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_title(title: str, caption: str | None = None) -> None:
    """Render a consistent page title."""
    st.markdown(f"## {title}")
    if caption:
        st.caption(caption)


def hero(title: str, subtitle: str, body: str | None = None) -> None:
    """Render a dark hero block."""
    content = f"<div class='hero'><h1>{title}</h1><p class='muted'>{subtitle}</p>"
    if body:
        content += f"<p>{body}</p>"
    content += "</div>"
    st.markdown(content, unsafe_allow_html=True)


def read_csv_or_message(path_value: str | Path, message: str) -> pd.DataFrame | None:
    """Read a CSV if it exists; otherwise show an informational message."""
    path = resolve_path(path_value)
    if path and path.exists():
        return pd.read_csv(path)
    if message:
        st.info(message)
    return None


def file_status(label: str, path_value: str | Path | None) -> None:
    """Show a compact generated/missing status row."""
    path = resolve_path(path_value)
    status = "Available" if path and path.exists() else "Missing"
    css = "status-ok" if status == "Available" else "status-missing"
    st.markdown(
        f"**{label}:** <span class='{css}'>{status}</span>",
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str | int | float, note: str = "") -> None:
    """Render a compact dashboard metric."""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
