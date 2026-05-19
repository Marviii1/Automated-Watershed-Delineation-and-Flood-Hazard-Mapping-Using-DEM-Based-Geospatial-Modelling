"""Hydrological modelling output dashboard page."""

from __future__ import annotations

import _bootstrap  # noqa: F401
from app.components.map_helpers import show_raster_status, show_vector_layer
from app.components.ui_helpers import page_title
from src.config import load_config_bundle

configs = load_config_bundle("config")
data = configs["data"]
page_title("Hydrology Outputs")
show_raster_status(data["interim"]["flow_accumulation"], "Flow accumulation", "scripts/04_generate_flow_direction_and_accumulation.py")
show_raster_status(data["interim"]["stream_raster"], "Stream raster", "scripts/05_extract_stream_network.py")
show_vector_layer(data["processed"]["streams_vector"], "Stream network")
