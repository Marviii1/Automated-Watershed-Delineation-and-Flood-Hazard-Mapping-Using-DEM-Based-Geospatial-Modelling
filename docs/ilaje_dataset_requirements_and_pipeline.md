# Ilaje LGA Dataset Requirements and Execution Pipeline

This project is now configured for Ilaje Local Government Area, Ondo State, Nigeria. Use your Ilaje LGA shapefile as the study-area boundary and keep every raster/vector input large enough to cover the full LGA before clipping.

## 1. Required Datasets

| Dataset | Required path in config | Accepted format | Purpose |
| --- | --- | --- | --- |
| Ilaje LGA boundary | `data/raw/boundary/ilaje_lga_boundary.shp` | Shapefile, GeoPackage, GeoJSON | Study-area mask for every analysis output |
| DEM | `data/raw/dem/ilaje_dem.tif` | GeoTIFF | Terrain, flow direction, flow accumulation, drainage extraction, watershed/subbasins |
| Outlet or pour points | `data/raw/outlets/ilaje_outlets.gpkg` | GeoPackage, Shapefile, GeoJSON | Watershed/subbasin delineation control points |

For the shapefile boundary, keep these files together in `data/raw/boundary/`:

- `ilaje_lga_boundary.shp`
- `ilaje_lga_boundary.shx`
- `ilaje_lga_boundary.dbf`
- `ilaje_lga_boundary.prj`

Recommended DEM sources include Copernicus DEM, NASADEM/SRTM, ALOS PALSAR DEM, or any locally validated DEM. For Ilaje's coastal terrain, a cleaner and higher-resolution DEM will usually improve drainage and flood-susceptibility outputs.

## 2. Optional Datasets

| Dataset | Config path | Purpose |
| --- | --- | --- |
| LULC raster | `data/raw/lulc/lulc.tif` | Flood-hazard conditioning factor |
| Soil / hydrologic soil group raster | `data/raw/soils/soils.tif` | Infiltration/runoff proxy |
| Reference hydrography | `data/raw/hydrography_reference/reference_streams.gpkg` | Validation against extracted DEM streams |
| Lineaments | `data/raw/lineaments_optional/lineaments.gpkg` | Structural drainage interpretation |
| Roads | `data/raw/roads_optional/roads.gpkg` | Exposure/context mapping |
| Settlements | `data/raw/settlements_optional/settlements.gpkg` | Exposure/context mapping |
| Population raster | `data/raw/population_optional/population.tif` | Exposure summaries |

Optional datasets can be added later. The pipeline warns when they are missing and skips the optional analysis that depends on them.

The LULC configuration is set for ESA WorldCover class codes: `10` tree cover, `20` shrubland, `30` grassland, `40` cropland, `50` built-up, `60` bare/sparse vegetation, `80` water, `90` herbaceous wetland, and `95` mangroves. For Ilaje, water, wetlands, and mangroves are scored as high flood-susceptibility LULC classes.

## 3. CRS and Study Area Setup

The default projected CRS is `EPSG:32631` because Ilaje LGA lies in UTM Zone 31N. Keep source data in their native CRS if needed; the pipeline clips/reprojects working outputs into the configured CRS.

Before running, confirm:

- The Ilaje boundary contains Polygon or MultiPolygon geometry.
- The boundary has a valid CRS.
- The DEM covers the whole LGA, with some buffer beyond the boundary if possible.
- Outlet points fall on or near the DEM-derived drainage network.
- Optional rasters either cover the LGA or can be clipped to it.

## 4. Folder Placement

Place inputs here unless you prefer to edit `config/data_paths.yml`:

```text
data/raw/boundary/ilaje_lga_boundary.shp
data/raw/boundary/ilaje_lga_boundary.shx
data/raw/boundary/ilaje_lga_boundary.dbf
data/raw/boundary/ilaje_lga_boundary.prj
data/raw/dem/ilaje_dem.tif
data/raw/outlets/ilaje_outlets.gpkg
data/raw/lulc/lulc.tif
data/raw/soils/soils.tif
```

## 5. Execution Pipeline

Run from the repository root in your GIS Python environment:

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

Do not run installation commands from this project unless you personally decide your existing GIS environment needs missing packages.

## 6. Outputs to Check First

After scripts 1-5, inspect:

- `data/interim/reprojected/ilaje_lga_boundary_projected.gpkg`
- `data/interim/clipped/dem_clipped.tif`
- `data/interim/hydrology/dem_hydro_corrected.tif`
- `data/interim/hydrology/d8_flow_accumulation_cells.tif`
- `data/processed/vectors/stream_network.shp`

For Ilaje, stream extraction thresholds may need tuning because low-relief coastal terrain can create broad accumulation zones. Adjust `stream_extraction_threshold_cells` in `config/hydrology_config.yml`, rerun scripts 5 onward, and compare against reference hydrography or high-resolution imagery.

## 7. Main Config Files to Edit

- `config/data_paths.yml`: file paths for boundary, DEM, outlets, and optional datasets.
- `config/project_config.yml`: study-area label and CRS.
- `config/hydrology_config.yml`: stream threshold, pour-point snapping, DEM conditioning.
- `config/flood_hazard_config.yml`: flood-factor weights and reclassification rules.
- `config/dashboard_config.yml`: dashboard title, map center, and displayed output paths.
