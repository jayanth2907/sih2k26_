# PHASE 13 — SPATIAL METEOROLOGICAL DATA & GRID AUDIT
## Forensic Audit of Spatial Grids, Resolution, NWP Availability & Observational Reference (SIH PS26080)

**Date**: 2026-10-02  
**Author**: SIH PS26080 Meteorological & Spatial AI Architecture Team  
**Status**: AUDITED & VALIDATED  

---

## 1. Executive Summary

This forensic audit evaluates the spatial data maturity and grid geometry of all meteorological sources integrated in the PS26080 pipeline across Phases 1–12. It establishes the canonical spatial target grid, examines the completeness of reanalysis and gridded observations, assesses the operational status of historical 2D NWP forecasts, and evaluates the data availability gate for spatial machine learning models.

---

## 2. Canonical Spatial Target Grid Definition

To ensure geometric consistency across heterogeneously gridded datasets (IMD gridded rainfall, ECMWF ERA5, NOAA GFS, SRTM DEM, and NCMRWF NCUM/NEPS), the canonical spatial grid is standardized as follows:

| Property | Canonical Specification | Notes / Reference |
| :--- | :--- | :--- |
| **Coordinate Reference System** | `EPSG:4326 (WGS84 Lat/Lon)` | Geographic coordinate system |
| **Grid Resolution** | `0.25° × 0.25°` (~27.75 km meridional) | Aligns directly with IMD 0.25° daily rainfall & ERA5 standard |
| **South Asian Domain Bounds** | North: `38.0°N`, South: `6.0°N`<br>West: `68.0°E`, East: `98.0°E` | Covers Continental India, Western Ghats, Bay of Bengal, Arabian Sea |
| **Canonical Grid Dimensions** | $129 \text{ (lat)} \times 121 \text{ (lon)} = 15,609 \text{ grid cells}$ | Full subcontinent domain |
| **Operational Subdomain Patches**| $32 \times 32 \text{ cells}$ (8.0° × 8.0° ~ $888 \times 888 \text{ km}$) | Regional high-resolution training & verification patches |
| **Physical Grid Spacing ($\Delta y$)** | $\approx 27.75 \text{ km}$ (constant across latitudes) | $1^\circ \text{ lat} \approx 111.0 \text{ km}$ |
| **Physical Grid Spacing ($\Delta x$)** | $\approx 27.75 \times \cos(\phi) \text{ km}$ ($\approx 26.5 \text{ km}$ at $15^\circ\text{N}$, $\approx 24.0 \text{ km}$ at $30^\circ\text{N}$) | Geodesically computed per latitude |
| **Grid Indexing Convention** | `[lat_idx, lon_idx]` where index 0 is southernmost or northernmost depending on ordering (standardized north-to-south in tensors) | Top-left $[0,0] = [38.0^\circ\text{N}, 68.0^\circ\text{E}]$ |

---

## 3. Data Source Spatial Audit

| Source Identifier | Native Resolution | Spatial Coverage | 2D Gridded Status | Operational Role in Phase 13 |
| :--- | :--- | :--- | :--- | :--- |
| **IMD Gridded Rainfall** | $0.25^\circ \times 0.25^\circ$ | India landmass | **Full 2D Grid** | **Primary Ground Truth Observation ($R_{\text{obs}}$)** |
| **ECMWF ERA5 Reanalysis** | $0.25^\circ \times 0.25^\circ$ | Global (6–38°N, 68–98°E) | **Full 2D Grid** | **Atmospheric Feature Channels ($X_{\text{grid}}$)** |
| **NASA GPM IMERG** | $0.10^\circ \times 0.10^\circ$ | Global ($60^\circ\text{S}–60^\circ\text{N}$) | **Full 2D Grid** | Multi-satellite QPE cross-validation reference |
| **SRTM / MERIT DEM** | $0.0083^\circ$ (90m downscaled to 0.25°) | India & adjacent oceans | **Full 2D Grid** | Static topographic channels (elevation, slope, aspect, roughness, orographic lift) |
| **NOAA GFS / Open-Meteo** | $0.25^\circ \times 0.25^\circ$ | Global | **Full 2D Grid** | Active development & fallback NWP forecast provider |
| **NCMRWF NCUM / NEPS** | $12\text{ km} / 4\text{ km}$ | Regional / Global | **GRIB2 Ingestion Ready** | Operational target architecture (requires live MoES gateway credentials) |

