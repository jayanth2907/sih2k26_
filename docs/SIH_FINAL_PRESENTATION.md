# SIH26080 FINAL PRESENTATION DECK

## "Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts"
**Ministry of Earth Sciences (MoES) · National Centre for Medium Range Weather Forecasting (NCMRWF)**  
**Target Pitch Deck: 12 Slides**

---

### Slide 1: Title & Problem Statement
* **Title:** HydroWatch AI — Regime-Aware Post-Processing of Monsoon Rainfall Forecasts
* **Problem Statement ID:** SIH26080
* **Target Organization:** Ministry of Earth Sciences (MoES)
* **Department:** National Centre for Medium Range Weather Forecasting (NCMRWF)
* **Core Value Proposition:** Learning state-dependent NWP forecast errors conditioned on synoptic weather regimes to provide calibrated rainfall totals, exceedance probabilities, and uncertainty bounds for India.

---

### Slide 2: Why Existing NWP Forecasts Require AI Post-Processing
* **NWP Foundation:** Numerical models (NCMRWF NCUM, NEPS, GFS) are indispensable for medium-range atmospheric dynamics.
* **Systematic Physical Biases over India:**
  - *Orographic Underestimation:* Western Ghats windward precipitation severely damped due to smoothed model topography.
  - *LPS Convective Core Displacement:* Track and intensity errors in Bay of Bengal Monsoon Lows.
  - *Coastline Smearing:* Grid resolution limits (~12km–25km) smear intense coastal convective bands inland.
  - *Break Monsoon False Alarms:* Convective parameterizations trigger spurious rainfall during dry spells.
* **The Post-Processing Opportunity:** Raw NWP has high dynamical skill but localized systematic biases that can be learned and eliminated by AI.

---

### Slide 3: Proposed Solution — Regime-Aware Residual Learning
* **Do Not Replace NWP — Calibrate It:** Retain the full thermodynamic trajectory of the numerical atmosphere.
* **Four Core Pillars:**
  1. *Synoptic Weather Regime Classification:* 6 South Asian circulation patterns diagnosed in real-time.
  2. *Soft Multi-Label Mixture of Experts:* Continuous weighting without artificial spatial boundaries.
  3. *Physics-Guided Residual Learning:* $\hat{y} = \max(0, y_{\text{NWP}} + \hat{\epsilon}_{\text{regime}})$.
  4. *Probabilistic Exceedance & Uncertainty:* Calibrated P10–P90 uncertainty intervals and IMD heavy rainfall exceedance probabilities ($P \ge 64.5\text{mm}$).

---

### Slide 4: End-to-End System Architecture
* **NWP & Telemetry Ingestion:** NCMRWF NCUM / GFS 0.25° fallback, IMD Radar, NASA POWER observations.
* **Canonical Meteorological Pipeline:** Automated unit conversion, QC validation, and 37-dimension feature extraction.
* **Regime Intelligence Engine:** Bayesian & heuristic multi-label classifier.
* **Four-Model Post-Processing Core:** Raw NWP $\rightarrow$ EQM $\rightarrow$ Global ML $\rightarrow$ Regime-Aware AI.
* **Product Generation & Visualization:** 748 district aggregations, GeoJSON isohyet contours, and Cesium 3D geospatial dashboard.

---

### Slide 5: The Weather Regime Intelligence Engine
* **6 Synoptic Regimes Diagnosed from Atmospheric State:**
  1. *Active Monsoon:* Strong Low-Level Jet ($>30\text{ kts}$), deep Monsoon Trough ($<22^\circ\text{N}$), OLR $<200\text{ W/m}^2$.
  2. *Break Monsoon:* Trough shifted north to foothills ($>26^\circ\text{N}$), central dry zone.
  3. *Monsoon Low / LPS:* Cyclonic vortex, high 850 hPa vorticity, moisture convergence.
  4. *Coastal Convergence:* Onshore moisture flux along western/eastern coastline.
  5. *Orographic Forcing:* Strong windward terrain gradient lift ($\mathbf{u} \cdot \nabla z$).
  6. *Western Disturbance:* Mid-latitude upper-tropospheric westerly trough.
* **Innovation:** Soft posterior probability mixture ($\sum w_k = 1.0$) handles overlapping co-occurring regimes seamlessly.

---

