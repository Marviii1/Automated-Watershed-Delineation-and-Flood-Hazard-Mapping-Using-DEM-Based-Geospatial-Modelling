# Methodology

## 1. DEM Preprocessing

The DEM is clipped to the study boundary, reprojected to the configured projected CRS, and hydrologically corrected before flow modelling. The hydrological correction method is configurable:

- **Breach depressions:** attempts to carve drainage paths through artificial barriers and is often useful for preserving terrain gradients.
- **Fill sinks:** raises depressions until downstream flow is possible and may be preferred for some DEM products.

Terrain derivatives include hillshade, slope, aspect, and optional additional products. Hillshades with multiple illumination angles can support visual interpretation of structural trends and terrain controls.

## 2. Flow Routing

The workflow uses D8 flow routing through WhiteboxTools. Each cell is assigned flow to one of its eight neighboring cells in the direction of steepest descent. Outputs include:

- D8 flow pointer / flow direction raster.
- D8 flow accumulation raster in number of contributing cells.

Flow accumulation values are thresholded to define the stream network.

## 3. Stream Extraction

Stream extraction uses a configurable accumulation threshold. A lower threshold produces denser drainage networks; a higher threshold produces only larger channels. The selected threshold should be tested against reference hydrography or high-resolution imagery when possible.

The extracted stream raster is converted to vector polylines where feasible. Stream ordering supports Strahler and Shreve outputs depending on available WhiteboxTools functions and local data behavior.

## 4. Watershed and Sub-Basin Delineation

Watershed delineation uses outlet or pour point data with D8 flow direction. Pour points may be manually supplied, derived from stream junctions, or snapped to high-flow accumulation cells if configured. The default scaffold expects supplied outlet points and leaves room for project-specific junction-derived pour point generation.

Outputs include watershed and sub-basin polygons. Basin geometry metrics include area, perimeter, and an estimated basin length from the maximum axis of the minimum rotated rectangle.

## 5. Morphometric Analysis

Morphometric analysis is grouped into linear, areal, and relief aspects.

### Linear Aspects

- Stream order.
- Number of streams per order.
- Total stream length per order.
- Mean stream length.
- Bifurcation ratio: `Rb = Nu / N(u+1)`.

Bifurcation ratio assumes reliable stream ordering and segmented channel topology. Where stream ordering or segmentation is incomplete, it should be interpreted cautiously.

### Areal Aspects

- Drainage density: `Dd = total stream length / basin area`.
- Stream frequency: `Fs = total number of streams / basin area`.
- Drainage texture: `T = total number of streams / basin perimeter`.
- Form factor: `Ff = basin area / basin length^2`.
- Circularity ratio: `Rc = 4*pi*A / P^2`.
- Elongation ratio: `Re = diameter of circle of same area / basin length`.
- Infiltration number: `If = drainage density * stream frequency`.

Higher drainage density and stream frequency often indicate more rapid runoff response, but interpretation depends on lithology, soil, vegetation, DEM resolution, and climate.

### Relief Aspects

- Basin relief: `H = elevation maximum - elevation minimum`.
- Relief ratio: `Rh = basin relief / basin length`.
- Relative relief: basin relief normalized by perimeter or comparable basin scale.
- Ruggedness number: `Rn = basin relief * drainage density`.
- Average slope.
- Minimum, maximum, and mean elevation.

## 6. Lineament-Drainage Integration

The project includes a semi-automated lineament workflow. It can:

- Generate hillshade imagery useful for structural interpretation.
- Ingest manually digitized or externally generated lineament vectors.
- Calculate lineament length, density, and orientation summaries.
- Calculate drainage-lineament intersections.
- Identify zones where high lineament density coincides with high drainage density.

Lineament density should not be described as direct proof of groundwater recharge. In this project, these products are framed as indicators of structurally influenced drainage zones or potential fracture-controlled hydrological corridors requiring geological validation.

## 7. Flood Hazard MCDA Modelling

Flood hazard modelling uses a configurable weighted overlay:

```text
Flood Hazard Index = sum(weight_i * score_i)
```

Each flood conditioning factor is aligned to a common reference raster, reclassified into 1-5 susceptibility scores, weighted, summed, and classified into:

1. Very Low
2. Low
3. Moderate
4. High
5. Very High

Potential factors include slope, elevation, flow accumulation, distance to streams, drainage density, TWI, SPI, land cover, and soil runoff proxy. Reclassification rules and weights are configured in `config/flood_hazard_config.yml`.

## 8. Sub-Basin Prioritization

Sub-basin priority combines flood hazard statistics with morphometric runoff indicators such as drainage density, stream frequency, relief, ruggedness, and slope. The result is a ranked table and GeoPackage layer with priority classes from Very Low Priority to Very High Priority.

## 9. Assumptions and Limitations

- Outputs depend strongly on DEM resolution, vertical accuracy, sink treatment, and stream threshold selection.
- Flood hazard index maps are susceptibility outputs, not flood depth or hydraulic inundation simulations.
- LULC and soil reclassification rules must be adapted to local class systems.
- Structural interpretations require geological expertise, field checks, and supporting datasets.
- Observed flood inventory or discharge records should be used for validation where available.

