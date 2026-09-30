# Meteorological Data Ingestion, Regridding & Feature Pipeline (PS26080)
**Smart India Hackathon 2026 — Problem Statement SIH26080**  
**Organization:** Ministry of Earth Sciences (MoES)  
**Department:** National Centre for Medium Range Weather Forecasting (NCMRWF)

---

## 1. Overview and Scientific Objectives

The Phase 2 Meteorological Data Pipeline establishes the standardized, causality-preserving observational and numerical input layer for regime-aware AI post-processing of Indian monsoon rainfall forecasts. 

Unlike conventional machine learning approaches that train on raw point forecasts without spatial or thermodynamic grounding, this pipeline ingests multi-level atmospheric state variables, performs quality control with audit logging, standardizes heterogeneous grids to a common coordinate reference, and computes physically meaningful derived atmospheric features.

```
+---------------------------------------------------------------------------------------------------+
|                                 METEOROLOGICAL DATA SOURCES                                       |
|  +--------------------+  +--------------------+  +--------------------+  +--------------------+   |
|  |    NCMRWF NCUM     |  |    NCMRWF NEPS     |  |    ECMWF ERA5      |  |  IMD Daily Gridded |   |
|  |  12km Operational  |  |  23-Member Ensemble|  |  0.25° Reanalysis  |  |    Observations    |   |
|  +--------------------+  +--------------------+  +--------------------+  +--------------------+   |
|  +--------------------+  +--------------------+  +--------------------+  +--------------------+   |
|  |   NASA GPM IMERG   |  |   SRTM 90m DEM     |  |  Survey of India   |  |   NOAA GFS 0.25°   |   |
|  | 0.1° Precipitation |  | Terrain & Gradients|  | District Polygons  |  | (Fallback Adapter) |   |
|  +--------------------+  +--------------------+  +--------------------+  +--------------------+   |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                               CANONICAL STANDARDIZATION & QUALITY CONTROL                         |
|  - Longitude domain wrapping [-180°, 180°]               - Pressure unit normalization (Pa -> hPa)|
|  - Physical boundary validation (RH: 0-100%, Rain >= 0)  - Causality audit (No lookahead bias)    |
|  - Spatial interpolation (2D Bilinear Grid Alignment)    - Quality Control Audit Logging          |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                             DERIVED METEOROLOGICAL FEATURE EXTRACTION                             |
|  - 850 / 700 hPa Wind Speed & Meteorological Direction   - Bolton/Tetens Specific Humidity (q)    |
|  - Bulk Vertical Wind Shear (850 - 500 hPa)              - Integrated Vapor Transport (IVT proxy) |
|  - Orographic Lift Index (Normal Wind * Slope * Height)  - Coastal Moisture Convergence Indicator |
|  - 6h, 12h, 24h Rainfall Accumulation Curves             - Multi-member Ensemble Spread & Disagree|
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                               CANONICAL METEOROLOGICAL RECORD                                     |
|                      Target Input for Weather Regime Classification & AI Post-Processing          |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Ingested Data Sources

The platform implements a modular adapter architecture (`backend/app/data/sources/`) covering 7 meteorological, observational, and geographic sources:

| # | Data Source Identifier | Role | Spatial Resolution | Temporal Frequency | Live / Demo Attribution |
|---|---|---|---|---|---|
| 1 | `NCMRWF_NCUM` | Target Operational Deterministic NWP | 12 km Regional (~4 km Nested) | Hourly out to T+240h | Target Integration (`is_demo: false` when connected, fallback demo tagged) |
| 2 | `NCMRWF_NEPS` | Target Operational Probabilistic Ensemble NWP | 12 km (23 Ensemble Members) | 6-hourly out to Day 10 | Target Integration (`is_demo: false` when connected, fallback demo tagged) |
| 3 | `ECMWF_ERA5` | Historical Reanalysis Training Benchmark | 0.25° × 0.25° (~31 km) | Hourly (1979–Present) | Operational Reanalysis Benchmark (`is_demo: false`) |
| 4 | `IMD_GRIDDED_RAINFALL` | Observational Ground Truth Calibration Target | 0.25° × 0.25° (~27 km) | Daily accumulated (0300 UTC) | Operational Observational Truth (`is_demo: false`) |
| 5 | `NASA_GPM_IMERG` | High-Resolution Satellite Precipitation Truth | 0.1° × 0.1° (~10 km) | Half-hourly accumulated | Operational Satellite Truth (`is_demo: false`) |
| 6 | `SRTM_DEM_TOPOGRAPHY` | Static Orographic & Terrain Predictor | 90 m (1 km aggregated) | Static | Operational Geospatial Grid (`is_demo: false`) |
| 7 | `SURVEY_OF_INDIA_DISTRICTS` | Administrative Boundary Polygon Hierarchy | 748 District Polygons | Static (2024 boundary set) | Operational Administrative Truth (`is_demo: false`) |
| * | `NOAA_GFS_OPENMETEO_FALLBACK` | Development & Offline Fallback Adapter | 0.25° × 0.25° | Hourly | Development Fallback (`is_demo: true` — never labeled as NCMRWF) |

---

## 3. Canonical Meteorological Record Schema

Every data adapter converts source-specific formats (GRIB2, NetCDF4, HDF5, GeoTIFF, REST JSON) into a unified `CanonicalMeteorologicalRecord` defined in `backend/app/data/schemas/meteorology.py`:

```python
class CanonicalMeteorologicalRecord(BaseModel):
    # 1. Temporal Identifiers
    timestamp: str                         # Forecast valid time or observation ISO 8601 UTC
    forecast_initialization: Optional[str] # Forecast cycle run ISO 8601 UTC
    lead_time_hours: int                   # Lead time in hours (0 for observations)

    # 2. Spatial Coordinates
    latitude: float                        # WGS84 Latitude [-90.0, 90.0]
    longitude: float                       # WGS84 Longitude [-180.0, 180.0]

    # 3. Precipitation & Ensemble Statistics
    rainfall: float                        # Rainfall rate / accumulation (mm)
    ensemble_mean: Optional[float]
    ensemble_std: Optional[float]
    ensemble_min: Optional[float]
    ensemble_max: Optional[float]
    ensemble_p10: Optional[float]
    ensemble_p90: Optional[float]

    # 4. Multi-Level Atmospheric Thermodynamics (850, 700, 500 hPa)
    temperature_850: Optional[float]       # Kelvin or Celsius
    temperature_700: Optional[float]
    temperature_500: Optional[float]
    relative_humidity_850: Optional[float] # % (0.0 to 100.0)
    relative_humidity_700: Optional[float]
    relative_humidity_500: Optional[float]

    # 5. Multi-Level Dynamic Wind Components (m/s)
    u850: Optional[float]; v850: Optional[float]
    u700: Optional[float]; v700: Optional[float]
    u500: Optional[float]; v500: Optional[float]

    # 6. Geopotential Height & Vertical Velocity
    geopotential_850: Optional[float]      # gpm
    geopotential_500: Optional[float]      # gpm
    vertical_velocity: Optional[float]     # Pa/s (omega)

    # 7. Surface Variables & Topography
    surface_pressure: Optional[float]      # hPa
    mslp: Optional[float]                  # Mean Sea Level Pressure (hPa)
    cape_j_kg: Optional[float]             # J/kg
    elevation: Optional[float]             # m above MSL
    slope: Optional[float]                 # degrees
    aspect: Optional[float]                # degrees azimuth
    terrain_roughness: Optional[float]     # m
    distance_to_coast: Optional[float]     # km

    # 8. Data Provenance & Reliability Metadata
    observed_rainfall: Optional[float]     # Collocated IMD ground truth (mm)
    data_source: str                       # E.g. 'NCMRWF_NCUM', 'ERA5'
    data_quality: str                      # 'QC_PASSED', 'IMPUTED', 'RAW'
    is_demo: bool                          # True for synthetic/fallback data
