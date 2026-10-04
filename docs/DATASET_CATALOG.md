# Meteorological Training Dataset Catalog

## 1. Catalog Overview

The dataset catalog records all raw, intermediate, and processed datasets utilized in the SIH PS26080 AI post-processing system.

---

## 2. Cataloged Historical Datasets

### Dataset: `ERA5_JJAS_2010_2023_025DEG`
- **Source**: Copernicus Climate Data Store (ECMWF)
- **Role**: Reanalysis Atmospheric State & Synoptic Predictor Training Baseline
- **Spatial Grid**: 0.25° × 0.25° (Lat: 6.0°N to 38.0°N, Lon: 66.0°E to 100.0°E)
- **Temporal Range**: 2010-06-01 to 2023-09-30 (JJAS Monsoon Seasons)
- **Vertical Levels**: 850 hPa, 700 hPa, 500 hPa
- **Variables**: $u, v, t, r, z, w$, MSLP, surface pressure, 2m temperature, CAPE, TP
- **Format**: NetCDF4 / Zarr
- **Provenance**: `REAL_REANALYSIS`
- **Status**: Cataloged & Adapter Ready

---

### Dataset: `IMD_025_DAILY_PRECIP_2010_2023`
- **Source**: India Meteorological Department (IMD / MoES)
- **Role**: Observational Ground-Truth Verification & Calibration Target
- **Spatial Grid**: 0.25° × 0.25° South Asian Domain
- **Temporal Range**: 2010-06-01 to 2023-10-01 (Daily 0300 UTC / 0830 IST Accumulation)
- **Variables**: 24-hour Accumulated Rainfall (mm)
- **Format**: Binary (`.grd`) / NetCDF4
- **Provenance**: `REAL_OBSERVATIONS`
- **Status**: Cataloged & Adapter Ready

---

### Dataset: `NCUM_HISTORICAL_NWP_ARCHIVE`
- **Source**: National Centre for Medium Range Weather Forecasting (NCMRWF)
- **Role**: Target Operational NWP Baseline for True Bias Correction Learning
- **Spatial Grid**: 12 km Regional / 4 km Nested
- **Temporal Range**: 2018-06-01 to 2023-09-30
- **Variables**: Forecast Precipitation, Dynamic Winds, Multi-Level Thermodynamics
- **Format**: GRIB2
- **Provenance**: `REAL_NWP_FORECAST_TARGET`
- **Status**: `PENDING_INSTITUTIONAL_ARCHIVE_TRANSFER`
