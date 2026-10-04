# Phase 8 — District-Level Decision Support & Prototype Warning System

**SIH Problem Statement 26080**: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts  
**Ministry of Earth Sciences (MoES) / NCMRWF**  
**Document Classification**: Technical Architecture & Scientific Decision-Support Specification  

---

## 1. Purpose & Scope

The purpose of Phase 8 is to transform gridded meteorological numerical weather prediction (NWP) forecasts and regime-aware machine learning post-processed fields into standardized administrative **District-Level Decision-Support Information** and **Prototype Rainfall Outlooks**.

Disaster management agencies, including the National Disaster Management Authority (NDMA), State Disaster Management Authorities (SDMAs), and District Disaster Management Authorities (DDMAs), operate along administrative boundaries. Gridded forecasts alone ($0.25^\circ \times 0.25^\circ \approx 27\text{ km} \times 27\text{ km}$) do not directly correspond to district jurisdictions. Phase 8 bridges this operational gap while strictly adhering to scientific transparency and institutional disclaimer standards.

```
+-------------------------------------------------------------+
|                     GRID / NWP FORECAST                     |
|           (NCMRWF NCUM 12km / GFS 0.25° Gridded Fields)     |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|              REGIME-AWARE AI POST-PROCESSING                |
|      (Physics-Guided Gradient Boosted Error Correction)     |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|             CALIBRATED RAINFALL + UNCERTAINTY               |
|            (P10 Lower, P50 Median, P90 Upper Bound)         |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                DISTRICT SPATIAL AGGREGATION                 |
|       (Point-Sampled Centroid Coordinate Extraction)        |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|       HEAVY / VERY HEAVY / EXTREME THRESHOLD ANALYSIS       |
|    (≥64.5 mm/24h, ≥115.6 mm/24h, ≥204.5 mm/24h Analysis)   |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|              DISTRICT DECISION-SUPPORT PRODUCT              |
|        (Deterministic Outlook Category & Scientific Basis)  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|               PROTOTYPE WARNING VISUALIZATION               |
|      (Cesium 3D Globe + Synchronized District Hierarchy)    |
+-------------------------------------------------------------+
```

> [!IMPORTANT]
> **Strict Institutional Disclaimer**: This system is a **PROTOTYPE DECISION-SUPPORT TOOL** for meteorological and disaster management research. It is **NOT** an official warning-generation platform and does **NOT** issue official IMD warnings, red alerts, or statutory advisories. Statutory forecasts and warnings in India are solely issued by the **India Meteorological Department (IMD)**.

---

## 2. District Dataset & Administrative Framework

The system maps district-level forecast aggregations based on the Survey of India administrative division directory.

| Property | Value / Specification |
| :--- | :--- |
| **Administrative Framework** | Survey of India Administrative Framework |
| **Cataloged Districts** | 748 Administrative Districts (National Framework) |
| **Programmatic Prototype Directory** | 14 Curated Regime-Representative Districts |
| **Coordinate Reference System** | WGS84 (`EPSG:4326`) |
| **Spatial Bounding Box** | India Domain: Latitude $[6.0^\circ\text{N}, 37.5^\circ\text{N}]$, Longitude $[68.0^\circ\text{E}, 98.0^\circ\text{E}]$ |
| **Primary Identifier** | Stable State-Prefixed District Code (e.g. `MH_SATARA`, `ML_EAST_KHASI_HILLS`) |

The 14 representative districts are curated to encompass all synoptic meteorological regimes of the Indian Summer Monsoon:
1. **Mumbai City (`MH_MUMBAI_CITY`)**: Coastal Convergence (Maharashtra)
2. **Mumbai Suburban (`MH_MUMBAI_SUBURBAN`)**: Coastal Urban Hydrology (Maharashtra)
3. **Thane (`MH_THANE`)**: Coastal / Near-Ghat Convergence (Maharashtra)
4. **Raigad (`MH_RAIGAD`)**: Coastal Konkan Lowlands (Maharashtra)
5. **Ratnagiri (`MH_RATNAGIRI`)**: South Konkan Heavy Precipitation Zone (Maharashtra)
6. **Sindhudurg (`MH_SINDHUDURG`)**: Southern Coastal Foothills (Maharashtra)
7. **Satara (`MH_SATARA`)**: Western Ghats Windward Orographic Lifting (Maharashtra)
8. **Pune (`MH_PUNE`)**: Western Ghats Leeward Rain-Shadow Zone (Maharashtra)
9. **Nagpur (`MH_NAGPUR`)**: Central India Core Monsoon / Break Monsoon Zone (Maharashtra)
10. **East Khasi Hills (`ML_EAST_KHASI_HILLS`)**: Meghalaya Plateau Orographic Funneling (Meghalaya)
11. **Chennai (`TN_CHENNAI`)**: Coromandel Coast / Coastal Front (Tamil Nadu)
12. **Srinagar (`JK_SRINAGAR`)**: Western Disturbance / Himalayan Basin (Jammu & Kashmir)
13. **Puri (`OD_PURI`)**: Bay of Bengal Monsoon Low / LPS Landfall Track (Odisha)
14. **Ernakulam (`KL_ERNAKULAM`)**: Malabar Coastal Monsoon Onset Zone (Kerala)

