# Data Dictionary

## Input Data Layers

| Layer | Type | Required | Description |
|---|---:|---:|---|
| study_area_boundary | Polygon vector | Yes | Basin or study area boundary used for clipping and reporting. |
| dem | Raster | Yes | Digital elevation model covering the study area. |
| outlet_points | Point vector | Yes | Pour points or outlets used for watershed delineation. |
| lulc | Raster | No | Land use / land cover factor for flood hazard modelling. |
| soils | Raster or vector | No | Soil permeability, texture, hydrologic group, or runoff proxy. |
| hydrography_reference | Vector | No | Reference stream network for validation and interpretation. |
| lineaments | Line vector | No | Manually digitized or externally generated lineaments. |
| settlements | Vector | No | Settlement points or polygons for exposure interpretation. |
| roads | Vector | No | Road network for exposure interpretation. |
| population | Raster | No | Population surface for optional exposure summaries. |

## Interim Outputs

| Output | Description |
|---|---|
| dem_clipped.tif | DEM clipped to the study area boundary. |
| dem_projected.tif | DEM reprojected to the project CRS. |
| dem_hydro_corrected.tif | Breached or filled DEM for hydrological modelling. |
| d8_pointer.tif | D8 flow direction / pointer raster. |
| d8_flow_accumulation_cells.tif | Flow accumulation in contributing cells. |
| streams_thresholded.tif | Raster stream network after accumulation thresholding. |
| stream_order_strahler.tif | Strahler stream order raster. |
| stream_order_shreve.tif | Shreve stream magnitude raster. |
| watershed.tif | Watershed raster from pour points. |
| terrain/slope_degrees.tif | Slope raster in degrees. |
| terrain/aspect_degrees.tif | Aspect raster. |
| terrain/hillshade.tif | Hillshade raster. |

## Final Processed Outputs

| Output | Description |
|---|---|
| stream_network.gpkg | Extracted stream polylines. |
| watershed.gpkg | Watershed polygons. |
| subbasins.gpkg | Sub-basin polygons. |
| subbasin_morphometry.csv | Morphometric indicators by sub-basin. |
| lineament_density.tif | Local density raster from optional lineament vectors. |
| lineament_stats.csv | Length and orientation statistics for lineaments. |
| drainage_lineament_intersections.gpkg | Stream-lineament intersection geometries. |
| flood_hazard_index_continuous.tif | Continuous weighted flood hazard index. |
| flood_hazard_index_classified.tif | Classified 1-5 flood hazard raster. |
| flood_hazard_zones.gpkg | Vectorized hazard class polygons. |
| hazard_area_summary.csv | Area by hazard class. |
| hazard_subbasin_summary.csv | FHI statistics by sub-basin. |
| subbasin_priority_ranking.csv | Ranked sub-basin priority table. |
| subbasin_priority_ranking.gpkg | Ranked sub-basin polygons. |

## Morphometric Table Fields

| Field | Description |
|---|---|
| subbasin_id | Unique sub-basin identifier. |
| area_km2 | Basin area in square kilometers. |
| perimeter_km | Basin perimeter in kilometers. |
| basin_length_km | Estimated maximum basin length. |
| stream_count | Number of stream segments. |
| total_stream_length_km | Total stream length. |
| mean_stream_length_km | Mean stream segment length. |
| drainage_density_km_per_km2 | Total stream length divided by basin area. |
| stream_frequency_no_per_km2 | Stream count divided by basin area. |
| drainage_texture | Stream count divided by perimeter. |
| form_factor | Basin area divided by basin length squared. |
| circularity_ratio | 4*pi*area divided by perimeter squared. |
| elongation_ratio | Equivalent circular diameter divided by basin length. |
| infiltration_number | Drainage density multiplied by stream frequency. |
| basin_relief_m | Maximum elevation minus minimum elevation. |
| relief_ratio | Basin relief divided by basin length. |
| ruggedness_number | Basin relief multiplied by drainage density. |

## Sub-Basin Ranking Fields

| Field | Description |
|---|---|
| fhi_mean | Mean continuous flood hazard index. |
| fhi_max | Maximum continuous flood hazard index. |
| majority_hazard_class | Dominant classified hazard class. |
| priority_score | Composite normalized ranking score. |
| priority_rank | Rank ordered from highest concern to lowest. |
| priority_class | Numeric priority class. |
| priority_label | Text priority class label. |

