# END-TO-END SCIENTIFIC & CODE TRACEABILITY

## SIH26080 — Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts
**Ministry of Earth Sciences (MoES) · National Centre for Medium Range Weather Forecasting (NCMRWF)**

---

### Execution Pipeline Traceability Map

This document establishes 1-to-1 code traceability from raw numerical and observational data ingestion through AI post-processing, probabilistic calibration, spatial aggregation, and 3D Cesium visualization.

```
[STAGE 1: NWP Ingestion]
        │
        ▼
[STAGE 2: Canonical Normalization & QC]
        │
        ▼
[STAGE 3: Meteorological Feature Engineering]
        │
        ▼
[STAGE 4: Synoptic Weather Regime Intelligence]
        │
        ▼
[STAGE 5: 4-Model Post-Processing Engine]
        │
        ▼
[STAGE 6: Probabilistic Uncertainty & Exceedance]
        │
        ▼
[STAGE 7: Spatial & District Aggregation]
        │
        ▼
[STAGE 8: 3D Cesium Dashboard & XAI Suite]
```

---

### Stage-by-Stage Traceability Matrix

#### Stage 1: Raw Numerical Weather Prediction (NWP)
* **Input:** Target coordinates $(\text{lat}, \text{lon})$, forecast date $T_0$, forecast horizon (24h).
* **Processing:** Queries NWP data streams; extracts surface precipitation, 850/700/500 hPa winds, relative humidity, CAPE, MSLP.
* **Output:** `RawNwpPointForecast` / `CanonicalMeteorologicalRecord`.
* **Source Files:**
  - `backend/app/services/nwp_client.py` (`OpenMeteoNwpClient`)
  - `backend/app/data/sources/ncmrwf.py` (`NCMRWFAdapter`)
* **API Route:** Internal service call / `GET /api/v1/data/status`
* **Mode:** **REAL GFS FALLBACK (0.25° Seamless)** / Modular target for **NCMRWF NCUM Global 12km**.

#### Stage 2: Canonical Meteorological Normalization & QC
* **Input:** Raw JSON responses from heterogeneous providers (NWP, NASA POWER, RainViewer, Sentinel-2).
* **Processing:** Unit conversion (Kelvin to Celsius, m/s to knots, Pa to hPa), longitude domain normalization $[-180, 180]$, physical bounds verification, non-finite value imputation.
* **Output:** Validated `CanonicalMeteorologicalRecord` with `QC_PASSED` flag.
* **Source Files:**
  - `backend/app/data/schemas/meteorology.py` (`CanonicalMeteorologicalRecord`)
  - `backend/app/services/weather_service.py` (`WeatherObservationService`)
* **Mode:** **REAL / DETERMINISTIC**.

#### Stage 3: Meteorological Feature Engineering
* **Input:** Standardized canonical meteorological fields and high-resolution DEM topography.
* **Processing:** Computes low-level wind shear, 850 hPa moisture flux transport ($q \cdot V_{850}$), orographic lifting index ($\mathbf{u} \cdot \nabla z$), coastal proximity index, and multi-day accumulation lags ($D-1, D-2, D-3$).
* **Output:** `MeteorologicalFeatureSet` with 37 engineered feature dimensions.
* **Source Files:**
  - `backend/app/services/feature_builder.py` (`FeatureBuilder`)
  - `backend/app/data/processing/features.py` (`FeatureExtractor`)
* **Mode:** **REAL COMPUTATION**.

#### Stage 4: Synoptic Weather Regime Intelligence Engine
* **Input:** `MeteorologicalFeatureSet` (LLJ speed, direction, Monsoon Trough latitude, OLR convection, CAPE).
* **Processing:** Hierarchical Bayesian and heuristic regime classifier computing continuous posterior probabilities across 6 South Asian monsoon regimes:
  1. *Active Monsoon* ($P \ge 0.50$ during strong westerlies, deep trough)
  2. *Break Monsoon* ($P \ge 0.50$ when trough shifts to Himalayan foothills)
  3. *Monsoon Low / LPS* ($P \ge 0.50$ with cyclonic vortex & low MSLP)
  4. *Coastal Convergence* ($P \ge 0.50$ along western/eastern peninsular coast)
  5. *Orographic Forcing* ($P \ge 0.50$ over Western Ghats / Meghalaya slope)
  6. *Western Disturbance* ($P \ge 0.50$ over Northwest India)
* **Output:** `RegimeResponse` with primary regime, confidence %, and 6-regime probability vector $\mathbf{w}$.
* **Source Files:**
  - `backend/app/regime/regime_classifier.py` (`WeatherRegimeClassifier`)
  - `backend/app/services/regime_service.py` (`WeatherRegimeService`)
