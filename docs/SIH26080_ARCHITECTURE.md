# SIH26080 SYSTEM ARCHITECTURE

## "Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts"
**Ministry of Earth Sciences (MoES) · National Centre for Medium Range Weather Forecasting (NCMRWF)**

---

### End-to-End System Dataflow Diagram

```
+─────────────────────────────────────────────────────────────────────────────+
|                          1. NWP & METEOROLOGICAL DATA                       |
|   • Numerical Forecasts (NCMRWF NCUM 12km / GFS 0.25° Fallback)             |
|   • Synoptic Telemetry (Low-Level Jet, Monsoon Trough, OLR, IVT, CAPE)      |
|   • Observation Target (IMD 0.25° Gridded Rainfall / DWR Radar / Gauges)    |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
|                    2. CANONICAL DATA PIPELINE & QUALITY CONTROL             |
|   • Unit Normalization & Spatial Interpolation (WGS84 0.25° Mesh)           |
|   • Non-finite value rejection & missing variable assertion                 |
|   • Chronological split validation & temporal zero-leakage enforcement      |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
|                         3. FEATURE ENGINEERING LAYER                         |
|   • Dynamic Wind Shear & Moisture Flux Divergence Calculation                |
|   • Orographic Lifting Index ($u \cdot \nabla z$) from High-Res DEM          |
|   • Multi-day Lagged Cumulative Indices (D-1, D-2, D-3 precipitation)        |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
|                    4. WEATHER REGIME INTELLIGENCE ENGINE                    |
|   • Physical Diagnostics & Convective Classifier                             |
|   • 6-Regime Multi-Label Probabilities:                                     |
|     Active Monsoon · Break Monsoon · Monsoon Low/LPS ·                       |
|     Coastal Convergence · Orographic Forcing · Western Disturbance           |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
|             5. FOUR-MODEL POST-PROCESSING BENCHMARK ENGINE                  |
|                                                                             |
|   [1] RAW NWP BASELINE          ──> Direct numerical output (No Correction) |
|   [2] QUANTILE MAPPING (EQM)    ──> Empirical CDF transfer function         |
|   [3] GLOBAL ML REGRESSOR       ──> Stationary HistGradientBoosting ML      |
|   [4] REGIME-AWARE AI (PS26080) ──> Soft-Conditioned Mixture of Experts     |
|                                     Residual Learning: $\hat{y} = y_{raw} + \hat{\epsilon}$ |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
|                 6. PROBABILISTIC UNCERTAINTY & EXCEEDANCE                   |
|   • P10 / P50 / P90 Uncertainty Bands                                       |
|   • Calibrated Heavy Rainfall Probabilities ($P \ge 64.5\text{mm}$, $P \ge 115.6\text{mm}$) |
|   • IMD Severity Category Mapping (Moderate, Heavy, Very Heavy, Extreme)    |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
|                    7. SPATIAL & DISTRICT AGGREGATION                        |
|   • Area-Weighted Mean Precipitation for 748 Administrative Districts       |
|   • District-Level Exceedance Probability Tiers & Risk Scoring              |
|   • GeoJSON Contour Isohyet Field Generation (WGS84)                        |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
|              8. OPERATIONAL CESIUM 3D DASHBOARD & XAI SUITE                 |
|   • Interactive 3D Globe with 6 Geospatial Layers:                          |
|     1. AI Calibrated Rainfall  2. Raw NWP Baseline  3. Bias Delta ($\Delta$)  |
|     4. Heavy Rain Probability  5. Monsoon Regime    6. Uncertainty Width    |
|   • Causal Post-Processing Story (Raw NWP -> Regime -> Drivers -> AI Rain)  |
|   • Tree SHAP Feature Attribution & Atmospheric Explanations                |
|   • Scientific Verification Hub (RMSE, CSI, ETS, POD, FAR, FSS)             |
|   • Transparent Data Provenance & Operational Audit Ledger                  |
+─────────────────────────────────────────────────────────────────────────────+
```

---

### Component Breakdown

#### A. Backend Architecture (FastAPI Service Layer)
* **`backend/app/services/regime_service.py`**: Meteorological feature extraction and hierarchical Bayesian/heuristic regime classification engine.
* **`backend/app/services/postprocessing_service.py`**: Core inference engine managing Raw NWP, Empirical Quantile Mapping, Global ML, and Regime-Aware Mixture of Experts.
* **`backend/app/services/verification_service.py`**: Evaluation module computing WMO standard verification metrics (RMSE, MAE, Mean Bias, POD, FAR, CSI, ETS, FSS).
* **`backend/app/services/district_service.py`**: Spatial aggregation module extracting district-level forecasts and risk scores across India.
* **`backend/app/services/unified_prediction_service.py`**: Orchestrator executing the complete multi-source pipeline and returning structured JSON payloads with provenance metadata.

#### B. Frontend Architecture (Next.js 16 + CesiumJS)
* **`Header.tsx`**: Top-level identity, active post-processor switcher, gateway telemetry status, and verification hub launcher.
* **`CesiumGlobe.tsx`**: High-performance 3D terrain viewer rendering 6 multi-spectral geospatial layers and WGS84 isohyet contours.
* **`MapHud.tsx`**: Floating synoptic summary HUD displaying active regime, calibrated 24h rainfall, and P10–P90 uncertainty distribution.
* **`EvidenceStrip.tsx`**: 4-model comparison card deck highlighting calibrated rainfall, bias delta, and baseline meteograms.
* **`WhyAssessment.tsx`**: Meteorological explainability suite featuring the 5-step "Why AI Corrected" causal narrative, synoptic telemetry cards, and Tree SHAP feature attribution.
* **`DistrictForecastTable.tsx`**: Sortable, searchable district forecast hierarchy table with camera focus synchronization.
* **`VerificationModal.tsx`**: Interactive verification hub displaying empirical skill benchmarks across thresholds and regimes.
* **`AuditPanel.tsx`**: Scientific data provenance drawer exposing model versions, data source status, execution latencies, and raw JSON.
