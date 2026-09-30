# KEY RESULTS & SCIENTIFIC SUMMARY

## Smart India Hackathon 2026 — PS SIH26080
**"Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts"**  
**Organization:** Ministry of Earth Sciences (MoES)  
**Department:** National Centre for Medium Range Weather Forecasting (NCMRWF)

---

### 1. Problem Statement & Operational Challenge

Numerical Weather Prediction (NWP) models (such as NCMRWF NCUM, GFS, ECMWF) are the foundation of modern weather forecasting. However, raw NWP forecasts over the Indian subcontinent exhibit well-documented, systematic biases:
* Severe orographic underestimation along the windward slopes of the Western Ghats and northeastern hills.
* Spatial displacement of convective cores in Monsoon Low Pressure Systems (LPS).
* Smearing of intense coastal rainfall inland due to grid resolution limits.
* Spurious false-alarm precipitation during regional Break Monsoon periods.

Because these errors are state-dependent and governed by large-scale circulation mechanisms, traditional static post-processing (e.g., standard quantile mapping) fails when synoptic regimes shift dynamically.

---

### 2. Proposed Solution: Regime-Aware AI Post-Processing

SIH26080 introduces an intelligent post-processing pipeline that:
1. **Diagnoses Synoptic Weather Regimes:** Automatically identifies large-scale circulation states (*Active Monsoon, Break Monsoon, Monsoon Low/LPS, Coastal Convergence, Orographic Forcing, Western Disturbance*) from meteorological predictors (Low-Level Jet, Monsoon Trough latitude, OLR, CAPE, Integrated Vapor Transport).
2. **Conditions Residual Corrections:** Dynamically weights regime-specific machine learning models using soft multi-label posterior probabilities.
3. **Learns NWP Bias:** Utilizes residual learning ($\hat{\epsilon} = y_{obs} - y_{raw}$) rather than end-to-end rainfall generation, preserving the physical consistency of the underlying NWP dynamics.
4. **Delivers Multi-Tier Operational Products:** Generates calibrated 24h precipitation, P10–P90 uncertainty intervals, calibrated heavy rainfall exceedance probabilities ($P \ge 64.5\text{mm}$, $P \ge 115.6\text{mm}$), and 748 district-level forecasts.

---

### 3. Four-Model Benchmark Hierarchy

All four forecasting pipelines are evaluated on identical meteorological inputs:

```
+-----------------------------------------------------------------------------------------+
|                        FOUR-MODEL POST-PROCESSING COMPARISON                            |
+---------------------+-------------------+-------------------+---------------------------+
| 1. RAW NWP          | Direct simulation | No bias correction| Uncalibrated Baseline     |
| 2. QUANTILE MAPPING | Empirical CDF     | Climatological ECDF| Statistical Calibration  |
| 3. GLOBAL ML        | HistGradBoosting  | Stationary ML     | Non-Regime ML Baseline    |
| 4. REGIME-AWARE AI  | Soft MoE Residual | Regime-Conditioned| Target SIH26080 Solution  |
+---------------------+-------------------+-------------------+---------------------------+
```

---

### 4. Quantitative Verification Results

Evaluated on held-out prospective test seasons (**2024–2025 JJAS**, $n=800$ evaluation cases; ground truth: IMD 0.25° Gridded Rainfall):

| Metric | Raw NWP Baseline | EQM (Quantile) | Global ML | Regime-Aware AI (SIH26080) |
| :--- | :---: | :---: | :---: | :---: |
| **RMSE (Root Mean Square Error)** | 24.83 mm | 12.29 mm | 5.79 mm | **5.68 mm** (*-77.1% vs NWP*) |
| **MAE (Mean Absolute Error)** | 19.06 mm | 9.54 mm | 3.47 mm | **3.89 mm** |
| **Mean Forecast Bias** | -17.08 mm | -0.25 mm | +0.33 mm | **-0.12 mm** (*Near-Zero Bias*) |
| **POD (Probability of Detection $\ge 64.5$mm)** | 0.291 | 0.831 | 0.912 | **0.899** |
| **FAR (False Alarm Rate)** | 0.000 | 0.102 | 0.069 | **0.036** (*Lowest False Alarms*) |
| **CSI (Critical Success Index / Threat)** | 0.291 | 0.759 | 0.854 | **0.869** (*+198.6% vs NWP*) |
| **ETS (Equitable Threat Score)** | 0.250 | 0.715 | 0.825 | **0.843** (*+237.2% vs NWP*) |
| **FSS (Fractions Skill Score @ 50km)** | 0.502 | 0.922 | 0.961 | **0.957** (*High Spatial Skill*) |

---

### 5. Core Innovations

1. **Soft Multi-Label Regime Conditioning:** Avoids artificial "hard switch" boundary artifacts by modeling continuous mixtures of active circulation regimes.
2. **Physics-Guided Residual Learning:** Machine learning models predict the *forecast error* rather than total precipitation, preventing unphysical non-zero predictions during clear sky or extreme artifacts.
3. **Calibrated Exceedance Probability Engine:** Converts point forecasts and ensemble spreads into actionable IMD heavy rainfall warning probabilities.
4. **Spatial Aggregation:** Computes area-weighted mean rainfall and exceedance fractions for all 748 Indian administrative districts.
5. **Tree SHAP & Physical Causal XAI:** Explains why the model added or subtracted rainfall based on Low-Level Jet speed, OLR convection, moisture convergence, and orographic lifting.

---

### 6. Data Provenance & Operational Transparency

The system maintains strict distinction between operational data feeds and prototype fallback datasets:
* **Demo / Fallback Mode:** Clearly labeled as `DEMO DATA · SYNTHETIC / FALLBACK MODE` (GFS 0.25° via Open-Meteo, NASA POWER observations, RainViewer Doppler radar composite).
* **Operational Readiness:** Modular connector architecture designed for direct integration with NCMRWF NCUM global (12km) and NEPS ensemble feeds when operational network access is available.
