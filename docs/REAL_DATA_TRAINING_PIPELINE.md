# Phase 11: Real Historical Data & Reproducible Training Pipeline

## 1. Scientific Objective & Scope

The objective of Phase 11 is to build a scientifically rigorous, reproducible historical training pipeline for **SIH PS26080: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts (MoES / NCMRWF)**.

> [!IMPORTANT]
> **Scientific Integrity & Benchmark Isolation Statement**:
> 1. Real historical reanalysis (ERA5) and gridded observations (IMD) training pipelines are developed and evaluated under a distinct evaluation namespace: `REAL_DATA_TRAINING_EVALUATION`.
> 2. The primary held-out 2024–2025 prospective benchmark and all Phases 1–10 baseline models remain **completely frozen and untouched**.
> 3. Any newly trained models are tagged as `EXPERIMENTAL` in the Model Registry and **do NOT automatically replace** operational dashboard models.

---

## 2. Dual Pipeline Architecture

To prevent conflating atmospheric reanalysis analysis with NWP forecasts, the system defines two explicit training tracks:

```
                          ┌──────────────────────────────────────────────┐
                          │   Historical Data Ingestion (2010–2023 JJAS) │
                          └──────────────────────┬───────────────────────┘
                                                 │
                     ┌───────────────────────────┴───────────────────────────┐
                     ▼                                                       ▼
  ┌─────────────────────────────────────┐         ┌─────────────────────────────────────┐
  │   PIPELINE A: REANALYSIS LEARNING   │         │   PIPELINE B: TRUE NWP POST-PROCESS │
  │                                     │         │                                     │
  │ • ERA5 Atmospheric State Predictors │         │ • Archived Raw NWP Forecasts (NCUM) │
  │ • IMD Observational Rainfall Target │         │ • IMD Collocated Observational Truth│
  │ • Regime Classification Conditioning│         │ • Residual Target: ε = Y_obs - Y_nwp│
  │ • Physical Feature Representation   │         │ • Regime-Conditioned Error Modeling │
  └─────────────────────────────────────┘         └─────────────────────────────────────┘
```

---

## 3. Data Sources & Variable Mapping

| Source Identifier | Role | Parameters / Pressure Levels | Spatial / Temporal Resolution | Access / Format |
| :--- | :--- | :--- | :--- | :--- |
| **`ECMWF_ERA5_REANALYSIS`** | Atmospheric Reanalysis | $u, v, t, r, z, w$ at 850, 700, 500 hPa; MSLP, 2t, CAPE, TP | 0.25° × 0.25° (~31 km), Hourly | Copernicus CDS API (`netcdf4`) |
| **`IMD_GRIDDED_RAINFALL`** | Ground-Truth Observation | 24-hour Accumulated Rainfall (0300 UTC / 0830 IST) | 0.25° × 0.25°, Daily | IMD National Data Centre (`.grd` / NetCDF) |
| **`NCMRWF_NCUM_ARCHIVE`** | Forecast Baseline (Target) | 24h Rainfall, $u_{850}, v_{850}, t_{850}, \text{RH}_{850}$, MSLP | 12 km Regional / 4 km Nested | NCMRWF Historical GRIB2 Archive |

---

## 4. Chronological Splitting Strategy & Leakage Prevention

Strict chronological splitting is enforced to avoid temporal autocorrelation leakage:

- **Training Split (2010–2019 JJAS)**: 10 historical monsoon seasons for fitting feature transformations, expert regressors, and quantile distributions.
- **Validation Split (2020–2021 JJAS)**: 2 monsoon seasons for hyperparameter tuning, L2 regularization, and expert blending weights.
- **Held-Out Test Split (2022–2023 JJAS)**: 2 monsoon seasons strictly isolated for out-of-sample retrospective evaluation.

### Leakage Audit Checklist
- **Temporal Leakage**: $\max(t_{\text{train}}) < \min(t_{\text{val}}) < \min(t_{\text{test}})$. Verified.
- **Target Leakage**: No observation target fields enter feature vectors. Verified.
- **Normalization Leakage**: Scalers and quantiles are fit strictly on training samples. Verified.
- **Threshold Leakage**: Extreme event thresholds ($\ge 64.5, \ge 115.6, \ge 204.5\text{ mm}$) follow IMD standards without test-set tuning. Verified.
- **Audit Verdict**: `NO LEAKAGE FOUND IN CODE/DATASET AUDIT`.

---

## 5. Feature Engineering Engine

All features are engineered via [`MeteorologicalFeatureEngineer`](file:///c:/Users/srija/OneDrive/Desktop/New%20folder/backend/app/data/processing/feature_engineering.py):
1. **Dynamic Wind Predictors**: Scalar speed and meteorological direction at 850 hPa and 700 hPa.
2. **Vertical Wind Shear**: Bulk shear between 850 hPa, 700 hPa, and 500 hPa ($\sqrt{\Delta u^2 + \Delta v^2}$).
3. **Moisture Transport Proxy (IVT)**: $q_{850} \times V_{850}$ computed using Bolton/Tetens vapor formulations.
4. **Orographic Lift Index**: Normal wind vector impingement against Western Ghats / Himalayan terrain slopes.
5. **Coastal Moisture Convergence**: Onshore wind speed weighted by distance to nearest coastline.
6. **Synoptic Barometry**: Departure from standard sea-level pressure ($|\text{MSLP} - 1013.25| / 5.0$).

---

## 6. Model Architectures & Training Workflow

Four standardized models are trained:
1. **Raw NWP Forecast Baseline**: Deterministic numerical forecast baseline.
2. **Empirical Quantile Mapping (EQM)**: Non-parametric cumulative distribution matching.
3. **Global ML**: Histogram-based Gradient Boosting Regressor (`HistGradientBoostingRegressor`) predicting residual error across all samples.
4. **Regime-Aware ML**: Soft Mixture-of-Experts combining regime-specialized estimators weighted via meta-ridge blending:
   $$\hat{\epsilon} = \sum_{k=1}^K P(\text{regime}_k \mid \mathbf{x}) \cdot f_k(\mathbf{x})$$
   $$y_{\text{corrected}} = \max(0, y_{\text{raw\_nwp}} + \hat{\epsilon})$$

---

## 7. Model Artifact Management & Registry Lifecycle

Artifacts are exported to `artifacts/models/<model_id>/<version>/`:
- `model.pkl`: Serialized model estimator / MoE ensemble.
- `metadata.json`: Dataset ID, config hash, data hash, training duration, Python/platform versions.
- `feature_schema.json`: Ordered list of input feature names and counts.

### Lifecycle Statuses
`EXPERIMENTAL` $\to$ `VALIDATED` $\to$ `FROZEN` $\to$ `DEPRECATED`.  
All new models initialize as `EXPERIMENTAL` and **never replace the active dashboard model**.
