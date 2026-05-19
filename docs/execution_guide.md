# Execution Guide

This repository is designed for manual execution in your existing GIS Python environment.

## 1. Activate Your Existing Environment

Example:

```bash
conda activate gis_env
```

Do not run installation commands from this guide unless you personally decide your environment needs missing packages.

## 2. Add Input Data

Place your datasets into `data/raw/` or update `config/data_paths.yml` to point to their actual locations. The current defaults target Ilaje LGA:

Minimum required:

- Ilaje LGA boundary polygon: `data/raw/boundary/ilaje_lga_boundary.shp`.
- DEM raster covering the full LGA: `data/raw/dem/ilaje_dem.tif`.
- Outlet / pour point layer: `data/raw/outlets/ilaje_outlets.gpkg`.

For a shapefile boundary, keep `.shp`, `.shx`, `.dbf`, and `.prj` files together.

## 3. Review Config Files

Update:

- `config/project_config.yml` for CRS and study area labels.
- `config/data_paths.yml` for input and output paths.
- `config/hydrology_config.yml` for DEM conditioning method and stream threshold.
- `config/morphometry_config.yml` for field names and metrics.
- `config/flood_hazard_config.yml` for factor rules and weights.
- `config/dashboard_config.yml` for dashboard labels and display layers.

## 4. Run Scripts in Order

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

## 5. Launch Dashboard

```bash
streamlit run app/streamlit_app.py
```

The dashboard reads existing outputs. It does not run heavy processing.

## 6. Optional Makefile Commands

The Makefile mirrors the numbered scripts and does not install packages, create environments, or download datasets:

```bash
make validate
make prepare-dem
make preprocess-dem
make flow
make streams
make watershed
make morphometry
make lineaments
make flood-factors
make flood-index
make rank
make maps
make report
make all
make dashboard
```

## 7. Recommended Quality Checks

- Compare extracted streams against reference hydrography.
- Test multiple stream extraction thresholds.
- Verify pour point placement.
- Confirm LULC and soil reclassification meanings.
- Review hazard weights and document expert assumptions.
- Validate priority outputs against known flood-prone areas where records exist.
