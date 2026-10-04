# SIH26080 — OPERATIONAL DASHBOARD ARCHITECTURE & SPATIAL FORECAST SPECIFICATION

**Target Problem Statement:** SIH26080 — Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts  
**Organization:** Ministry of Earth Sciences (MoES)  
**Department:** National Centre for Medium Range Weather Forecasting (NCMRWF)  
**System Name:** MEGHANETRA (PS26080 Spatial Calibration Platform)  
**Architecture Classification:** Prospective Prototype / Scientific Demonstration Platform  

---

## 1. SYSTEM ARCHITECTURAL OVERVIEW

The MEGHANETRA (PS26080) frontend is built on **Next.js 16 (App Router), React 19, CesiumJS 1.145 (3D Geospatial Engine), and Vanilla CSS Design Tokens**. The dashboard connects directly to the Phase 3 meteorological AI post-processing engine (`FastAPI` backend on port `8001`).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                     MEGHANETRA HUD                                     │
│                        Header Bar (Model Switcher & Verification Hub)                  │
├────────────────────────────────────────┬───────────────────────────────────────────────┤
│                                        │  FLOATING TELEMETRY MAP HUD                   │
│   CESIUM 3D GLOBE                      │  • Monsoon Regime & Confidence (81%)          │
│   • Layer 1: AI Calibrated (Regime ML) │  • Selected Model Output (82.4 mm/24h)        │
│   • Layer 2: Raw NWP Baseline (GFS)    │  • Raw NWP Reference (65.1 mm/24h)            │
│   • Layer 3: Bias Delta (+17.3 mm)     │  • Bias Correction Delta (+17.3 mm)           │
│   • Layer 4: Heavy Rain Prob (74%)     │  • Exceedance P(≥64.5mm) & P(≥115.6mm)        │
│   • Layer 5: Dynamic Weather Regime    │  • Uncertainty Distribution (P10 ── P50 ── P90)│
│   • Layer 6: Uncertainty Spread (Width)│  • Operational Mode Attribution               │
├────────────────────────────────────────┴───────────────────────────────────────────────┤
│   EVIDENCE STRIP (4-Method Interactive Comparative Matrix)                             │
│   [1. Raw NWP] ─── [2. Quantile Mapping] ─── [3. Global ML] ─── [4. Regime-Aware AI]   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│   DISTRICT FORECAST TABLE (748 Districts Hierarchy, Sorting & Map Repositioning)       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│   WHY ASSESSMENT & EXPLAINABILITY (Synoptic Radar, Tree SHAP & Isohyet Contours)       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│   FRESHNESS TIMELINE & TECHNICAL PROVENANCE AUDIT DRAWER                               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. API INTEGRATION SPECIFICATION

The frontend maintains zero mock data in production, binding strictly to backend endpoints:

| Endpoint | Method | Component Consumer | Function & Return Payload |
| :--- | :---: | :--- | :--- |
| `/api/v1/predict` | `POST` | `Dashboard Core` | Unified synoptic diagnosis, 4-model post-processing, probabilities, and provenance |
| `/api/v1/postprocess/districts` | `GET` | `DistrictForecastTable` | Administrative hierarchy (748 districts) with area-weighted mean rainfall and regime |
| `/api/v1/postprocess/models` | `GET` | `Header`, `EvidenceStrip` | Model registry catalog, checkpoint versions, feature schemas, and training histories |
| `/api/v1/postprocess/compare` | `GET/POST`| `WhyAssessment` | 4-model comparison matrix (Raw, EQM, Global ML, Regime ML) |
| `/api/v1/postprocess/verification`| `GET` | `VerificationModal` | Prospective evaluation metrics (RMSE, MAE, Bias, POD, FAR, CSI, ETS, FSS) |
| `/api/v1/regime` | `GET` | `MapHud`, `EvidenceStrip` | Real-time synoptic weather regime classification and physical drivers |
| `/api/v1/data/status` | `GET` | `Header`, `AuditPanel` | Upstream telemetry streams health (NWP, DWR Radar, NASA POWER, Terrain) |

---

## 3. UNIFIED FORECAST STATE CONTRACT