```

---

## 4. Quality Control & Audit Logging Protocol

The automated QC module (`backend/app/data/processing/quality_control.py`) inspects every record before downstream processing:
1. **Rainfall Non-Negativity:** Negative precipitation values (arising from numerical spline artifacts) are reset to $0.0\text{ mm}$ and logged.
2. **Physical Extreme Capping:** World-record 24-hour rainfall cap ($1200\text{ mm}$) prevents corruption from corrupted sensor feeds.
3. **Relative Humidity Bound Clamping:** Values $<0\%$ clamped to $0\%$, values $>100\%$ clamped to $100\%$, with audit logs generated for extreme violations ($>105\%$).
4. **Pressure Unit Standardizing:** Ingested barometric pressure values exceeding $2000$ are automatically recognized as Pascals ($\text{Pa}$) and converted to hectopascals ($\text{hPa}$) ($P_{\text{hPa}} = P_{\text{Pa}} / 100$).
5. **Causality Integrity:** Forecast initialization time must precede or equal valid time ($t_{\text{init}} \le t_{\text{valid}}$), and historical observations used for conditioning must strictly satisfy $t_{\text{obs}} \le t_{\text{init}}$ to prevent lookahead data leakage.

---

## 5. Feature Engineering Physics

The derived feature pipeline (`backend/app/data/processing/feature_engineering.py`) computes 15 essential meteorological indices:

1. **Wind Vector Metrics:**
   $$\text{Speed} = \sqrt{u^2 + v^2}$$
   $$\text{Direction} = \left(270^\circ - \text{atan2}(v, u)\right) \pmod{360^\circ}$$

2. **Bulk Vertical Wind Shear ($850 - 500\text{ hPa}$):**
   $$\Delta V_{\text{shear}} = \sqrt{(u_{500} - u_{850})^2 + (v_{500} - v_{850})^2}$$

3. **Specific Humidity ($q$) via Tetens & Bolton Formulations:**
   $$e_s(T) = 6.112 \exp\left(\frac{17.67 T_c}{T_c + 243.5}\right)$$
   $$e = \frac{\text{RH}}{100} \cdot e_s$$
   $$q = \frac{0.622 \cdot e}{P - 0.378 \cdot e} \times 1000 \quad (\text{g/kg})$$

4. **Integrated Vapor Transport (IVT Proxy):**
   $$\text{IVT}_{\text{proxy}} = q_{850} \cdot V_{850} \quad (\text{kg}/(\text{m}\cdot\text{s}))$$

5. **Orographic Lift Index:**
   $$\text{OLI} = V_{850} \cdot |\cos(\theta_{\text{wind}} - \theta_{\text{aspect}})| \cdot \tan(\alpha_{\text{slope}}) \cdot \left(\frac{z_{\text{elev}}}{1000}\right)$$

6. **Coastal Moisture Convergence Index:**
   $$\text{CMI} = \left(V_{850} \cdot \frac{\text{RH}_{850}}{100}\right) \cdot \exp\left(-\frac{d_{\text{coast}}}{75\text{ km}}\right)$$

---

## 6. Dataset Structure and Chronological Splitting Strategy

```
data/
├── training/    # Historical monsoon seasons 2018 - 2022 (JJAS)
├── validation/  # Monsoon season 2023 (JJAS) for tuning & threshold calibration
└── test/        # Out-of-sample monsoon seasons 2024 - 2025 (JJAS)
```

**Zero Leakage Rule:**
Random `train_test_split` is strictly prohibited. Atmospheric states exhibit strong spatial and synoptic temporal autocorrelation. Chronological splitting ensures true out-of-sample prospective evaluation matching real NCMRWF operations.
