"""HydroMorpho-Flood Intelligence Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

import _bootstrap  # noqa: F401
from app.components.chart_helpers import bar_chart, heatmap, scatter_chart
from app.components.map_helpers import (
    add_raster_overlay,
    add_vector_layer,
    empty_map,
    render_map,
    show_static_png,
    show_static_raster,
    show_static_vector_map,
)
from app.components.ui_helpers import apply_dark_theme, file_status, hero, metric_card
from src.config import load_config_bundle, resolve_path


configs = load_config_bundle("config")
dashboard = configs["dashboard"]
project = configs["project"]
data = configs["data"]
raw = data["raw"]
interim = data["interim"]
processed = data["processed"]
project_crs = project.get("default_crs_projected", "EPSG:32631")


st.set_page_config(
    page_title=dashboard["title"],
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_dark_theme()


def read_table(path_value: str | Path | None, valid_hazard: bool = False) -> pd.DataFrame | None:
    """Read a CSV output if available."""
    path = resolve_path(path_value)
    if not path or not path.exists():
        return None
    df = pd.read_csv(path)
    if valid_hazard and "hazard_class" in df.columns:
        df = df[df["hazard_class"].between(1, 5)]
    return df


hazard_df = read_table(processed.get("hazard_area_summary_csv"), valid_hazard=True)
morph_df = read_table(processed.get("subbasin_morphometry_csv"))
priority_df = read_table(processed.get("subbasin_priority_csv"))


def sidebar() -> str:
    """Render custom sidebar navigation."""
    st.sidebar.markdown(
        f"""
        <div class="sidebar-title">HydroMorpho-Flood<br/>Intelligence</div>
        <div class="sidebar-subtitle">{project.get("study_area_name")} - {project.get("state")}, {project.get("country")}</div>
        """,
        unsafe_allow_html=True,
    )
    views = [
        "Overview & Statistics",
        "Interactive Web Maps",
        "Static Maps",
        "Hydrology Outputs",
        "Watershed & Morphometry",
        "Flood Hazard Index",
        "Sub-Basin Prioritization",
        "Lineament Integration",
    ]
    selected = st.sidebar.selectbox("View", views, index=0)
    st.sidebar.divider()
    st.sidebar.markdown("### About")
    st.sidebar.write(
        "DEM-based hydrology, morphometry, flood susceptibility, and priority ranking for Ilaje LGA."
    )
    repo_url = project.get("github_repo_url")
    if repo_url:
        st.sidebar.markdown(f"[GitHub Repository]({repo_url})")
    st.sidebar.divider()
    st.sidebar.caption("Dashboard reads generated outputs only. Run GIS scripts manually before deployment.")
    return selected


def kpi_strip() -> None:
    """Render top KPI cards."""
    hazard_area = hazard_df["area_km2"].sum() if hazard_df is not None and "area_km2" in hazard_df else None
    high_area = None
    high_pct = None
    if hazard_df is not None:
        high_rows = hazard_df[hazard_df["hazard_label"].isin(["High", "Very High"])]
        high_area = high_rows["area_km2"].sum()
        if hazard_area:
            high_pct = high_area / hazard_area * 100
    cols = st.columns(5)
    with cols[0]:
        metric_card("Study area", f"{hazard_area:,.1f} km2" if hazard_area else "Pending")
    with cols[1]:
        dd = morph_df["drainage_density_km_per_km2"].mean() if morph_df is not None else None
        metric_card("Mean drainage density", f"{dd:.3f}" if dd is not None else "Pending")
    with cols[2]:
        mean_fhi = None
        if priority_df is not None and "fhi_mean" in priority_df:
            mean_fhi = priority_df["fhi_mean"].mean()
        metric_card("Mean FHI", f"{mean_fhi:.3f}" if mean_fhi is not None else "Pending")
    with cols[3]:
        metric_card(
            "High + Very High",
            f"{high_area:,.1f} km2" if high_area is not None else "Pending",
            f"{high_pct:.1f}% of mapped area" if high_pct is not None else "",
        )
    with cols[4]:
        top = "Pending"
        if priority_df is not None and "priority_label" in priority_df.columns:
            top = priority_df.sort_values("priority_rank").iloc[0]["priority_label"]
        metric_card("Top priority", top)


def weights_chart() -> None:
    """Render enabled MCDA factor weights."""
    factors = configs["flood"]["factors"]
    rows = [
        {"factor": name.replace("_", " "), "weight": spec.get("weight", 0)}
        for name, spec in factors.items()
        if spec.get("enabled", False)
    ]
    if not rows:
        return
    df = pd.DataFrame(rows).sort_values("weight")
    fig = px.bar(
        df,
        x="weight",
        y="factor",
        orientation="h",
        text=df["weight"].map(lambda value: f"{value:.0%}"),
        title="Flood factor weights",
        template="plotly_dark",
        color_discrete_sequence=["#1f9d78"],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(paper_bgcolor="#070b10", plot_bgcolor="#0e1621", font_color="#e8f0fb")
    st.plotly_chart(fig, use_container_width=True)


def section_overview() -> None:
    hero(
        dashboard["title"],
        f"{project.get('study_area_name')} - {project.get('state')}, {project.get('country')} | DEM hydrology | MCDA flood hazard | UTM Zone 31N",
        dashboard.get("project_text", {}).get("home_summary", ""),
    )
    kpi_strip()
    st.divider()
    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("### Flood hazard class distribution")
        if hazard_df is not None:
            chart_df = hazard_df.copy()
            total = chart_df["area_km2"].sum()
            chart_df["share_pct"] = chart_df["area_km2"] / total * 100 if total else 0
            fig = px.bar(
                chart_df,
                x="area_km2",
                y="hazard_label",
                orientation="h",
                text=chart_df["share_pct"].map(lambda value: f"{value:.1f}%"),
                color="hazard_label",
                title="Area by flood hazard class",
                template="plotly_dark",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(paper_bgcolor="#070b10", plot_bgcolor="#0e1621", font_color="#e8f0fb")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Run scripts 09 and 10 to generate flood hazard statistics.")
    with right:
        st.markdown("### MCDA factor weights")
        weights_chart()
    st.divider()
    st.markdown("### Results Tables and Downloads")
    render_downloads_and_tables(expanded=True)


def section_interactive_maps() -> None:
    st.markdown("# Interactive Web Maps")
    st.caption("Toggle layers, zoom, inspect overlays, and switch base maps.")
    map_mode = st.selectbox(
        "Map focus",
        ["Flood hazard and drainage", "Hydrology", "Watershed and priority", "Study area and LULC"],
    )
    m = empty_map(configs)
    if map_mode == "Flood hazard and drainage":
        add_raster_overlay(m, processed["fhi_classified"], "Classified flood hazard", "RdYlBu_r", 0.78)
        add_raster_overlay(m, processed["fhi_continuous"], "Continuous FHI", "inferno", 0.5)
        add_vector_layer(m, processed["streams_vector"], "Stream network", "#38bdf8", weight=2, fill_opacity=0, project_crs=project_crs)
        add_vector_layer(m, processed["watershed_vector"], "Watershed", "#facc15", weight=3, fill_opacity=0.04, project_crs=project_crs)
    elif map_mode == "Hydrology":
        add_raster_overlay(m, interim["flow_accumulation"], "Flow accumulation", "viridis", 0.7)
        add_raster_overlay(m, interim["stream_raster"], "Stream raster", "Blues", 0.65)
        add_raster_overlay(m, interim["strahler_order"], "Strahler order", "plasma", 0.65)
        add_vector_layer(m, processed["streams_vector"], "Stream network", "#38bdf8", weight=2, fill_opacity=0, project_crs=project_crs)
    elif map_mode == "Watershed and priority":
        add_raster_overlay(m, processed["fhi_classified"], "Flood hazard", "RdYlBu_r", 0.55)
        add_vector_layer(m, processed["subbasin_priority_gpkg"], "Priority ranking", "#f97316", weight=3, fill_opacity=0.22, project_crs=project_crs, tooltip_fields=["subbasin_id", "priority_label", "priority_score"])
        add_vector_layer(m, processed["subbasins_vector"], "Sub-basins", "#22c55e", weight=2, fill_opacity=0.08, project_crs=project_crs, tooltip_fields=["subbasin_id"])
    else:
        add_raster_overlay(m, raw["lulc"], "ESA WorldCover LULC", "tab20", 0.65)
        add_raster_overlay(m, interim["corrected_dem"], "Corrected DEM", "terrain", 0.45)
        add_vector_layer(m, interim["study_area_projected"], "Ilaje LGA boundary", "#facc15", weight=3, fill_opacity=0.05, project_crs=project_crs)
    render_map(m, height=700)


def section_static_maps() -> None:
    st.markdown("# Static Maps")
    st.caption("Report-ready previews for terrain, hydrology, flood hazard, and priority outputs.")
    tabs = st.tabs(["Terrain", "Hydrology", "Hazard", "Priority"])
    with tabs[0]:
        cols = st.columns(3)
        with cols[0]:
            show_static_png("outputs/figures/dem_preview.png", "Corrected DEM")
        with cols[1]:
            show_static_raster(f"{interim['terrain_dir']}/hillshade.tif", "Hillshade", "gray")
        with cols[2]:
            show_static_png("outputs/figures/slope_preview.png", "Slope")
    with tabs[1]:
        cols = st.columns(3)
        with cols[0]:
            show_static_png("outputs/figures/flow_accumulation_preview.png", "Flow Accumulation")
        with cols[1]:
            show_static_png("outputs/maps/stream_network.png", "Stream Network")
        with cols[2]:
            show_static_png("outputs/maps/stream_order_strahler.png", "Strahler Stream Order")
    with tabs[2]:
        cols = st.columns(2)
        with cols[0]:
            show_static_png("outputs/maps/flood_hazard_index.png", "Flood Hazard Index")
        with cols[1]:
            show_static_vector_map(processed["fhi_zones_vector"], "Flood Hazard Zones", project_crs, column="hazard_class")
    with tabs[3]:
        cols = st.columns(2)
        with cols[0]:
            show_static_png("outputs/maps/subbasins.png", "Sub-Basins")
        with cols[1]:
            show_static_png("outputs/maps/subbasin_priority.png", "Sub-Basin Priority")


def section_data() -> None:
    st.markdown("# Study Area and Data")
    m = empty_map(configs)
    add_vector_layer(m, interim["study_area_projected"], "Ilaje boundary", "#facc15", weight=3, fill_opacity=0.08, project_crs=project_crs)
    add_raster_overlay(m, raw["lulc"], "ESA WorldCover", "tab20", 0.6)
    add_vector_layer(m, processed["streams_vector"], "Extracted streams", "#38bdf8", weight=2, fill_opacity=0, project_crs=project_crs)
    render_map(m, height=560)
    left, right = st.columns(2)
    with left:
        st.markdown("### Core datasets")
        file_status("Ilaje LGA boundary", raw["study_area_boundary"])
        file_status("DEM raster", raw["dem"])
        file_status("ESA WorldCover LULC", raw["lulc"])
        file_status("Outlet / pour points", raw.get("outlet_points"))
    with right:
        st.markdown("### Optional datasets")
        for key in ["soils", "hydrography_reference", "lineaments", "settlements", "roads", "population"]:
            file_status(key.replace("_", " ").title(), raw.get(key))


def section_hydrology() -> None:
    st.markdown("# Hydrology Outputs")
    m = empty_map(configs)
    add_raster_overlay(m, interim["flow_accumulation"], "Flow accumulation", "viridis", 0.7)
    add_raster_overlay(m, interim["strahler_order"], "Strahler order", "plasma", 0.6)
    add_vector_layer(m, processed["streams_vector"], "Stream network", "#38bdf8", weight=2, fill_opacity=0, project_crs=project_crs)
    add_vector_layer(m, processed["watershed_vector"], "Watershed", "#facc15", weight=3, fill_opacity=0.03, project_crs=project_crs)
    render_map(m, height=620)
    cols = st.columns(3)
    with cols[0]:
        show_static_png("outputs/figures/dem_preview.png", "Corrected DEM")
    with cols[1]:
        show_static_png("outputs/figures/flow_accumulation_preview.png", "Flow Accumulation")
    with cols[2]:
        show_static_png("outputs/maps/stream_order_strahler.png", "Strahler Order")


def section_morphometry() -> None:
    st.markdown("# Watershed and Morphometry")
    m = empty_map(configs)
    add_vector_layer(m, processed["watershed_vector"], "Watershed", "#facc15", weight=3, fill_opacity=0.04, project_crs=project_crs)
    add_vector_layer(m, processed["subbasins_vector"], "Sub-basins", "#22c55e", weight=2, fill_opacity=0.12, project_crs=project_crs, tooltip_fields=["subbasin_id"])
    add_vector_layer(m, processed["streams_vector"], "Stream network", "#38bdf8", weight=2, fill_opacity=0, project_crs=project_crs)
    render_map(m, height=560)
    if morph_df is None:
        st.info("Run script 07 to generate morphometric outputs.")
        return
    cols = st.columns(4)
    with cols[0]:
        metric_card("Area", f"{morph_df['area_km2'].sum():.1f} km2")
    with cols[1]:
        metric_card("Drainage density", f"{morph_df['drainage_density_km_per_km2'].mean():.3f}")
    with cols[2]:
        metric_card("Stream frequency", f"{morph_df['stream_frequency_no_per_km2'].mean():.3f}")
    with cols[3]:
        metric_card("Relief", f"{morph_df['basin_relief_m'].mean():.1f} m")
    st.dataframe(morph_df, use_container_width=True, hide_index=True)
    left, right = st.columns(2)
    with left:
        bar_chart(morph_df, "subbasin_id", "drainage_density_km_per_km2", "Drainage Density")
    with right:
        scatter_chart(morph_df, "drainage_density_km_per_km2", "ruggedness_number", title="Drainage Density vs Ruggedness")
    heatmap(morph_df, "Morphometric Correlation Heatmap")


def section_hazard() -> None:
    st.markdown("# Flood Hazard Index")
    m = empty_map(configs)
    add_raster_overlay(m, processed["fhi_classified"], "Classified flood hazard", "RdYlBu_r", 0.78)
    add_vector_layer(m, processed["streams_vector"], "Stream network", "#38bdf8", weight=2, fill_opacity=0, project_crs=project_crs)
    add_vector_layer(m, processed["watershed_vector"], "Watershed", "#facc15", weight=3, fill_opacity=0.03, project_crs=project_crs)
    render_map(m, height=620)
    if hazard_df is None:
        st.info("Run scripts 09 and 10 to generate flood hazard outputs.")
        return
    cols = st.columns(3)
    with cols[0]:
        metric_card("Mapped hazard area", f"{hazard_df['area_km2'].sum():.1f} km2")
    with cols[1]:
        largest = hazard_df.sort_values("area_km2", ascending=False).iloc[0]
        metric_card("Dominant class", largest["hazard_label"], f"{largest['area_km2']:.1f} km2")
    with cols[2]:
        metric_card("Classes", len(hazard_df))
    bar_chart(hazard_df, "hazard_label", "area_km2", "Hazard Area by Class", color="hazard_label")
    st.dataframe(hazard_df, use_container_width=True, hide_index=True)


def section_priority() -> None:
    st.markdown("# Sub-Basin Prioritization")
    m = empty_map(configs)
    add_raster_overlay(m, processed["fhi_classified"], "Flood hazard class", "RdYlBu_r", 0.6)
    add_vector_layer(m, processed["subbasin_priority_gpkg"], "Priority ranking", "#f97316", weight=3, fill_opacity=0.22, project_crs=project_crs, tooltip_fields=["subbasin_id", "priority_label", "priority_score"])
    render_map(m, height=620)
    if priority_df is None:
        st.info("Run script 11 to generate priority outputs.")
        return
    ranked = priority_df.sort_values("priority_rank")
    cols = st.columns(3)
    with cols[0]:
        metric_card("Ranked units", len(ranked))
    with cols[1]:
        metric_card("Highest priority", ranked.iloc[0].get("priority_label", "N/A"))
    with cols[2]:
        metric_card("Top score", f"{ranked.iloc[0].get('priority_score', 0):.3f}")
    bar_chart(ranked, "subbasin_id", "priority_score", "Priority Score by Sub-Basin", color="priority_label")
    st.dataframe(ranked, use_container_width=True, hide_index=True)


def section_lineaments() -> None:
    st.markdown("# Lineament Integration")
    st.caption("Optional structural drainage interpretation. Not required for the DEM/LULC flood model.")
    m = empty_map(configs)
    add_raster_overlay(m, processed["lineament_density_raster"], "Lineament density", "inferno", 0.7)
    add_vector_layer(m, raw.get("lineaments"), "Imported lineaments", "#f97316", weight=2, fill_opacity=0, project_crs=project_crs)
    add_vector_layer(m, processed["streams_vector"], "Stream network", "#38bdf8", weight=2, fill_opacity=0, project_crs=project_crs)
    render_map(m, height=560)
    lineament_stats = read_table(processed.get("lineament_stats_csv"))
    if lineament_stats is not None:
        st.dataframe(lineament_stats, use_container_width=True, hide_index=True)
    else:
        st.info("No lineament vector was supplied. This section will populate after script 08 is run with lineament data.")


def render_downloads_and_tables(expanded: bool = False) -> None:
    """Render CSV result tables and download buttons."""
    for label, path_value in processed.items():
        path = resolve_path(path_value)
        if path and path.exists() and path.suffix.lower() == ".csv":
            with st.expander(
                label.replace("_", " ").title(),
                expanded=expanded and label in {"hazard_area_summary_csv", "subbasin_priority_csv"},
            ):
                df = read_table(path)
                if df is not None:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.download_button(f"Download {path.name}", df.to_csv(index=False), file_name=path.name, mime="text/csv")
    st.markdown("### Spatial output paths")
    for label, path_value in processed.items():
        path = resolve_path(path_value)
        if path and path.exists() and path.suffix.lower() != ".csv":
            st.write(f"**{label.replace('_', ' ').title()}:** `{path}`")


def section_downloads() -> None:
    st.markdown("# Downloads and Tables")
    render_downloads_and_tables(expanded=True)


def section_about() -> None:
    hero(
        project.get("project_name", "HydroMorpho-Flood Intelligence System"),
        project.get("project_subtitle", ""),
        "Reusable GIS and Python workflow for watershed intelligence and flood-susceptibility mapping.",
    )
    st.markdown("### Project Purpose")
    st.write(
        "This dashboard communicates outputs from a configurable pipeline that preprocesses DEM data, models drainage flow, "
        "extracts streams, computes morphometric indicators, integrates optional structural drainage evidence, "
        "builds a multi-criteria flood hazard index, and ranks sub-basins for planning attention."
    )
    repo_url = project.get("github_repo_url")
    if repo_url:
        st.link_button("Open GitHub Repository", repo_url)
    st.markdown("### Streamlit Cloud")
    st.write(
        "The app is Cloud-compatible when generated outputs are committed or replaced with lightweight sample outputs. "
        "Heavy GIS processing is intentionally kept outside the dashboard."
    )


view = sidebar()

if view == "Overview & Statistics":
    section_overview()
elif view == "Interactive Web Maps":
    section_interactive_maps()
elif view == "Static Maps":
    section_static_maps()
elif view == "Hydrology Outputs":
    section_hydrology()
elif view == "Watershed & Morphometry":
    section_morphometry()
elif view == "Flood Hazard Index":
    section_hazard()
elif view == "Sub-Basin Prioritization":
    section_priority()
elif view == "Lineament Integration":
    section_lineaments()
else:
    section_overview()