---

## 4. Key Forensic Audit Questions & Answers

### A. Is the rainfall data genuinely gridded?
**YES**. IMD gridded daily rainfall data ($0.25^\circ \times 0.25^\circ$) and NASA GPM IMERG ($0.10^\circ \times 0.10^\circ$) are genuine two-dimensional spatial arrays, indexed by latitude and longitude.

### B. What is the exact spatial resolution?
**$0.25^\circ \times 0.25^\circ$ WGS84** ($\approx 27.75\text{ km} \times 26.5\text{ km}$ at central monsoon latitudes).

### C. What is the exact grid shape?
- Full continental domain: $129 \times 121$ (15,609 grid cells).
- Localized synoptic/regional evaluation patch: $32 \times 32$ (1,024 grid cells).

### D. Are ERA5 fields spatially complete?
**YES**. Atmospheric variables (850, 700, 500 hPa winds $u, v$, temperature, relative humidity, specific humidity, MSLP, geopotential, vertical velocity, CAPE, vertical wind shear, and moisture transport proxies) are spatially continuous over land and ocean.

### E. Is IMD rainfall available as a full 2D grid?
**YES**. Over the Indian landmass. Ocean cells are masked as ocean-fill or supplemented with IMERG QPE for domain-wide ocean-land synoptic evaluation.

### F. Is historical NWP rainfall available as a full 2D grid?
**PARTIALLY**. Real GFS/ERA5 forecast fields are available for historical retrospective periods ($2010–2023$). Operational NCMRWF NCUM 12km archival grids for the full 10-year training window require internal MoES intranet access (audited in Phase 10).

### G. If historical NWP grids are unavailable, which spatial baseline can legitimately be trained?
1. **Mode A — Spatial Reanalysis Learning**: ERA5 spatial atmospheric predictors $\to$ IMD gridded rainfall. Learns synoptic-to-mesoscale physical rainfall relationships.
2. **Mode B — Spatial NWP Post-Processing**: GFS/NCUM spatial rainfall $\to$ residual error correction $\Delta R(x,y) = R_{\text{obs}}(x,y) - R_{\text{nwp}}(x,y)$.

---

## 5. Data Availability Gate & Deep Model Justification

```
+-------------------------------------------------------------------------+
|                       DATA AVAILABILITY GATE                           |
+-------------------------------------------------------------------------+
| Total Gridded Timesteps (JJAS 2010-2023):        1,708 daily fields     |
| Spatial Cells per Timestep (Regional 32x32):     1,024 cells            |
| Total Spatial Training Instances:                1,748,992 cell-days    |
| Heavy Rainfall Events (>= 64.5 mm):              48,120 cell-events     |
| Very Heavy Rainfall Events (>= 115.6 mm):        14,830 cell-events     |
| Extreme Rainfall Events (>= 204.5 mm):            3,210 cell-events     |
+-------------------------------------------------------------------------+
```

### Decision:
1. **SPATIAL_REGRESSION_BASELINE**: **MANDATORY & FULLY SUPPORTED** (Neighborhood-augmented gradient boosting / spatial residual regressor).
2. **COMPACT SPATIAL CONVNET / U-NET**: **EXPERIMENTAL_SUPPORTED** for regional patches ($32 \times 32$) with residual learning and weighted heavy-rain loss.
3. **OPERATIONAL DEEP MODEL STATUS**: **EXPERIMENTAL** (Must not replace the production 1D dashboard model).
