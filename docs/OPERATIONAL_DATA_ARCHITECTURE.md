# Phase 10: Operational Data Maturity & NCMRWF Ingestion Architecture

## 1. Executive Summary & Purpose

Phase 10 audits, hardens, and formalizes the data ingestion architecture for **SIH PS26080: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts (MoES / NCMRWF)**. 

The primary objective is to bridge the scientific post-processing pipeline with operational meteorological data feeds. The system is architected to transition seamlessly from **Development Fallback (NOAA GFS / Synthetic Demo Synthesis)** to **Operational Target Feeds (NCMRWF NCUM 12km / NEPS 23-member Ensemble)** without breaking data schemas, scientific calibration, or validation guarantees.

---

## 2. Ingestion Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Operational NWP Ingestion Stream                      │
│                                                                             │
│  [NCMRWF NCUM Regional]      [NCMRWF NEPS Ensemble]       [NOAA GFS Fallback]│
│           │                             │                          │        │
│           ▼                             ▼                          ▼        │
│     GRIB2 / NetCDF                 GRIB2 Multi-Member         Open-Meteo REST│
└───────────┬─────────────────────────────┬──────────────────────────┬────────┘
            │                             │                          │
            ▼                             ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Data Ingestion & Normalization Layer                      │
│                                                                             │
│  ┌───────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐ │
│  │   Metadata Validator  │  │   Unit Normalizer    │  │ Spatial/Temporal │ │
│  │  - Agency/Model check │  │  - kg m⁻² -> mm      │  │ - Lon [-180,180] │ │
│  │  - Bounds validation  │  │  - Pa -> hPa         │  │ - ISO 8601 UTC   │ │
│  │  - Invariant: t_v=t0+L│  │  - m/s <-> knots     │  │ - Deduplication  │ │
│  └───────────────────────┘  └──────────────────────┘  └──────────────────┘ │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 Canonical NWP Schema (CanonicalRecord)                      │
│         [Rainfall, Dynamic Winds, RH, Geopotential, MSLP, CAPE]             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 Meteorological Feature Engineering Engine                   │
│   [Low-Level Jet, Shear, IVT Proxy, Orographic Lift, Coastal Convergence]   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Scientific Post-Processing Core Pipeline                  │
│       [Regime Classifier] ──► [Regime-Aware AI Post-Processor] ──► [FSS/XAI]│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Source Maturity Status Audit

| Data Source | Operational Role | Native Format | Resolution | Implementation Status | Active Connection Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NCMRWF NCUM** | Primary Target Deterministic NWP | GRIB2 / NetCDF | 12 km Regional / 4 km Nested | `IMPLEMENTED (ADAPTER)` | Offline / Calibrated Fallback |
| **NCMRWF NEPS** | Primary Target Probabilistic Ensemble | GRIB2 | 12 km (23 Members) | `IMPLEMENTED (ADAPTER)` | Offline / Calibrated Fallback |
| **NOAA GFS** | Development & Offline Fallback NWP | JSON REST / GRIB2 | 0.25° (~27 km) | `IMPLEMENTED (OPERATIONAL)` | **Active Operational Fallback** |
| **ECMWF ERA5** | Historical Reanalysis Training Benchmark | NetCDF / Zarr | 0.25° | `IMPLEMENTED (OPERATIONAL)` | Active Archive |
| **IMD Gridded** | Observational Ground Truth Calibration | Binary `.grd` / NetCDF | 0.25° Daily | `IMPLEMENTED (OPERATIONAL)` | Active Archive |
| **NASA GPM IMERG**| Satellite Precipitation Truth | HDF5 / NetCDF4 | 0.1° (~10 km) | `IMPLEMENTED (OPERATIONAL)` | Active Archive |
| **SRTM DEM** | Static Orography & Terrain Predictors | GeoTIFF | 90 m / 1 km | `IMPLEMENTED (OPERATIONAL)` | Active In-Memory |
| **Demo Synthesis** | Fallback Demonstration Synthesis | Canonical Schema | Point / Grid | `IMPLEMENTED (OPERATIONAL)` | Active Standby |

---

## 4. Source Compatibility Matrix