---

## 3. Critical 748 vs 766 Reconciliation

### Audit Findings
- **Current Maintained Count**: 748 districts.
- **Audit / Reference Target Count**: 766 districts (2021–2024 Census & state reorganization listings).
- **Dataset Vintage**: 
  - The 748 count corresponds to the 2019–2021 Survey of India / Local Government Directory (LGD) administrative census baseline following the reorganization of Jammu & Kashmir / Ladakh and initial Telangana district restructuring.
  - The 766 count reflects subsequent 2022–2024 sub-district bifurcations in states such as Madhya Pradesh (Mauganj, Pandhurna), Rajasthan, and Punjab (Malerkotla).
- **Repository Verification**:
  - The codebase previously cataloged the framework as 748 districts.
  - A verified 766-district polygon boundary shapefile is **not present** in the repository.
- **Resolution**:
  - **748-district prototype dataset retained; 766-district target dataset not present in the current repository.**
  - In strict compliance with scientific integrity rules, unverified shapefiles were not fabricated or downloaded merely to claim 766 districts. The prototype explicitly exposes this boundary lineage.

---

## 4. Geometry & Spatial Aggregation Methodology

### Implemented Methodology: Point-Sampled District Estimate
Due to the absence of heavy multi-polygon shapefile geometries in the lightweight operational REST tier:
- District rainfall is evaluated using **Point-Sampled Centroid Coordinate Extraction** (`POINT_SAMPLED_CENTROID`).
- Centroid coordinates $(\text{lat}_c, \text{lon}_c)$ are fed into the high-resolution terrain, atmospheric, and regime feature builder ($44$ synoptic and topographical features).
- The regime-aware ML post-processor computes the localized bias correction $\Delta$ and calibrated quantiles ($P_{10}, P_{50}, P_{90}$).

> [!NOTE]
> The UI and API explicitly label this method as `"POINT_SAMPLED_CENTROID"`. It is **not** misrepresented as an area-weighted polygon intersection.

---

## 5. Population Weighting Status

- **Status**: **NOT AVAILABLE**
- **Rationale**: High-resolution gridded Census population data (e.g. LandScan or Census 2011 gridded rasters) is not bundled in the core repository.
- **Design Rule**:
  - Population numbers are **never fabricated**.
  - Rainfall totals ($mm/24h$) and population exposure metrics are strictly decoupled.

---

## 6. IMD-Aligned Rainfall Thresholds

The system applies standard physical precipitation thresholds established by the India Meteorological Department:

| Category | Daily Rainfall Threshold ($R_{24h}$) | Operational Definition |
| :--- | :--- | :--- |
| **Normal / Moderate** | $< 64.5\text{ mm/24h}$ | Light to Moderate Precipitation |
| **Heavy Rainfall** | $64.5 \le R_{24h} < 115.6\text{ mm/24h}$ | Heavy Downpour Zone |
| **Very Heavy Rainfall** | $115.6 \le R_{24h} < 204.5\text{ mm/24h}$ | Severe Inundation Risk |
| **Extremely Heavy Rainfall** | $\ge 204.5\text{ mm/24h}$ | Exceptional Catastrophic Deluge |

Thresholds are centralized in `HeavyRainfallCalibrator` and uniformly enforced across backend models, schema validators, and frontend tables.

---

## 7. Probabilistic District Products & Uncertainty

For every district, the system produces:
1. **Calibrated 24h Rainfall P50**: Median forecast after regime-conditioned error reduction ($mm$).
2. **Raw NWP Baseline**: Uncalibrated model output ($mm$).
3. **AI Bias Delta ($\Delta$)**: Additive or multiplicative correction offset ($mm$).
4. **Uncertainty Quantiles**:
   - $P_{10}$: Lower forecast quantile (10th percentile).
   - $P_{50}$: Calibrated median forecast.
   - $P_{90}$: Upper forecast quantile (90th percentile).
   - Ensemble Spread: Standard error width $\sigma \approx \frac{P_{90} - P_{10}}{2.56}$.
5. **Calibrated Exceedance Probabilities**:
   - $P(\text{Rain} \ge 64.5\text{ mm})$: Heavy rain probability.
   - $P(\text{Rain} \ge 115.6\text{ mm})$: Very heavy rain probability.
   - $P(\text{Rain} \ge 204.5\text{ mm})$: Extremely heavy rain probability.
   - Enforces strict monotonicity: $P(\ge 64.5) \ge P(\ge 115.6) \ge P(\ge 204.5)$.

---

## 8. Deterministic Decision-Support Classification Logic

To eliminate subjective or uncalibrated risk scoring, category assignment follows a deterministic, transparent rule matrix:

