# SPATIAL DATA AUDIT (SIH PS26080)

## Overview & Grid Specifications

- **Reference Grid**: 0.25° × 0.25° WGS84 (`EPSG:4326`)
- **South Asian Monsoon Domain**: Latitudes 6.0°N to 38.0°N, Longitudes 68.0°E to 98.0°E
- **Grid Resolution**: $\Delta y = 27.75\text{ km}$, $\Delta x = 27.75 \cos(\text{lat})\text{ km}$
- **2D Observation Grids**: IMD Gridded Rainfall (0.25°), NASA GPM IMERG (0.10° regridded)
- **2D Atmospheric Predictors**: ECMWF ERA5 (850/700/500 hPa winds, RH, T, MSLP, geopotential, CAPE, vertical velocity, IVT, vorticity)
- **Static Topography**: SRTM/MERIT 0.25° DEM (Elevation, Slope, Aspect, Roughness, Orographic Lift Index, Distance to Coast)
- **Spatial Target**: Residual error $\Delta R(x,y) = R_{\text{obs}}(x,y) - R_{\text{nwp}}(x,y)$

## Data Availability Gate
- **Sample Scale**: 1,708 JJAS daily grids (2010–2023)
- **Spatial Instances**: >1.7M cell-observations
- **Spatial Baseline Model**: `SPATIAL_RESIDUAL_BASELINE_V1` (Neighborhood-augmented residual regressor with 3x3, 5x5, 9x9 multi-scale physical receptive fields)
- **Deep Spatial Architecture**: `SPATIAL_REGIME_AWARE_V1` (Compact Convolutional / U-Net architecture with soft regime gating and weighted heavy-rain loss)
- **Model Registry Governance**: Registered with lifecycle state `EXPERIMENTAL`. Active production model remains frozen.