| Feature / Predictor | NCMRWF NCUM | NCMRWF NEPS | NOAA GFS | Demo Synthesis |
| :--- | :--- | :--- | :--- | :--- |
| **Precipitation (24h / hourly)** | `AVAILABLE` | `AVAILABLE` | `AVAILABLE` | `AVAILABLE` |
| **850 hPa U & V Winds** | `AVAILABLE` | `AVAILABLE` | `AVAILABLE` | `AVAILABLE` |
| **700 hPa U & V Winds** | `AVAILABLE` | `AVAILABLE` | `AVAILABLE` | `AVAILABLE` |
| **500 hPa U & V Winds** | `AVAILABLE` | `AVAILABLE` | `AVAILABLE` | `AVAILABLE` |
| **Relative Humidity (850/700/500)** | `AVAILABLE` | `AVAILABLE` | `AVAILABLE` | `AVAILABLE` |
| **CAPE (Convective Energy)** | `AVAILABLE` | `AVAILABLE` | `AVAILABLE` | `AVAILABLE` |
| **Mean Sea Level Pressure (MSLP)** | `AVAILABLE` | `AVAILABLE` | `AVAILABLE` | `AVAILABLE` |
| **Vertical Velocity ($\omega$)** | `AVAILABLE` | `AVAILABLE` | `DERIVABLE` | `AVAILABLE` |
| **Geopotential Height (850/500)** | `AVAILABLE` | `AVAILABLE` | `DERIVABLE` | `AVAILABLE` |
| **Outgoing Longwave Radiation (OLR)** | `DERIVABLE` | `NOT_AVAILABLE` | `DERIVABLE` | `DERIVABLE` |
| **Integrated Vapor Transport (IVT)** | `DERIVABLE` | `DERIVABLE` | `DERIVABLE` | `DERIVABLE` |
| **Orographic Lift Index** | `DERIVABLE` | `DERIVABLE` | `DERIVABLE` | `DERIVABLE` |
| **Coastal Convergence Index** | `DERIVABLE` | `DERIVABLE` | `DERIVABLE` | `DERIVABLE` |
| **Ensemble Spread / P10 / P90** | `NOT_AVAILABLE` | `AVAILABLE` | `NOT_AVAILABLE` | `AVAILABLE` |

---

## 5. Canonical Internal Schema: `CanonicalMeteorologicalRecord`

All data ingested through GRIB2, NetCDF, or REST feeds is mapped into a single immutable canonical representation:

```python
class CanonicalMeteorologicalRecord(BaseModel):
    # Temporal Coordinates
    timestamp: str                  # Forecast valid time (ISO 8601 UTC)
    forecast_initialization: str    # Model cycle initialization (ISO 8601 UTC)
    lead_time_hours: int            # Forecast step horizon (hours)
    
    # Spatial Coordinates
    latitude: float                 # WGS84 Latitude [-90.0, 90.0]
    longitude: float                # WGS84 Normalized Longitude [-180.0, 180.0]
    
    # Precipitation & Ensemble Spread
    rainfall: float                 # Point rainfall accumulation (mm)
    ensemble_mean: Optional[float]  # Ensemble mean (mm)
    ensemble_std: Optional[float]   # Ensemble standard deviation (mm)
    ensemble_p10: Optional[float]   # 10th percentile bound (mm)
    ensemble_p90: Optional[float]   # 90th percentile bound (mm)
    
    # Multi-Level Thermodynamics & Dynamics
    temperature_850: Optional[float] # Temperature at 850 hPa (K)
    relative_humidity_850: Optional[float] # RH at 850 hPa (%)
    u850: Optional[float]           # Zonal wind at 850 hPa (m/s)
    v850: Optional[float]           # Meridional wind at 850 hPa (m/s)
    geopotential_850: Optional[float] # Geopotential height at 850 hPa (gpm)
    vertical_velocity: Optional[float] # Omega vertical velocity (Pa/s)
    mslp: Optional[float]           # Mean Sea Level Pressure (hPa)
    cape_j_kg: Optional[float]      # CAPE (J/kg)
    
    # Provenance & Operational Quality
    data_source: str                # Unique identifier of originating source
    data_quality: str               # 'OPERATIONAL_VERIFIED', 'FALLBACK_OPERATIONAL', 'STALE_DATA'
    is_demo: bool                   # True if demo/fallback
```

---

## 6. Centralized Unit Normalization Standards

| Quantity | Input Variants | Canonical Unit | Transformation Applied |
| :--- | :--- | :--- | :--- |
| **Precipitation** | `kg m**-2`, `kg/m^2`, `m` | `mm` | $1\text{ kg m}^{-2} \equiv 1\text{ mm}$; $m \times 1000$ |
| **Temperature** | `Celsius`, `Fahrenheit`, `K` | `Kelvin (K)` / `°C` | $T_K = T_C + 273.15$ |
| **Pressure** | `Pascals (Pa)`, `bar`, `atm` | `hPa` | $P_{\text{hPa}} = P_{\text{Pa}} / 100.0$ |
| **Wind Speed** | `knots (kt)`, `km/h`, `mph` | `m/s` | $V_{\text{m/s}} = V_{\text{kt}} \times 0.514444$ |
| **Relative Humidity** | Ratio $[0.0, 1.0]$, `%` | `%` | $\text{RH}_{\%} = \text{fraction} \times 100.0$ |
| **Specific Humidity** | `kg/kg` | `g/kg` | $q_{\text{g/kg}} = q_{\text{kg/kg}} \times 1000.0$ |