State across all UI panels is synchronized via the standardized `ForecastState` contract defined in [`frontend/src/lib/types.ts`](file:///c:/Users/srija/OneDrive/Desktop/New%20folder/frontend/src/lib/types.ts):

```typescript
export interface ForecastState {
  timestamp: string;
  forecast_initialization: string;
  lead_time_hours: number;
  latitude: number;
  longitude: number;
  district_name: string;
  state_name: string;
  data_source: string;
  is_demo: boolean;
  selected_model: 'raw_nwp' | 'quantile_mapping' | 'global_ml' | 'regime_aware_ml';
  active_layer: 'ai_calibrated' | 'raw_nwp' | 'bias_delta' | 'heavy_prob' | 'regime' | 'uncertainty';
  regime: WeatherRegimeType;
  regime_probabilities: Record<string, number>;
  regime_confidence: number;
  raw_nwp_mm: number;
  eqm_mm: number;
  global_ml_mm: number;
  regime_aware_mm: number;
  bias_delta_mm: number;
  heavy_probability: number;
  very_heavy_probability: number;
  extreme_probability: number;
  p10_mm: number;
  p50_mm: number;
  p90_mm: number;
  uncertainty_width_mm: number;
  model_version: string;
  data_freshness_status: string;
}
```

---

## 4. CESIUM 3D SPATIAL INTELLIGENCE LAYERS

The Cesium 3D Globe renders high-resolution terrain relief, Esri aerial imagery, and interactive rainfall layers:

1. **Layer 1: AI Calibrated Rainfall (`ai_calibrated`):**
   - Displays Regime-Aware ML corrected rainfall field (WGS84 isohyet contours).
   - Dynamic legend scale: $0\text{ mm} \rightarrow 35\text{ mm} \rightarrow 64.5\text{ mm} \rightarrow 115.6\text{ mm}+$.
2. **Layer 2: Raw NWP Baseline (`raw_nwp`):**
   - Displays direct numerical model output (NOAA GFS / NCMRWF NCUM).
3. **Layer 3: Bias Correction Delta (`bias_delta`):**
   - Displays spatial error correction: $\Delta = \text{Corrected} - \text{Raw NWP}$.
   - Diverging scale: $-30\text{ mm}$ (dampening) to $+30\text{ mm}$ (orographic/coastal enhancement).
4. **Layer 4: Heavy Rainfall Probability (`heavy_prob`):**
   - Probability of exceeding heavy rainfall threshold ($P(\ge 64.5\text{ mm})$).
5. **Layer 5: Weather Regime (`regime`):**
   - Spatial footprint of diagnosed synoptic mechanism (Active, Break, Orographic, LPS, Coastal).
6. **Layer 6: Uncertainty Spread (`uncertainty`):**
   - Uncertainty width: $P_{90} - P_{10}$ (narrow spread = high confidence, wide spread = ensemble dispersion).

### Globe Click Interaction
Clicking any point on the Cesium 3D terrain executes a cartographic pick, extracting exact coordinates and presenting a telemetry popover with coordinates, district name, active regime, raw NWP, calibrated rainfall, bias delta, and exceedance probabilities.

---

## 5. DISTRICT AGGREGATION & ADMINISTRATIVE HIERARCHY

District-level precipitation metrics are calculated exclusively in the backend (`DistrictProvider` in [`backend/app/data/sources/districts.py`](file:///c:/Users/srija/OneDrive/Desktop/New%20folder/backend/app/data/sources/districts.py)) using scientifically validated spatial aggregation:
- **Precipitation Accumulation:** Area-weighted mean across district bounding polygons.
- **Extreme Events:** Peak maximum grid point value within district boundaries.
- **Heavy Rain Probability:** Exceedance fraction based on calibrated ensemble spreads.

When a district is selected in `DistrictForecastTable`, the Cesium camera flies to the district centroid, and telemetry HUD, regime drivers, and explanation panels synchronize instantly.

---

## 6. MODEL COMPARISON & SWITCHING ENGINE

The user can toggle seamlessly between all 4 post-processing methodologies:
1. **Raw NWP Baseline:** Direct uncalibrated GFS/NCUM numerical forecast.
2. **Empirical Quantile Mapping (EQM):** Statistical cumulative distribution transfer function.
3. **Global ML Correction:** Pan-India stationary gradient-boosted regressor.
4. **Regime-Aware AI Post-Processing:** Soft-conditioned mixture-of-experts model conditioned on synoptic weather regime.

Switching models preserves identical forecast time, target coordinates, and atmospheric input fields, making the comparative scientific calibration immediately evident.

---

## 7. PROVENANCE AUDIT & DEMO AUTHENTICITY

The system enforces strict provenance logging in `AuditPanel`:
- **Data Source:** Explicitly distinguishes `GFS DEMO FALLBACK (Open-Meteo 0.25°)` from `NCMRWF NCUM Global 12km`.
- **Observation Target:** `IMD DWR / NASA POWER Daily Gauges`.
- **Regime Engine:** `RegimeEngine v2.1 (MoES)`.
- **Post-Processor Checkpoint:** `Regime-Aware Neural ML v1.0`.
- **Lead Time:** `T+24h`.
- **Authenticity Classification:** Labeled `DEMO / SYNTHETIC FALLBACK` unless live NCMRWF credentials and feeds are active.
