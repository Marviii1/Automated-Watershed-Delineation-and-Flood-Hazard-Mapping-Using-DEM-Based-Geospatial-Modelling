# HydroMorpho-Flood Intelligence System

## Study Area

**Study area:** Ilaje Local Government Area  
**State:** Ondo State  
**Country:** Nigeria  
**Description:** Configured for Ilaje LGA, Ondo State, Nigeria. Use the Ilaje LGA polygon as the study-area mask and keep raw datasets large enough to cover the full LGA boundary.

## Datasets Used

- DEM: `data/raw/dem/ilaje_dem.tif`
- Boundary: `data/raw/boundary/ilaje_lga_boundary.shp`
- Outlets: `data/raw/outlets/ilaje_outlets.gpkg`
- LULC: `data/raw/lulc/lulc.tif`
- Soils: `data/raw/soils/soils.tif`

## Methodology

The workflow clips and projects the DEM, applies hydrological conditioning, derives D8 flow products, extracts streams, delineates watershed and sub-basins, computes morphometric indicators, integrates optional lineament information, creates flood hazard factor scores, and ranks sub-basins.

## Morphometric Summary

|   subbasin_id |   area_km2 |   perimeter_km |   basin_length_km |   stream_count |   total_stream_length_km |   mean_stream_length_km |   drainage_density_km_per_km2 |   stream_frequency_no_per_km2 |   drainage_texture |   form_factor |   circularity_ratio |   elongation_ratio |   infiltration_number |   elev_min_m |   elev_max_m |   elev_mean_m |   basin_relief_m |   relief_ratio |   relative_relief |   ruggedness_number |   average_slope_degrees |   fast_runoff_tendency |
|--------------:|-----------:|---------------:|------------------:|---------------:|-------------------------:|------------------------:|------------------------------:|------------------------------:|-------------------:|--------------:|--------------------:|-------------------:|----------------------:|-------------:|-------------:|--------------:|-----------------:|---------------:|------------------:|--------------------:|------------------------:|-----------------------:|
|             1 | 0.00177644 |       0.178818 |          0.059606 |              0 |                        0 |                     nan |                             0 |                             0 |                  0 |           0.5 |            0.698132 |           0.797885 |                     0 |           14 |           15 |          14.5 |                1 |      0.0167768 |        0.00559228 |                   0 |                0.720623 |                      1 |

## Flood Hazard Area Summary

|   hazard_class | hazard_label   |   area_km2 |
|---------------:|:---------------|-----------:|
|              1 | Very Low       |    10.8967 |
|              2 | Low            |   801.144  |
|              3 | Moderate       |   504.686  |
|              4 | High           |    92.5417 |
|              5 | Very High      |    10.8976 |
|            241 | 241            |  4473.75   |

## Lineament-Drainage Summary

_Missing table: C:\Users\Marvii\Documents\GIS_PROJECTS\Hydrological Drainage_ Analysis\data\processed\tables\lineament_stats.csv_

Lineament outputs are interpreted as structurally influenced drainage zones or potential fracture-controlled hydrological corridors, not as direct proof of groundwater recharge.

## Sub-Basin Priority Ranking

|   subbasin_id |   area_km2 |   perimeter_km |   basin_length_km |   stream_count |   total_stream_length_km |   mean_stream_length_km |   drainage_density_km_per_km2 |   stream_frequency_no_per_km2 |   drainage_texture |   form_factor |   circularity_ratio |   elongation_ratio |   infiltration_number |   elev_min_m |   elev_max_m |   elev_mean_m |   basin_relief_m |   relief_ratio |   relative_relief |   ruggedness_number |   average_slope_degrees |   fast_runoff_tendency |   fhi_mean |   fhi_max |   majority_hazard_class | majority_hazard_label   |   priority_score |   priority_rank |   priority_class | priority_label    |
|--------------:|-----------:|---------------:|------------------:|---------------:|-------------------------:|------------------------:|------------------------------:|------------------------------:|-------------------:|--------------:|--------------------:|-------------------:|----------------------:|-------------:|-------------:|--------------:|-----------------:|---------------:|------------------:|--------------------:|------------------------:|-----------------------:|-----------:|----------:|------------------------:|:------------------------|-----------------:|----------------:|-----------------:|:------------------|
|             1 | 0.00177644 |       0.178818 |          0.059606 |              0 |                        0 |                     nan |                             0 |                             0 |                  0 |           0.5 |            0.698132 |           0.797885 |                     0 |           14 |           15 |          14.5 |                1 |      0.0167768 |        0.00559228 |                   0 |                0.720623 |                      1 |    2.72727 |   2.81818 |                       3 | Moderate                |                0 |               1 |                3 | Moderate Priority |

## Limitations

Flood hazard classes are susceptibility indicators derived from terrain and thematic factor overlay. They are not hydraulic inundation depths. Lineament-drainage outputs identify possible structurally influenced drainage zones and should be interpreted with geological context and field validation.
