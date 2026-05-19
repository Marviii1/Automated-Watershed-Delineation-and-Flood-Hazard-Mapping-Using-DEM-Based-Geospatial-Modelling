# HydroMorpho-Flood Intelligence System

Automated Watershed Delineation, Morphometric Characterization, Structural Drainage Analysis, and Flood Hazard Mapping Using DEM-Based Geospatial Modelling.

This repository is a reproducible Python-first geospatial analysis pipeline for Ilaje LGA, Ondo State, Nigeria. Every path, CRS, processing threshold, ranking rule, and flood-hazard weight is controlled through YAML configuration files so the workflow can still be reused for other study areas.

## Problem Statement

Watershed flood response is controlled by terrain, drainage structure, basin geometry, land cover, soil response, and possible structural controls on drainage alignment. Many GIS workflows handle these components as disconnected manual steps. This project provides an end-to-end, scriptable workflow that transforms DEM and optional thematic datasets into hydrological products, morphometric tables, flood hazard rasters, sub-basin priority rankings, maps, charts, reports, and a Streamlit review dashboard.

## Goals

- Prepare and hydrologically correct DEM data.
- Generate D8 flow direction, flow accumulation, stream networks, and stream order products.
- Delineate watershed and sub-basins from supplied or snapped pour points.
- Compute basin and sub-basin morphometric indicators.
- Integrate drainage outputs with optional lineament data using cautious structural-hydrology language.
- Build configurable flood hazard index rasters using weighted overlay / MCDA.
- Rank sub-basins by flood susceptibility and morphometric runoff indicators.
- Produce report-ready maps, charts, tables, and a Streamlit dashboard.

## Use Your Existing GIS Environment

Do not create a new environment for this repository unless you choose to. The project is designed to run inside your existing GIS Python environment, for example:

```bash
conda activate gis_env
```

`requirements.txt` lists likely dependencies for reference only. Install or adjust packages manually in your own environment if needed.

## Repository Structure

```text
hydromorpho-flood-intelligence/
|-- Makefile
|-- config/                 # YAML configuration files
|-- data/                   # raw, interim, and processed data folders
|-- outputs/                # maps, charts, figures, reports, logs
|-- scripts/                # numbered CLI workflow scripts
|-- src/                    # reusable Python modules
|-- notebooks/              # lightweight review notebooks
|-- app/                    # Streamlit dashboard
`-- docs/                   # methodology and execution documentation
```

## Required Datasets for Ilaje LGA

Minimum required inputs:

- Ilaje LGA study area boundary polygon: Shapefile, GeoPackage, or GeoJSON. The default path is `data/raw/boundary/ilaje_lga_boundary.shp`.
- DEM raster covering Ilaje LGA, preferably with a small buffer beyond the boundary. The default path is `data/raw/dem/ilaje_dem.tif`.
- Outlet / pour point layer for watershed delineation. The default path is `data/raw/outlets/ilaje_outlets.gpkg`.

Optional inputs:

- Land use / land cover raster.
- Soil texture, permeability, hydrologic soil group, or runoff proxy.
- Reference hydrography for validation.
- Lineament vectors from geological mapping, remote sensing, or manual digitization.
- Roads, settlements, and population data for exposure interpretation.

Update [config/data_paths.yml](config/data_paths.yml) before running.

See [docs/ilaje_dataset_requirements_and_pipeline.md](docs/ilaje_dataset_requirements_and_pipeline.md) for the full dataset checklist and execution pipeline.

## Manual Execution Order

Run the scripts manually from the repository root:

```bash
python scripts/01_validate_project_inputs.py
python scripts/02_prepare_study_area_and_dem.py
python scripts/03_preprocess_dem.py
python scripts/04_generate_flow_direction_and_accumulation.py
python scripts/05_extract_stream_network.py
python scripts/06_delineate_watershed_and_subbasins.py
python scripts/07_compute_morphometric_parameters.py
python scripts/08_lineament_drainage_analysis.py
python scripts/09_prepare_flood_hazard_factors.py
python scripts/10_compute_flood_hazard_index.py
python scripts/11_rank_subbasins.py
python scripts/12_generate_maps_charts_and_summary_outputs.py
python scripts/13_generate_report_assets.py
```

Then launch the dashboard:

```bash
streamlit run app/streamlit_app.py
```

Each script accepts optional config arguments. Example:

```bash
python scripts/10_compute_flood_hazard_index.py --config-dir config
```

The Makefile mirrors the same script names and does not install packages, create environments, or download data:

```bash
make all
make dashboard
```

## Expected Outputs

- Hydrologically corrected DEM, hillshade, slope, aspect, and optional terrain derivatives.
- D8 flow direction and accumulation rasters.
- Stream network rasters and vector layers.
- Strahler and optional Shreve stream order outputs.
- Watershed and sub-basin polygons.
- Basin and sub-basin morphometric CSV tables.
- Lineament density, lineament statistics, and drainage-lineament intersection outputs where lineaments are supplied.
- Reclassified flood conditioning factor rasters.
- Continuous and classified flood hazard index rasters.
- Hazard zones vector layer where vectorization is enabled.
- Hazard area summaries and sub-basin zonal statistics.
- Ranked sub-basin CSV and GeoPackage outputs.
- Maps, figures, charts, and Markdown report assets.

## Methodological Overview

The pipeline uses WhiteboxTools for hydrological DEM conditioning, D8 flow routing, accumulation, stream extraction, stream ordering, watershed delineation, and selected terrain products. Python geospatial libraries handle configuration, validation, clipping, reprojection, vector operations, raster alignment, morphometric formulas, weighted overlay, summaries, visualization, and dashboard rendering.

Flood hazard modelling uses configurable reclassification rules and weights:

```text
Flood Hazard Index = sum(weight_i * reclassified_factor_i)
```

All factors are expected to be aligned to a common CRS, extent, transform, and resolution before weighted overlay.

## Dashboard

The Streamlit dashboard reads generated outputs only. It does not perform heavy GIS processing. If an output is missing, pages show clear guidance such as "Run script 10_compute_flood_hazard_index.py to generate this layer."

For Streamlit Cloud deployment, commit the dashboard files, `requirements.txt`, `packages.txt`, `.streamlit/config.toml`, and whichever generated lightweight outputs you want the deployed app to display. Update `github_repo_url` in [config/project_config.yml](config/project_config.yml) after creating your GitHub repository.

## Limitations

- Automated lineament extraction is treated as a semi-automated scaffold because robust structural interpretation normally requires expert review and validation.
- DEM resolution, sink treatment, stream extraction thresholds, and pour point accuracy strongly affect drainage products.
- Flood hazard outputs are susceptibility indices, not hydraulic inundation model results.
- LULC and soil factors depend on local class definitions and must be configured carefully.
- Morphometric rankings are decision-support indicators and should be validated against observed flood records where possible.

## Future Improvements

- Add calibration against observed stream networks and flood inventory points.
- Add HAND, rainfall intensity, curve number, or hydrodynamic model coupling.
- Add automated AHP pairwise comparison templates.
- Add richer uncertainty reporting for DEM resolution, threshold sensitivity, and factor weights.
- Add batch processing for multiple basins.

## Portfolio and Research Relevance

This repository demonstrates a complete geospatial analytics workflow: terrain preprocessing, hydrologic modelling, morphometric science, structural drainage interpretation, MCDA flood susceptibility modelling, reproducible engineering practices, and interactive communication of results.
