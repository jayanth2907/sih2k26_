# OPERATIONAL ROADMAP & PHASE 6 DEPLOYMENT PLAN

## SIH26080 — Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts
**Ministry of Earth Sciences (MoES) · National Centre for Medium Range Weather Forecasting (NCMRWF)**

---

### Phase Structure Overview

```
[CURRENT PROTOTYPE]
        │
        ▼
[PHASE A: Operational Data Ingestion (NCUM / NEPS)]
        │
        ▼
[PHASE B: Multi-Decadal Historical Training Archive]
        │
        ▼
[PHASE C: Convective-Permitting Spatial Post-Processing]
        │
        ▼
[PHASE D: Continuous Operational WMO Verification]
        │
        ▼
[PHASE E: Automated High-Availability Production Deployment]
```

---

### 1. Current State: Certified Prototype (Phases 0–5 Complete)
* **Status:** Fully functional, hardened SIH26080 prototype.
* **Capabilities:**
  - 6-regime synoptic intelligence engine with soft multi-label weighting.
  - Four-model post-processing benchmark (Raw NWP, EQM, Global ML, Regime-Aware AI).
  - P10–P90 uncertainty intervals and calibrated exceedance probabilities ($P \ge 64.5\text{mm}$).
  - 748 district-level forecast aggregations.
  - Interactive Cesium 3D geospatial dashboard with 6 operational layers.
  - Transparent provenance and zero data leakage validation.

---

### 2. Phase A — Operational NCMRWF Data Ingestion
* **Objective:** Replace open fallback streams with direct high-speed HPC feeds from NCMRWF computing clusters (Pratyush / Mihir).
* **Key Tasks:**
  1. Establish automated NetCDF/GRIB2 ingestion daemons for NCUM global (~12km) and NCUM-R regional (~4km) models.
  2. Ingest all 22 raw ensemble members from the NCMRWF Ensemble Prediction System (NEPS).
  3. Integrate secure MoES API authentication and Common Alerting Protocol (CAP) endpoints.

---

### 3. Phase B — Multi-Decadal Paired Training Archive
* **Objective:** Expand the training baseline from 5 historical years (2018–2022) to a comprehensive 20-year paired reforecast archive (2004–2024).
* **Key Tasks:**
  1. Assimilate historical IMD 0.25° daily gridded rainfall archives spanning diverse climate cycles (strong El Niño, La Niña, positive/negative IOD).
  2. Train regime-specific expert sub-models with hyperparameter Bayesian optimization.
  3. Pre-compute localized empirical quantile transfer tables across all 748 districts.

---

### 4. Phase C — Convective-Permitting Spatial Deep Learning (Optional / Targeted)
* **Objective:** Evaluate spatial convolutional/diffusion architectures (e.g. U-Net / Fourier Neural Operators) *only where justified* by spatial resolution demands.
* **Key Tasks:**
  1. Evaluate high-resolution downscaling over complex terrain (Western Ghats, Western Himalayas, Northeast India).
  2. Implement physics-informed spatial loss functions penalizing total water mass divergence.
  3. Maintain strict residual learning formulation to prevent hallucinated extreme precipitation.

---

### 5. Phase D — Continuous Operational WMO Verification Hub
* **Objective:** Establish automated real-time verification against daily IMD rain-gauge networks.
* **Key Tasks:**
  1. Automated daily calculation of continuous metrics (RMSE, MAE, Mean Bias) and categorical metrics (POD, FAR, CSI, ETS, FSS @ 50km).
  2. Automated generation of monthly and seasonal post-processing validation bulletins for NCMRWF leadership.
  3. Drift detection alerts triggering when regime classification confidence falls below acceptable thresholds.

---

### 6. Phase E — Automated Production Deployment & CAP Dissemination
* **Objective:** 24/7 mission-critical deployment with automated alerting.
* **Key Tasks:**
  1. Containerized Kubernetes deployment across high-availability MoES cloud infrastructure.
  2. Automated 00Z and 12Z operational run scheduling.
  3. Automated generation of Common Alerting Protocol (CAP) XML/JSON feeds pushed to the National Disaster Management Authority (NDMA) and State Disaster Management Authorities (SDMAs).