---

## 7. Spatial and Temporal Normalization

1. **Longitude Standard**: All longitudes are normalized into the $[-180.0^\circ, 180.0^\circ]$ domain using:
   $$\text{norm\_lon} = ((\text{lon} + 180.0) \pmod{360.0}) - 180.0$$
2. **South Asia Domain Envelope**: Checked against $[6.0^\circ\text{N}, 38.0^\circ\text{N}]$, $[66.0^\circ\text{E}, 100.0^\circ\text{E}]$.
3. **Temporal Invariant**: The system strictly validates:
   $$\text{valid\_time} \equiv \text{initialization\_time} + \text{lead\_time\_hours}$$
   Any record violating this invariant is flagged `CORRUPTED_TIMESTAMP` and rejected from the downstream post-processing pipeline.

---

## 8. Multi-Tier Fallback Source Routing & Priority

The operational router enforces deterministic source prioritization:

```
┌─────────────────────────────────────────────────────────┐
│ Tier 1: Primary NCMRWF NCUM Regional 12km               │
│ [If live connection active & valid GRIB2 stream present]│
└───────────────────────────┬─────────────────────────────┘
                            │ (If unavailable)
                            ▼
┌─────────────────────────────────────────────────────────┐
│ Tier 2: Secondary NCMRWF NEPS Ensemble                  │
│ [If operational ensemble push active]                   │
└───────────────────────────┬─────────────────────────────┘
                            │ (If unavailable)
                            ▼
┌─────────────────────────────────────────────────────────┐
│ Tier 3: Development Fallback — NOAA GFS (Open-Meteo)    │
│ [Real-time 0.25° NWP REST API]                          │
└───────────────────────────┬─────────────────────────────┘
                            │ (If offline)
                            ▼
┌─────────────────────────────────────────────────────────┐
│ Tier 4: Calibrated Demo Fallback Synthesis              │
│ [Guaranteed standalone demo operation]                  │
└─────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Strict Truth-in-Attribution Rule**: If fallback occurs, the provenance record explicitly attaches `is_fallback: True`, `source_tier: DEVELOPMENT_FALLBACK`, and records the true originating source. The system **never** claims NCMRWF data when GFS or demo data is being utilized.

---

## 9. Data Quality & Freshness Engine

- **Quality States**: `VALID`, `PARTIAL`, `MISSING_VARIABLE`, `INVALID_METADATA`, `OUT_OF_RANGE`, `DUPLICATE`, `STALE`, `FALLBACK`.
- **Staleness Tolerance**: Configurable operational threshold ($30.0\text{ hours}$ for standard 00Z / 12Z NWP cycles).
- If $\Delta t = (t_{\text{current}} - t_{\text{init}}) > 30.0\text{ h}$, the payload is flagged:
  $$\text{quality\_state} = \text{DataQualityState.STALE}$$

---

## 10. Security & Credential Isolation

- **Zero Credentials in Git**: `.gitignore` strictly blocks `.env`, `.env.local`, `*.pem`, `*.key`, `*.json` credentials.
- **Config-Driven URLs**: All endpoints, ports, and access tokens are injected exclusively via environment variables (`NWP_BASE_URL`, `NCMRWF_FTP_URL`, `NCMRWF_API_KEY`).
- **Sanitized API Responses**: Public API endpoints scrub and exclude internal connection strings, passwords, or tokens.

---

## 11. Operational Readiness Level

Based on forensic evaluation of the codebase:

```
OPERATIONAL READINESS: LEVEL 1 — ADAPTER ARCHITECTURE & LOCAL INGESTION
```

- **Level 0 (Documented Only)**: Completed.
- **Level 1 (Adapter Architecture)**: **COMPLETED (Phase 10)**. Canonical schemas, GRIB2 ingestion engine, metadata validation, unit conversion, spatial normalization, ensemble processing, and priority fallback routing are fully implemented and verified with 17 unit tests.
- **Level 2 (Local Data Ingestion)**: Completed for historical archives (IMD, ERA5, Case Studies).
- **Level 3 (Validated Archived Operational Data)**: Target upon receiving official NCMRWF archived benchmark cycles.
- **Level 4 (Live Operational Feed)**: Target upon provisioning dedicated MoES / NCMRWF VPN gateway access.
