"""Generate report-friendly Markdown summary assets."""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.config import load_config_bundle
from src.logging_utils import setup_logging
from src.reporting import generate_markdown_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate report assets.")
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    logger = setup_logging("13_generate_report_assets")
    configs = load_config_bundle(args.config_dir)
    output = f"{configs['data']['outputs']['reports_dir']}/hydromorpho_summary_report.md"
    generate_markdown_report(configs, output)
    logger.info("Markdown report written: %s", output)


if __name__ == "__main__":
    main()
