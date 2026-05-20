"""Interactive and static map helpers for the Streamlit dashboard."""

from __future__ import annotations

import base64
import json
from io import BytesIO
from pathlib import Path

import folium
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import numpy as np
import rasterio
import streamlit as st
import streamlit.components.v1 as components
from folium import LayerControl
from folium.plugins import Fullscreen, MeasureControl, MiniMap
from matplotlib import colormaps
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds

from src.config import resolve_path


def _path(path_value: str | Path | None) -> Path | None:
    return resolve_path(path_value)


def _vector_fallback(path: Path) -> Path:
    if path.exists():
        return path
    if path.suffix.lower() == ".shp":
        gpkg = path.with_suffix(".gpkg")
        if gpkg.exists():
            return gpkg
    return path


def _dashboard_overlay_path(path: Path) -> tuple[Path, Path]:
    overlay_dir = resolve_path("data/processed/dashboard_layers")
    stem = path.stem
    return overlay_dir / f"{stem}.png", overlay_dir / f"{stem}.json"


def _png_data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _project_crs(configs: dict) -> str:
    return configs.get("project", {}).get("default_crs_projected", "EPSG:32631")


def _map_center(configs: dict) -> tuple[float, float]:
    center = configs.get("dashboard", {}).get("default_map", {}).get("center", [6.22, 4.72])
    return float(center[0]), float(center[1])


def empty_map(configs: dict | None = None) -> folium.Map:
    """Create the dark base map."""
    configs = configs or {}
    lat, lon = _map_center(configs)
    zoom = configs.get("dashboard", {}).get("default_map", {}).get("zoom", 10)
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
        prefer_canvas=True,
    )
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", control=True).add_to(m)
    folium.TileLayer("CartoDB positron", name="Light reference", control=True).add_to(m)
    MiniMap(toggle_display=True, tile_layer="CartoDB dark_matter").add_to(m)
    Fullscreen().add_to(m)
    MeasureControl(position="topleft").add_to(m)
    return m


def add_vector_layer(
    m: folium.Map,
    path_value: str | Path | None,
    name: str,
    color: str = "#38bdf8",
    fill_color: str | None = None,
    weight: int = 2,
    fill_opacity: float = 0.15,
    project_crs: str = "EPSG:32631",
    tooltip_fields: list[str] | None = None,
) -> bool:
    """Add a vector layer to a Folium map."""
    path = _path(path_value)
    if path:
        path = _vector_fallback(path)
    if not path or not path.exists():
        return False
    try:
        gdf = gpd.read_file(path)
        if gdf.empty:
            return False
        if gdf.crs is None:
            gdf = gdf.set_crs(project_crs, allow_override=True)
        gdf = gdf.to_crs("EPSG:4326")
        try:
            gdf["geometry"] = gdf.geometry.simplify(0.00005, preserve_topology=True)
        except Exception:
            pass
        fields = [field for field in (tooltip_fields or []) if field in gdf.columns]
        style = {
            "color": color,
            "weight": weight,
            "fillColor": fill_color or color,
            "fillOpacity": fill_opacity,
        }
        folium.GeoJson(
            gdf,
            name=name,
            style_function=lambda _feature, style=style: style,
            tooltip=folium.GeoJsonTooltip(fields=fields, aliases=fields) if fields else None,
        ).add_to(m)
        return True
    except Exception as exc:
        st.warning(f"Could not add {name}: {exc}")
        return False