* **API Route:** `GET /api/v1/regime` / `POST /api/v1/regime/classify`
* **Mode:** **REAL REGIME CLASSIFIER**.

#### Stage 5: Four-Model Post-Processing Benchmark Engine
* **Input:** `PostProcessingInput` (raw NWP rainfall, lead time, coordinates, regime probabilities, atmospheric features).
* **Processing:** Concurrent execution of 4 post-processing pipelines:
  1. **Raw NWP:** $\hat{y}_{raw} = y_{NWP}$ ($\Delta_{bias} = 0.0\text{ mm}$)
  2. **Empirical Quantile Mapping:** $\hat{y}_{eqm} = F_{obs}^{-1}(F_{nwp}(y_{raw}))$
  3. **Global ML Regressor:** $\hat{y}_{gml} = y_{raw} + f_{global}(\mathbf{x})$ (`HistGradientBoostingRegressor`)
  4. **Regime-Aware ML:** $\hat{y}_{regime} = y_{raw} + \sum_{k=1}^{6} w_k \cdot f_k(\mathbf{x}) + g(\mathbf{w}, \mathbf{x})$
* **Output:** `ForecastComparisonSummary` / `PostProcessingOutput` with calibrated rainfall and bias deltas.
* **Source Files:**
  - `backend/app/postprocessing/inference.py` (`PostProcessingInferenceEngine`)
  - `backend/app/postprocessing/regime_aware_ml.py` (`RegimeAwareMLModel`)
  - `backend/app/postprocessing/global_ml.py` (`GlobalMLModel`)
  - `backend/app/postprocessing/quantile_mapping.py` (`QuantileMappingModel`)
  - `backend/app/postprocessing/base.py` (`PostProcessingInput`, `PostProcessingOutput`)
* **API Routes:**
  - `POST /api/v1/postprocess/correct`
  - `POST /api/v1/postprocess/compare`
  - `GET /api/v1/postprocess/models`
* **Mode:** **REAL TRAINED MODELS (Fit on 2018–2022 historical datasets)**.

#### Stage 6: Probabilistic Uncertainty & Heavy Rain Exceedance
* **Input:** Calibrated point rainfall $\hat{y}$, residual variance, diagnosed regime spread.
* **Processing:** Computes calibrated parametric quantiles:
  - $P10$ (10th percentile lower uncertainty bound)
  - $P50$ (Median expected rainfall)
  - $P90$ (90th percentile upper uncertainty bound)
  - Uncertainty Interval Width $= P90 - P10$
  - Computes exceedance probabilities: $P(\text{Precip} \ge 64.5\text{mm})$, $P(\text{Precip} \ge 115.6\text{mm})$, $P(\text{Precip} \ge 204.5\text{mm})$.
* **Output:** `HeavyRainfallProbabilities` and `UncertaintyQuantiles`.
* **Source Files:**
  - `backend/app/services/risk_fusion_service.py` (`RiskFusionService`)
  - `backend/app/postprocessing/regime_aware_ml.py`
* **Mode:** **REAL PROBABILISTIC CALIBRATION**.

#### Stage 7: Spatial & District-Level Aggregation
* **Input:** Gridded post-processed fields across 748 Indian administrative districts.
* **Processing:** Computes area-weighted mean rainfall, maximum district rainfall, exceedance fractions, and dominant district regime.
* **Output:** `List[DistrictForecast]` with searchable and sortable district records.
* **Source Files:**
  - `backend/app/services/district_service.py` (`DistrictForecastService`)
  - `backend/app/schemas/postprocess.py` (`DistrictForecast`)
* **API Route:** `GET /api/v1/postprocess/districts`
* **Mode:** **REAL SPATIAL AGGREGATION**.

#### Stage 8: Unified Orchestrator & Cesium 3D Dashboard
* **Input:** Client request payload `UnifiedPredictionRequest`.
* **Processing:** Executes complete pipeline, bundles telemetry, generates WGS84 GeoJSON isohyet contours, and logs provenance.
* **Output:** `UnifiedPredictionResponse`.
* **Source Files:**
  - `backend/app/services/unified_prediction_service.py` (`UnifiedPredictionService`)
  - `frontend/src/app/page.tsx` (`MeghanetraDashboard`)
  - `frontend/src/components/map/CesiumGlobe.tsx` (6 3D Geospatial Layers)
  - `frontend/src/components/explainability/WhyAssessment.tsx` (5-Step Visual Causal Flow & Tree SHAP)
  - `frontend/src/components/verification/VerificationModal.tsx` (Verification Benchmark Hub)
  - `frontend/src/components/provenance/AuditPanel.tsx` (Data Provenance Ledger)
* **API Route:** `POST /api/v1/predict`
* **Mode:** **PRODUCTION VERIFIED**.
