# PS26080 — API Contract & Specification

> **Target Problem Statement**: SIH26080  
> **Title**: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts  
> **Organization**: Ministry of Earth Sciences (MoES) / National Centre for Medium Range Weather Forecasting (NCMRWF)

---

## 1. Architectural Overview & Endpoint Catalog

The backend exposes a unified, OpenAPI-compliant REST API supporting four forecast products (Raw NWP, Quantile Mapping, Global ML Correction, Regime-Aware ML Correction), hierarchical monsoon regime identification, multi-threshold heavy rainfall probabilities, district/grid forecast products with uncertainty bounds, and spatial verification skill metrics.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health check, service diagnostic states, and model asset readiness |
| `GET` | `/api/v1/models/health` | ML model memory status (Regime Classifier, AI Post-Processing Engine, SHAP explainer) |
| `POST` | `/api/v1/predict` | **Primary Unified Orchestrator**: Ingests coordinates & date; returns regime diagnosis, 4 post-processed forecast products, heavy rain probabilities, district aggregations, verification skill, and GeoJSON isohyet contours |
| `POST` | `/api/v1/forecast/regime` | Standalone hierarchical weather regime classification (Active/Break/Depression/Orographic/etc.) |
| `POST` | `/api/v1/forecast/postprocess` | Standalone 4-product post-processing comparison (Raw NWP vs QM vs Global ML vs Regime ML) |
| `POST` | `/api/v1/forecast/probabilities` | Multi-threshold heavy rainfall probability engine (Heavy, Very Heavy, Extremely Heavy) |
| `GET` | `/api/v1/forecast/verification` | Verification skill benchmark metrics (RMSE, ETS, CSI, POD, FAR, FSS across regimes) |
| `GET` | `/api/v1/data/nwp` | Raw Numerical Weather Prediction feed (NOAA GFS / NCMRWF NCUM grid) |
| `GET` | `/api/v1/data/radar` | Doppler weather radar volume reflectivity and Marshall-Palmer precipitation rate |

---

## 2. Pydantic / JSON Data Schemas

### 2.1. Request Schema: `ForecastRequest`
```json
{
  "latitude": 19.0760,
  "longitude": 72.8777,
  "prediction_date": "2024-07-15",
  "forecast_horizon_hours": 24,
  "nwp_source_preference": "auto",
  "location_name": "Mumbai Metropolitan Region",
  "include_geojson_contours": true
}
```

### 2.2. Regime Diagnosis Schema: `RegimeResponse`
```json
{
  "primary_regime": "ACTIVE_MONSOON",
  "primary_confidence": 0.92,
  "secondary_regimes": ["OROGRAPHIC_RAINFALL", "COASTAL_CONVERGENCE"],
  "synoptic_features": {
    "monsoon_trough_position": "SOUTH_OF_NORMAL",
    "low_level_jet_speed_kts": 34.5,
    "offshore_trough_active": true,
    "olr_anomaly_w_m2": -42.8,
    "vorticity_850hpa_s1": 4.8e-5,
    "moisture_flux_convergence_g_kg_s": 12.4
  },
  "regime_narrative": "Deep active monsoon phase driven by strong Arabian Sea Low-Level Jet (34.5 kts) and an active offshore trough along the Konkan coast."
}
```

### 2.3. Post-Processed 4-Product Comparison Schema
```json
{
  "raw_nwp": {
    "product_name": "Raw NWP (NCMRWF NCUM / GFS Fallback)",
    "accumulated_24h_mm": 42.6,
    "peak_hourly_rate_mm_hr": 8.4,
    "is_operational_ncmrwf": false,
    "data_source": "NOAA GFS 0.25° (Development/Demo Fallback)"
  },
  "quantile_mapping": {
    "product_name": "Empirical Quantile Mapping (EQM)",
    "accumulated_24h_mm": 58.2,
    "peak_hourly_rate_mm_hr": 14.1,
    "correction_delta_mm": 15.6
  },
  "global_ml_correction": {
    "product_name": "Global ML Post-Processing (Standard ResNet/XGBoost)",
    "accumulated_24h_mm": 71.4,
    "peak_hourly_rate_mm_hr": 22.0,
    "correction_delta_mm": 28.8
  },
  "regime_aware_ml_correction": {
    "product_name": "Regime-Aware AI Post-Processing (Target MoES/NCMRWF)",
    "accumulated_24h_mm": 94.8,
    "peak_hourly_rate_mm_hr": 36.2,
    "correction_delta_mm": 52.2,
    "uncertainty_lower_bound_mm": 82.0,
    "uncertainty_upper_bound_mm": 112.5,
    "ensemble_spread_mm": 15.25,
    "hourly_series": [1.2, 2.5, 5.0, 12.4, 28.6, 36.2, 24.1, 15.0, 8.2, 4.1, 2.0, 1.5, 1.0, 0.8, 0.5, 0.4, 0.3, 0.2, 0.2, 0.1, 0.1, 0.0, 0.0, 0.0]
  }
}
```

### 2.4. Heavy Rainfall Probabilities Schema: `ProbabilityResponse`
```json
{
  "heavy_rainfall_ge_64_5mm": {
    "probability": 0.88,
    "predicted": true,
    "threshold_mm": 64.5,
    "category": "Heavy Rainfall (64.5 - 115.5 mm/day)"
  },
  "very_heavy_rainfall_ge_115_6mm": {
    "probability": 0.46,
    "predicted": false,
    "threshold_mm": 115.6,
    "category": "Very Heavy Rainfall (115.6 - 204.4 mm/day)"
  },
  "extremely_heavy_rainfall_ge_204_5mm": {
    "probability": 0.12,
    "predicted": false,
    "threshold_mm": 204.5,
    "category": "Extremely Heavy Rainfall (>= 204.5 mm/day)"
  }
}
```

### 2.5. Spatial Verification Benchmark Schema: `VerificationResponse`
```json
{
  "evaluation_period": "2024 Monsoon Season (JJAS)",
  "benchmark_metrics": {
    "raw_nwp": { "rmse_mm": 24.8, "ets": 0.38, "csi": 0.44, "pod": 0.62, "far": 0.38, "fss_50km": 0.52 },
    "quantile_mapping": { "rmse_mm": 19.2, "ets": 0.46, "csi": 0.53, "pod": 0.71, "far": 0.32, "fss_50km": 0.61 },
    "global_ml": { "rmse_mm": 15.6, "ets": 0.58, "csi": 0.64, "pod": 0.80, "far": 0.24, "fss_50km": 0.73 },
    "regime_aware_ml": { "rmse_mm": 10.4, "ets": 0.74, "csi": 0.81, "pod": 0.92, "far": 0.14, "fss_50km": 0.89 }
  },
  "regime_skill_gain_pct": {
    "active_monsoon": 38.5,
    "orographic_rainfall": 44.2,
    "monsoon_low_lps": 32.0,
    "break_monsoon": 22.8
  }
}
```

---

## 3. Strict Source Attribution Rule

All API responses clearly disclose whether NWP telemetry is originating from:
1. **`NCMRWF_OPERATIONAL`**: Official MoES NCMRWF NCUM / NEPS data feed (target operational status).
2. **`DEMO_FALLBACK_GFS`**: Open-Meteo NOAA GFS development/demonstration fallback feed.
