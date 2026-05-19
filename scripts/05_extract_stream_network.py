"""Extract stream network and stream order products."""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.config import load_config_bundle
from src.hydrology import extract_streams, stream_order, stream_to_vector
from src.logging_utils import setup_logging
from src.preflight import require_existing_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract stream network.")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    logger = setup_logging("05_extract_stream_network")
    configs = load_config_bundle(args.config_dir)
    data = configs["data"]
    hyd = configs["hydrology"]
    interim = data["interim"]
    require_existing_paths(
        {"flow accumulation": interim["flow_accumulation"], "flow direction": interim["flow_direction"]},
        logger,
        "Run script 04_generate_flow_direction_and_accumulation.py first.",
    )

    extract_streams(
        interim["flow_accumulation"],
        interim["stream_raster"],
        hyd["stream_extraction_threshold_cells"],
        hyd["whitebox"]["working_dir"],
        logger,
    )
    stream_to_vector(
        interim["stream_raster"],
        interim["flow_direction"],
        data["processed"]["streams_vector"],
        hyd["whitebox"]["working_dir"],
        logger,
    )
    for method in hyd.get("stream_order_methods", []):
        output = interim["strahler_order"] if method == "strahler" else interim["shreve_order"]
        stream_order(
            interim["stream_raster"],
            interim["flow_direction"],
            output,
            method,
            hyd["whitebox"]["working_dir"],
            logger,
        )
    logger.info("Stream extraction completed.")


if __name__ == "__main__":
    main()