### Slide 6: Four-Model Post-Processing Benchmark Hierarchy
* **Evaluated on Identical Meteorological Inputs:**
  1. *Raw NWP Baseline:* Uncorrected numerical forecast ($\Delta_{bias} = 0.0\text{ mm}$).
  2. *Empirical Quantile Mapping (EQM):* Non-parametric statistical cumulative distribution transfer function.
  3. *Global ML Regressor:* Stationary Pan-India gradient boosting regressor (`HistGradientBoostingRegressor`).
  4. *Regime-Aware AI (PS26080):* Soft-conditioned mixture of experts using dynamic regime probabilities.

---

### Slide 7: Regime-Aware AI — Formulation & Residual Mechanics
* **Mathematical Formulation:**
  $$\hat{y}_{\text{regime}} = \max\left(0, y_{\text{raw}} + \sum_{k=1}^{6} w_k \cdot f_k(\mathbf{x}) + g(\mathbf{w}, \mathbf{x})\right)$$
* **Why Residual Learning Works:**
  - *Physical Conservation:* Zero predicted rain during dry spells; zero phantom artifacts.
  - *Gradient Efficiency:* Learning small error deltas converges faster and generalizes better than predicting absolute rainfall.
  - *Forensic Interpretability:* Meteorologists can inspect the exact bias delta added or subtracted by AI.

---

### Slide 8: Spatial & District-Level Forecast Products
* **National Administrative Coverage:** 748 Indian administrative districts.
* **Standardized District Indicators:**
  - Area-weighted mean calibrated precipitation (mm/24h).
  - Heavy rainfall exceedance probabilities ($P \ge 64.5\text{mm}$, $P \ge 115.6\text{mm}$).
  - Calibrated uncertainty intervals [$P10 - P90$].
  - Dominant synoptic circulation regime.
* **Interactive 3D Geospatial Synchronization:** Instant Cesium camera flight and localized telemetry update upon district selection.

---

### Slide 9: Quantitative Verification & Benchmark Skill
*(Evaluated on prospective held-out 2024–2025 JJAS test seasons, $n=800$, zero temporal leakage)*

| Verification Metric | Raw NWP Baseline | EQM (Quantile) | Global ML | Regime-Aware AI (PS26080) |
| :--- | :---: | :---: | :---: | :---: |
| **RMSE (mm)** | 24.83 | 12.29 | 5.79 | **5.68** (*-77.1%*) |
| **MAE (mm)** | 19.06 | 9.54 | 3.47 | **3.89** |
| **Mean Bias (mm)** | -17.08 | -0.25 | +0.33 | **-0.12** |
| **Critical Success Index (CSI)** | 0.291 | 0.759 | 0.854 | **0.869** (*+198.6%*) |
| **Equitable Threat Score (ETS)** | 0.250 | 0.715 | 0.825 | **0.843** (*+237.2%*) |
| **Fractions Skill Score (FSS 50km)** | 0.502 | 0.922 | 0.961 | **0.957** |

---

### Slide 10: Explainability & Uncertainty Quantification
* **5-Step Visual Causal Narrative:**
  $$\text{Raw NWP} \longrightarrow \text{Weather Regime} \longrightarrow \text{Synoptic Drivers} \longrightarrow \text{Learned Bias Delta} \longrightarrow \text{Calibrated Forecast}$$
* **Tree SHAP Feature Attribution:** Quantifies mathematical feature importance (Low-Level Jet speed, OLR, CAPE, terrain slope).
* **Uncertainty Width:** Dedicated Cesium layer rendering the spatial distribution of $P90 - P10$ spread.

---

### Slide 11: Transparent Data Provenance & Current Limitations
* **Operational Transparency:**
  - Prototype runs on approved open fallback streams (NOAA GFS 0.25° / NASA POWER / RainViewer).
  - Explicit UI labeling: `DEMO DATA · SYNTHETIC / FALLBACK MODE`.
* **Current Prototype Limitations:**
  - Horizontal grid resolution: 0.25° (~25km) synoptic mesh.
  - Single-deterministic NWP input with statistical ensemble spread approximation.
  - Multi-year operational verification across NCMRWF HPC clusters recommended for Phase 6.

---

### Slide 12: Operational Deployment Roadmap (Phase 6)
* **Phase A — Secure Operational NCMRWF Ingestion:** Direct high-speed connection to NCUM global (12km) and NCUM-R regional (4km).
* **Phase B — Full NEPS Ensemble Integration:** Ingest all 22 ensemble members for empirical spread post-processing.
* **Phase C — Sub-Daily Update Cycles:** Rapid 3-hourly and 6-hourly post-processing updates.
* **Phase D — Automated CAP Feeds:** Push automated Common Alerting Protocol (CAP) alerts to NDMA and State Disaster Management Authorities.