```python
if calibrated_p50_mm >= 204.5 or extreme_prob >= 0.25:
    category = "EXTREMELY_HEAVY_RAINFALL"
    basis = f"Calibrated P50 ({calibrated_p50_mm:.1f} mm) or extreme probability ({extreme_prob*100:.1f}%) meets/exceeds 204.5 mm threshold."
elif calibrated_p50_mm >= 115.6 or very_heavy_prob >= 0.40:
    category = "VERY_HEAVY_RAINFALL"
    basis = f"Calibrated P50 ({calibrated_p50_mm:.1f} mm) or very heavy probability ({very_heavy_prob*100:.1f}%) meets/exceeds 115.6 mm threshold."
elif calibrated_p50_mm >= 64.5 or heavy_prob >= 0.55:
    category = "HEAVY_RAINFALL"
    basis = f"Calibrated P50 ({calibrated_p50_mm:.1f} mm) or heavy rain probability ({heavy_prob*100:.1f}%) meets/exceeds 64.5 mm threshold."
else:
    category = "NORMAL"
    basis = f"Calibrated P50 ({calibrated_p50_mm:.1f} mm) is below the 64.5 mm heavy-rainfall threshold."
```

Every response includes both the discrete `decision_support_category` and the explicit explanatory `decision_basis`.

---

## 9. REST API Contract

### Endpoint: `GET /api/v1/postprocess/districts`

#### Query Parameters
- `state` (optional string): Filter by State / UT (e.g. `Maharashtra`).
- `regime` (optional string): Filter by dominant regime (e.g. `OROGRAPHIC_RAINFALL`).
- `category` (optional string): Filter by decision category (e.g. `HEAVY_RAINFALL`).

#### Sample Response Payload
```json
[
  {
    "district_id": "MH_SATARA",
    "district_name": "Satara",
    "state_name": "Maharashtra",
    "lat": 17.6805,
    "lon": 73.9935,
    "raw_nwp_mm": 78.0,
    "corrected_mm": 114.5,
    "correction_delta_mm": 36.5,
    "uncertainty_lower_bound_mm": 76.0,
    "uncertainty_upper_bound_mm": 162.0,
    "ensemble_spread_mm": 33.6,
    "heavy_prob": 0.92,
    "very_heavy_prob": 0.54,
    "extreme_prob": 0.125,
    "dominant_regime": "OROGRAPHIC_RAINFALL",
    "regime_confidence": 0.88,
    "aggregation_method": "POINT_SAMPLED_CENTROID",
    "decision_support_category": "VERY_HEAVY_RAINFALL",
    "decision_basis": "Calibrated P50 (114.5 mm) or very heavy probability (54.0%) meets/exceeds 115.6 mm/24h threshold.",
    "provenance_status": "HELD_OUT_PROTOTYPE_EVALUATION",
    "is_official_imd_warning": false,
    "disclaimer": "Prototype model-derived decision support. Not an official IMD warning."
  }
]
```

---

## 10. Frontend User Experience & Geospatial Synchronization

1. **District Hierarchy Table (`DistrictForecastTable.tsx`)**:
   - Multi-column sorting (District, Regime, Raw NWP, Calibrated P50, Uncertainty, Bias $\Delta$, Heavy %, Very Heavy %, Extreme %).
   - Real-time search across district names, state names, and regime types.
   - Three-dimensional dropdown filters for State, Regime, and Decision-Support Category.
   - Decision-support status badges with color coding (Green: Normal, Yellow: Heavy, Orange: Very Heavy, Red: Extremely Heavy).
2. **Interactive District Outlook Detail Drawer**:
   - Full scientific telemetry card with P10/P50/P90 quantiles.
   - Exceedance probabilities breakdown.
   - Explicit scientific decision basis.
   - Quick action: "Fly 3D Camera & Analyze" (smooth Cesium repositioning).
   - Quick action: "Why Was This District Corrected?" (connects to `WhyAICorrected` / atmospheric synoptic analysis).
3. **Cesium 3D Globe Synchronization (`CesiumGlobe.tsx`)**:
   - Clicking any district smoothly flies the 3D camera to its terrain position.
   - Point inspection popover displays calibrated metrics and the mandatory prototype disclaimer.

---

## 11. Data Provenance & Verification

- **Provenance Mode**: `HELD_OUT_PROTOTYPE_EVALUATION` (or `DEMO DATA · SYNTHETIC / FALLBACK MODE`).
- **Ground Truth Observational Target**: IMD $0.25^\circ$ Daily Gridded Rainfall & DWR Radar QPE network.
- **Verification Metrics**: Evaluated across 800+ held-out test samples (2024–2025 Monsoon).

---

## 12. Known Limitations

1. **Geometry Granularity**: Prototype currently uses point-sampled centroid coordinates rather than multi-polygon area-weighted clipping.
2. **Census Reorganization**: 748-district Survey of India administrative baseline retained; post-2022 bifurcated 766-district dataset is not available in the local repository.
3. **Population Data**: Population exposure analytics are marked `NOT AVAILABLE` due to the lack of Census gridded rasters.
4. **Official Warning Authority**: Product is solely prototype decision support and must never be cited as an official IMD alert.