def _raster_to_data_url(path: Path, cmap: str, max_size: int = 900) -> tuple[str, list[list[float]]]:
    with rasterio.open(path) as src:
        scale = max(src.width / max_size, src.height / max_size, 1)
        out_width = max(1, int(src.width / scale))
        out_height = max(1, int(src.height / scale))
        data = src.read(1, out_shape=(out_height, out_width), resampling=Resampling.nearest)
        nodata = src.nodata
        bounds = transform_bounds(src.crs, "EPSG:4326", *src.bounds, densify_pts=21)

    arr = data.astype("float32")
    mask = np.zeros(arr.shape, dtype=bool)
    if nodata is not None:
        mask |= arr == nodata
    mask |= ~np.isfinite(arr)
    valid = arr[~mask]
    if valid.size == 0:
        arr = np.zeros(arr.shape, dtype="float32")
        valid = arr.ravel()

    low, high = np.nanpercentile(valid, [2, 98])
    if high <= low:
        low, high = float(np.nanmin(valid)), float(np.nanmax(valid) or 1)
    normed = np.clip((arr - low) / (high - low if high != low else 1), 0, 1)
    rgba = colormaps.get_cmap(cmap)(normed)
    rgba[..., 3] = np.where(mask, 0, 0.72)

    image = (rgba * 255).astype("uint8")
    buffer = BytesIO()
    plt.imsave(buffer, image, format="png")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    south, west, north, east = bounds[1], bounds[0], bounds[3], bounds[2]
    return f"data:image/png;base64,{encoded}", [[south, west], [north, east]]


def add_raster_overlay(
    m: folium.Map,
    path_value: str | Path | None,
    name: str,
    cmap: str = "viridis",
    opacity: float = 0.72,
) -> bool:
    """Add a raster as a Folium image overlay."""
    path = _path(path_value)
    if not path or not path.exists():
        if path:
            png_path, meta_path = _dashboard_overlay_path(path)
            if png_path.exists() and meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    folium.raster_layers.ImageOverlay(
                        image=_png_data_url(png_path),
                        bounds=meta["bounds"],
                        name=name,
                        opacity=opacity,
                        interactive=True,
                        cross_origin=False,
                        zindex=1,
                    ).add_to(m)
                    return True
                except Exception as exc:
                    st.warning(f"Could not add PNG overlay {name}: {exc}")
        return False
    try:
        image_url, bounds = _raster_to_data_url(path, cmap)
        folium.raster_layers.ImageOverlay(
            image=image_url,
            bounds=bounds,
            name=name,
            opacity=opacity,
            interactive=True,
            cross_origin=False,
            zindex=1,
        ).add_to(m)
        return True
    except Exception as exc:
        st.warning(f"Could not add raster {name}: {exc}")
        return False


def render_map(m: folium.Map, height: int = 620) -> None:
    """Render a Folium map in Streamlit."""
    LayerControl(collapsed=False).add_to(m)
    components.html(m.get_root().render(), height=height, scrolling=False)


def _default_boundary() -> Path | None:
    return _path("data/interim/reprojected/ilaje_lga_boundary_projected.gpkg")


def _load_boundary(target_crs, boundary_path: str | Path | None = None) -> gpd.GeoDataFrame | None:
    path = _path(boundary_path) if boundary_path else _default_boundary()
    if not path or not path.exists():
        return None
    try:
        gdf = gpd.read_file(path)
        if gdf.empty:
            return None
        if gdf.crs is None and target_crs is not None:
            gdf = gdf.set_crs(target_crs, allow_override=True)
        if target_crs is not None and gdf.crs != target_crs:
            gdf = gdf.to_crs(target_crs)
        return gdf
    except Exception:
        return None


def _add_cartographic_elements(ax, bounds, crs_label: str | None = None) -> None:
    xmin, xmax, ymin, ymax = bounds
    width = xmax - xmin
    height = ymax - ymin
    ax.annotate(
        "N",
        xy=(0.94, 0.88),
        xytext=(0.94, 0.76),
        xycoords="axes fraction",
        textcoords="axes fraction",
        ha="center",
        va="center",
        fontsize=12,
        color="#111827",
        arrowprops={"arrowstyle": "-|>", "color": "#111827", "lw": 1.6},
        bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "#334155", "alpha": 0.9},
    )

    scale_km = max(1, round((width / 5) / 1000))
    scale_m = scale_km * 1000
    sx = xmin + width * 0.08
    sy = ymin + height * 0.08
    ax.plot([sx, sx + scale_m], [sy, sy], color="#111827", lw=3)
    ax.plot([sx, sx], [sy - height * 0.01, sy + height * 0.01], color="#111827", lw=2)
    ax.plot([sx + scale_m, sx + scale_m], [sy - height * 0.01, sy + height * 0.01], color="#111827", lw=2)
    ax.text(
        sx + scale_m / 2,
        sy + height * 0.025,
        f"{scale_km} km",
        ha="center",
        va="bottom",
        color="#111827",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.85},
    )
    if crs_label:
        ax.text(
            0.01,
            0.01,
            f"CRS: {crs_label}",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=8,
            color="#334155",
            bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "#cbd5e1", "alpha": 0.85},
        )


