# Outputs Catalog

## Script 01: Validate Inputs

Creates log output only. Confirms required inputs and warns about missing optional datasets.

## Script 02: Prepare Study Area and DEM

- `data/interim/clipped/dem_clipped.tif`
- `data/interim/reprojected/dem_projected.tif`

## Script 03: Preprocess DEM

- `data/interim/hydrology/dem_hydro_corrected.tif`
- `data/interim/terrain/slope_degrees.tif`
- `data/interim/terrain/aspect_degrees.tif`
- `data/interim/terrain/hillshade.tif`

## Script 04: Flow Direction and Accumulation

- `data/interim/hydrology/d8_pointer.tif`
- `data/interim/hydrology/d8_flow_accumulation_cells.tif`

## Script 05: Stream Network

- `data/interim/hydrology/streams_thresholded.tif`
- `data/processed/vectors/stream_network.gpkg`
- `data/interim/hydrology/stream_order_strahler.tif`
- `data/interim/hydrology/stream_order_shreve.tif`

## Script 06: Watershed and Sub-Basins

- `data/interim/hydrology/watershed.tif`
- `data/processed/vectors/watershed.gpkg`
- `data/processed/vectors/subbasins.gpkg`

## Script 07: Morphometry

- `data/processed/tables/subbasin_morphometry.csv`

## Script 08: Lineament-Drainage Analysis

Generated only when optional lineament vectors exist:

- `data/processed/rasters/lineament_density.tif`
- `data/processed/tables/lineament_stats.csv`
- `data/processed/vectors/drainage_lineament_intersections.gpkg`

## Script 09: Flood Hazard Factors

- `data/processed/rasters/factor_*_score.tif`
- aligned intermediate factor rasters beside score rasters

## Script 10: Flood Hazard Index

- `data/processed/rasters/flood_hazard_index_continuous.tif`
- `data/processed/rasters/flood_hazard_index_classified.tif`
- `data/processed/vectors/flood_hazard_zones.gpkg`
- `data/processed/tables/hazard_area_summary.csv`
- `data/processed/tables/hazard_subbasin_summary.csv`

## Script 11: Sub-Basin Ranking

- `data/processed/tables/subbasin_priority_ranking.csv`
- `data/processed/vectors/subbasin_priority_ranking.gpkg`

## Script 12: Maps and Charts

- `outputs/figures/dem_preview.png`
- `outputs/figures/slope_preview.png`
- `outputs/figures/flow_accumulation_preview.png`
- `outputs/maps/stream_network.png`
- `outputs/maps/subbasins.png`
- `outputs/maps/flood_hazard_index.png`
- `outputs/maps/subbasin_priority.png`
- `outputs/charts/hazard_area_bar.png`

## Script 13: Report Assets

- `outputs/reports/hydromorpho_summary_report.md`

