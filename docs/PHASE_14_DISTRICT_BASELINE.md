# PHASE 14 — CURRENT DISTRICT BASELINE & FORENSIC AUDIT

**SIH Problem Statement 26080**: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts  
**Ministry of Earth Sciences (MoES) / NCMRWF**  
**Document Classification**: Forensic Architectural Audit & Baseline Inventory  

---

## 1. Executive Summary

This forensic audit evaluates the pre-existing district decision-support layer within the PS26080 repository, documenting the exact baseline before Phase 14 enhancements. 

Prior to Phase 14, district rainfall estimation relied on **Point-Sampled Centroid Coordinate Extraction** (`POINT_SAMPLED_CENTROID`). While this served as a lightweight operational prototype, complex terrain (e.g., windward Western Ghats vs. leeward rain-shadow) and wide administrative boundaries necessitated upgrading to a formal **2D Grid → Polygon Area-Weighted Aggregation Engine** with precomputed spatial weights, multi-scale threshold exposure fractions, and machine-generated warning intelligence.

---

## 2. Inventory of Baseline Components

### 2.1 Backend Sources & Endpoints
- **District Provider**: `backend/app/data/sources/districts.py`
  - Defines `DistrictProvider` / `DistrictsSource` with 748-district framework directory and 14 representative synoptic centroids.
  - Coordinate reference: WGS84 (`EPSG:4326`).
  - Spatial bounding box: Latitude $[6.0^\circ\text{N}, 37.5^\circ\text{N}]$, Longitude $[68.0^\circ\text{E}, 98.0^\circ\text{E}]$.
- **Inference Coordinator**: `backend/app/postprocessing/inference.py`
  - Implements `generate_district_forecast()` and `get_all_district_forecasts()`.
  - Aggregates single-cell point estimates at $(\text{lat}_c, \text{lon}_c)$.
- **API Endpoint**: `GET /api/v1/postprocess/districts`
  - Returns `List[DistrictForecast]`.
  - Filters by `state`, `regime`, and `category`.

### 2.2 Decision Categories & Threshold Logic
- **Rainfall Categories**:
  - `NORMAL`: $R_{24h} < 64.5\text{ mm}$
  - `HEAVY_RAINFALL`: $64.5 \le R_{24h} < 115.6\text{ mm}$
  - `VERY_HEAVY_RAINFALL`: $115.6 \le R_{24h} < 204.5\text{ mm}$
  - `EXTREMELY_HEAVY_RAINFALL`: $R_{24h} \ge 204.5\text{ mm}$
- **Prototype Probability Escalation Triggers**:
  - Extreme rain trigger: $P(\ge 204.5\text{ mm}) \ge 0.25$
  - Very heavy rain trigger: $P(\ge 115.6\text{ mm}) \ge 0.40$
  - Heavy rain trigger: $P(\ge 64.5\text{ mm}) \ge 0.55$

### 2.3 Frontend Consumption
- **District Forecast Table**: `frontend/src/components/forecast/DistrictForecastTable.tsx`
  - Multi-column sorting across Raw NWP, Calibrated P50, Bias $\Delta$, Uncertainty, and Exceedance Probabilities.
  - Filterable by State, Regime, and Decision Category.
- **Cesium Globe**: `frontend/src/components/map/CesiumGlobe.tsx`
  - Smooth camera repositioning to district coordinates.
  - Telemetry inspect popover displaying calibrated metrics and prototype disclaimers.

---

## 3. Baseline Method vs Phase 14 Target

| Feature | Pre-Phase 14 Baseline | Phase 14 Target |
| :--- | :--- | :--- |
| **Spatial Method** | Point-Sampled Centroid (`POINT_SAMPLED_CENTROID`) | 2D Polygon Area-Weighted (`POLYGON_AREA_WEIGHTED`) |
| **Spatial Weights** | None (1:1 single nearest grid cell) | Precomputed normalized cell-polygon intersection weights |
| **Area Exposure** | Not calculated | Heavy, Very Heavy, Extreme area fractions ($0.0 \to 1.0$) |
| **Missing Coverage** | Implicitly ignored | Explicit `valid_area_fraction` & `INSUFFICIENT_SPATIAL_COVERAGE` |
| **Uncertainty Aggregation** | Point $P_{10}/P_{50}/P_{90}$ | Spatially aggregated distribution quantiles |
| **Bulletins** | None | Deterministic machine-generated plain-text bulletins |
| **Export Formats** | REST JSON only | JSON, CSV, GeoJSON FeatureCollections, GeoPackage |
| **Population Weighting** | `NOT_AVAILABLE` | `NOT_AVAILABLE` (Strict rule: zero fabrication) |
| **Official Status** | Prototype decision support | Prototype decision support (Strictly not IMD statutory warning) |

---

## 4. Preservation Invariant

The point-sampled centroid method remains fully preserved as an active baseline (`POINT_SAMPLED_CENTROID`) for side-by-side verification and regression testing. Existing endpoints and schemas maintain 100% backward compatibility.