def _cmap_for_label(label: str, cmap: str, valid_values: np.ndarray):
    lower = label.lower()
    if "hazard" in lower and "classified" in lower:
        colors = ["#2c7bb6", "#abd9e9", "#ffffbf", "#fdae61", "#d7191c"]
        return ListedColormap(colors), BoundaryNorm([0.5, 1.5, 2.5, 3.5, 4.5, 5.5], 5), "Flood hazard class"
    if "stream raster" in lower or "stream order" in lower or "strahler" in lower:
        return colormaps.get_cmap("turbo"), None, label
    if "slope" in lower:
        return colormaps.get_cmap("magma"), None, "Slope score / degrees"
    if "flow accumulation" in lower:
        return colormaps.get_cmap("viridis"), None, "Flow accumulation"
    if "hillshade" in lower:
        return colormaps.get_cmap("gray"), None, "Illumination"
    return colormaps.get_cmap(cmap), None, label


def show_static_raster(path_value: str | Path | None, label: str, cmap: str = "viridis") -> None:
    """Render a cartographic static raster map."""
    path = _path(path_value)
    if path:
        path = _vector_fallback(path)
    if not path or not path.exists():
        st.info(f"{label} has not been generated yet.")
        return
    try:
        with rasterio.open(path) as src:
            data = src.read(1, masked=True)
            transform = src.transform
            bounds_obj = src.bounds
            extent = [bounds_obj.left, bounds_obj.right, bounds_obj.bottom, bounds_obj.top]
            crs_label = src.crs.to_string() if src.crs else None
            src_crs = src.crs

        arr = data.astype("float32")
        mask = np.ma.getmaskarray(data) | ~np.isfinite(np.ma.filled(arr, np.nan))
        if "stream raster" in label.lower() or "stream order" in label.lower() or "strahler" in label.lower():
            mask |= np.ma.filled(arr, 0) <= 0
        if "classified" in label.lower() and "hazard" in label.lower():
            mask |= ~np.isin(np.ma.filled(arr, 0), [1, 2, 3, 4, 5])
        arr = np.ma.array(arr, mask=mask)
        valid = arr.compressed()

        fig, ax = plt.subplots(figsize=(9, 6.2), facecolor="#f8fafc")
        ax.set_facecolor("#edf2f7")
        if valid.size:
            map_cmap, norm, colorbar_label = _cmap_for_label(label, cmap, valid)
            if norm is None and valid.size > 10:
                low, high = np.nanpercentile(valid, [2, 98])
                if high > low:
                    arr = np.ma.masked_array(np.clip(arr, low, high), mask=arr.mask)
            image = ax.imshow(arr, cmap=map_cmap, norm=norm, extent=extent, origin="upper")
            colorbar = fig.colorbar(image, ax=ax, shrink=0.72, pad=0.02)
            colorbar.set_label(colorbar_label, color="#111827", fontsize=9)
            colorbar.ax.tick_params(labelsize=8, colors="#111827")

        boundary = _load_boundary(src_crs)
        if boundary is not None:
            boundary.boundary.plot(ax=ax, color="#111827", linewidth=1.2)

        ax.set_title(label, color="#111827", fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel("Easting (m)", color="#334155", fontsize=9)
        ax.set_ylabel("Northing (m)", color="#334155", fontsize=9)
        ax.tick_params(axis="both", labelsize=8, colors="#334155")
        ax.set_aspect("equal")
        _add_cartographic_elements(ax, extent, crs_label)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except Exception as exc:
        st.warning(f"Could not render {label}: {exc}")


def show_static_vector_map(
    path_value: str | Path | None,
    label: str,
    project_crs: str = "EPSG:32631",
    column: str | None = None,
    color: str = "#38bdf8",
) -> None:
    """Render a cartographic static vector map."""
    path = _path(path_value)
    if not path or not path.exists():
        st.info(f"{label} has not been generated yet.")
        return
    try:
        gdf = gpd.read_file(path)
        if gdf.empty:
            st.info(f"{label} contains no features.")
            return
        if gdf.crs is None:
            gdf = gdf.set_crs(project_crs, allow_override=True)
        fig, ax = plt.subplots(figsize=(9, 6.2), facecolor="#f8fafc")
        ax.set_facecolor("#edf2f7")
        if column and column in gdf.columns:
            gdf.plot(column=column, ax=ax, legend=True, cmap="viridis", edgecolor="#e8f0fb", linewidth=0.6)
        else:
            gdf.plot(ax=ax, color=color, edgecolor="#111827", linewidth=0.8, alpha=0.75)
        boundary = _load_boundary(gdf.crs)
        if boundary is not None:
            boundary.boundary.plot(ax=ax, color="#111827", linewidth=1.2)
        xmin, ymin, xmax, ymax = gdf.total_bounds
        xpad = (xmax - xmin) * 0.08 or 1000
        ypad = (ymax - ymin) * 0.08 or 1000
        ax.set_xlim(xmin - xpad, xmax + xpad)
        ax.set_ylim(ymin - ypad, ymax + ypad)
        ax.set_title(label, color="#111827", fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel("Easting (m)", color="#334155", fontsize=9)
        ax.set_ylabel("Northing (m)", color="#334155", fontsize=9)
        ax.tick_params(axis="both", labelsize=8, colors="#334155")
        ax.set_aspect("equal")
        _add_cartographic_elements(ax, [xmin - xpad, xmax + xpad, ymin - ypad, ymax + ypad], gdf.crs.to_string() if gdf.crs else project_crs)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except Exception as exc:
        st.warning(f"Could not render {label}: {exc}")


def overview_map(configs: dict) -> folium.Map:
    """Create a full project overview map with available outputs."""
    data = configs["data"]
    processed = data["processed"]
    interim = data["interim"]
    m = empty_map(configs)
    add_raster_overlay(m, interim.get("corrected_dem"), "Corrected DEM", "terrain", 0.55)
    add_raster_overlay(m, processed.get("fhi_classified"), "Flood hazard class", "RdYlBu_r", 0.72)
    add_vector_layer(m, processed.get("watershed_vector"), "Watershed", "#facc15", weight=3, fill_opacity=0.04, project_crs=_project_crs(configs))
    add_vector_layer(m, processed.get("subbasins_vector"), "Sub-basins", "#22c55e", weight=2, fill_opacity=0.05, project_crs=_project_crs(configs), tooltip_fields=["subbasin_id"])
    add_vector_layer(m, processed.get("streams_vector"), "Stream network", "#38bdf8", weight=2, fill_opacity=0, project_crs=_project_crs(configs))
    add_vector_layer(m, processed.get("subbasin_priority_gpkg"), "Priority ranking", "#f97316", weight=2, fill_opacity=0.18, project_crs=_project_crs(configs), tooltip_fields=["subbasin_id", "priority_label", "priority_score"])
    return m


def show_raster_status(path_value: str, label: str, script_hint: str) -> None:
    """Show raster availability."""
    path = _path(path_value)
    if path and path.exists():
        st.success(f"{label} is available: `{path}`")
    else:
        st.info(f"Run `{script_hint}` to generate this layer.")


def show_vector_layer(path_value: str, label: str) -> None:
    """Display vector metadata."""
    path = _path(path_value)
    if path:
        path = _vector_fallback(path)
    if not path or not path.exists():
        st.info(f"Run the relevant processing script to generate {label}.")
        return
    try:
        gdf = gpd.read_file(path)
        st.write(f"**{label}:** {len(gdf):,} features")
    except Exception as exc:
        st.warning(f"Could not read {label}: {exc}")
