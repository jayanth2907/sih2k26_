# HydroWatch AI: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

[![SIH 2026](https://img.shields.io/badge/SIH-2026%20Problem%20Statement%2026080-blue.svg)](https://sih.gov.in)
[![Ministry](https://img.shields.io/badge/Ministry-Ministry%20of%20Earth%20Sciences%20(MoES)-0284c7.svg)](https://moes.gov.in)
[![Department](https://img.shields.io/badge/Department-NCMRWF%20%7C%20IMD-00E5FF.svg)](https://www.ncmrwf.gov.in)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2016.3%20%7C%20React%2019-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![Cesium](https://img.shields.io/badge/Geospatial-Cesium%20Ion%203D-1f6feb.svg?logo=cesium&logoColor=white)](https://cesium.com)
[![Tests Passing](https://img.shields.io/badge/Tests-193%20Passing-success.svg)](https://github.com)

**HydroWatch AI** is a meteorological intelligence and regime-aware AI post-processing platform designed for the **Ministry of Earth Sciences (MoES)** and the **National Centre for Medium Range Weather Forecasting (NCMRWF)** under **Smart India Hackathon 2026 (Problem Statement SIH26080)**.

The platform addresses the challenge of Numerical Weather Prediction (NWP) systematic biases during the South Asian Summer Monsoon (SASM) by diagnosing synoptic weather regimes and applying regime-conditioned residual AI post-processing across four benchmark models:
1. **Raw NWP Baseline** (Direct uncalibrated numerical output)
2. **Empirical Quantile Mapping (EQM)** (Statistical non-parametric distribution baseline)
3. **Global ML Correction** (Stationary pan-India ML post-processor using `HistGradientBoostingRegressor`)
4. **Regime-Aware AI Post-Processor** (MoES PS26080 soft-conditioned mixture of experts)

---

## Logical System Architecture

```
+─────────────────────────────────────────────────────────────────────────────────────────+
|                                1. NWP & METEOROLOGICAL DATA                             |
|  Numerical Forecasts (NCMRWF NCUM / GFS Fallback) │ Synoptics (LLJ, Trough, OLR, CAPE)  |
+────────────────────────────────────────────┬────────────────────────────────────────────+
                                             │
                                             ▼
+─────────────────────────────────────────────────────────────────────────────────────────+
|                     2. CANONICAL DATA PIPELINE & QUALITY CONTROL                        |
|  Unit Normalization & WGS84 Mesh │ QC Bounds Assertion │ Zero Data Leakage Isolation    |
+────────────────────────────────────────────┬────────────────────────────────────────────+
                                             │
                                             ▼
+─────────────────────────────────────────────────────────────────────────────────────────+
|                             3. FEATURE ENGINEERING LAYER                                |
|  Dynamic Wind Shear │ Moisture Flux Transport (q*V850) │ Orographic Lifting Index (u*∇z)|
+────────────────────────────────────────────┬────────────────────────────────────────────+
                                             │
                                             ▼
+─────────────────────────────────────────────────────────────────────────────────────────+
|                         4. WEATHER REGIME INTELLIGENCE ENGINE                           |
|  Active Monsoon │ Break Monsoon │ Monsoon Low/LPS │ Coastal │ Orographic │ W. Disturbance|
|  (Hierarchical Multi-Label Posterior Probabilities: ∑ w_k = 1.0)                        |
+────────────────────────────────────────────┬────────────────────────────────────────────+
                                             │
                                             ▼
+─────────────────────────────────────────────────────────────────────────────────────────+
|                   5. FOUR-MODEL POST-PROCESSING BENCHMARK ENGINE                        |
|  [1] Raw NWP  │  [2] Quantile Mapping (EQM)  │  [3] Global ML  │  [4] Regime-Aware AI   |
|  Residual Learning: y_corrected = max(0, y_raw + predicted_error)                       |
+────────────────────────────────────────────┬────────────────────────────────────────────+
                                             │
                                             ▼
+─────────────────────────────────────────────────────────────────────────────────────────+
|                       6. UNCERTAINTY & EXCEEDANCE PROBABILITIES                         |
|  Calibrated P10 - P50 - P90 Uncertainty Bands │ Exceedance: P(≥64.5mm), P(≥115.6mm)     |
+────────────────────────────────────────────┬────────────────────────────────────────────+
                                             │
                                             ▼
+─────────────────────────────────────────────────────────────────────────────────────────+
|                     7. SPATIAL DISTRICT PRODUCTS & CESIUM 3D GLOBE                      |
|  748 District Administrative Forecasts │ 6 Synchronized Cesium 3D Geospatial Layers     |
|  WGS84 Calibrated Isohyet Contours │ Causal XAI Suite │ Verification Benchmark Hub      |
+─────────────────────────────────────────────────────────────────────────────────────────+
```

---

## Meteorological Synoptic Regimes (Multi-Label & Soft-Conditioned)

| Regime Identifier | Synoptic Diagnostic Criteria | Regional Impact Footprint |
| :--- | :--- | :--- |
| **`ACTIVE_MONSOON`** | Low-Level Jet $>30\text{ kts}$, Monsoon Trough south of normal ($<22^\circ\text{N}$), OLR $<200\text{ W/m}^2$. | Central India, Konkan, Bay of Bengal |
| **`BREAK_MONSOON`** | Monsoon Trough shifted to Himalayan foothills ($>26^\circ\text{N}$), peninsula dry, weak LLJ. | Foothills, Northeast India |
| **`MONSOON_LOW_LPS`** | Cyclonic low-pressure vortex from Bay of Bengal, strong mid-tropospheric vorticity. | Odisha, Gangetic Plain, Central India |
| **`COASTAL_CONVERGENCE`** | Strong land-sea thermal contrast and boundary layer frictional convergence. | Konkan Coast, Malabar Coast, Coromandel |
| **`OROGRAPHIC_RAINFALL`** | Moist Low-Level Jet forced perpendicularly up steep Western Ghats/Himalayan slopes. | Western Ghats (Mahabaleshwar), Khasi Hills |
| **`WESTERN_DISTURBANCE`** | Extra-tropical mid-latitude upper-tropospheric westerly trough. | Jammu & Kashmir, Himachal, Punjab |

---

## Four-Model Post-Processing Verification Benchmark

Evaluated on held-out prospective test seasons (**2024–2025 JJAS**, $n=800$, zero temporal leakage; ground truth: IMD 0.25° Gridded Rainfall):

| Metric / Product | 1. Raw NWP Baseline | 2. Quantile Mapping (EQM) | 3. Global ML Correction | 4. Regime-Aware AI (SIH26080) |
| :--- | :---: | :---: | :---: | :---: |
| **Algorithm** | Direct uncalibrated NWP | Empirical CDF matching | `HistGradientBoostingRegressor` | Soft-Conditioned Mixture of Experts |
| **RMSE (mm)** | 24.83 | 12.29 | 5.79 | **5.68** (*-77.1% vs NWP*) |
| **MAE (mm)** | 19.06 | 9.54 | 3.47 | **3.89** |
| **Mean Forecast Bias** | -17.08 mm | -0.25 mm | +0.33 mm | **-0.12 mm** (*Near-Zero Bias*) |
| **Probability of Detection (POD $\ge 64.5$mm)** | 0.291 | 0.831 | 0.912 | **0.899** |
| **False Alarm Rate (FAR)** | 0.000 | 0.102 | 0.069 | **0.036** (*Lowest False Alarms*) |
| **Critical Success Index (CSI)** | 0.291 | 0.759 | 0.854 | **0.869** (*+198.6% vs NWP*) |
| **Equitable Threat Score (ETS)** | 0.250 | 0.715 | 0.825 | **0.843** (*+237.2% vs NWP*) |
| **Spatial Fractions Skill Score (FSS 50km)** | 0.502 | 0.922 | 0.961 | **0.957** |
| **Uncertainty Spread ($P_{90} - P_{10}$)** | Uncalibrated | Climatological | Global interval | **Calibrated dynamic regime band** |

---

## Data Provenance & Operational Transparency

```
+-----------------------------------------------------------------------------------------------+
|                               DATA PROVENANCE MATRIX                                          |
+----------------------+-----------------------------+------------------------------------------+
| Data Stream          | Operational Target (MoES)   | Prototype / Fallback Ingestion           |
+----------------------+-----------------------------+------------------------------------------+
| Numerical Weather    | NCMRWF NCUM Global 12km     | NOAA GFS 0.25° Seamless (Open-Meteo API) |
| Ensemble Prediction  | NCMRWF NEPS (22 members)    | Empirical Gaussian spread approximation  |
| Ground Truth (Train) | IMD 0.25° Gridded Rainfall  | IMD Gridded & NASA POWER Daily Archives  |
| Doppler Radar        | IMD DWR Network             | RainViewer S-Band Reflectivity Composite |
| Satellite Baseline   | INSAT-3DR / Sentinel-2      | Sentinel-2 L2A STAC COG Public Pipeline  |
+----------------------+-----------------------------+------------------------------------------+
```

Whenever fallback data is consumed, the platform explicitly displays `DEMO DATA · SYNTHETIC / FALLBACK MODE` across all dashboard panels.

---

## Quick Start & Local Execution

### 1. Prerequisites
- Python 3.10+ / Node.js 18+

### 2. Backend Setup
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run backend unit & integration tests (193 tests)
python -m pytest backend/tests -v

# Start FastAPI server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Build production bundle
npm run build

# Start production server
npm start
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

- [`docs/DISTRICT_DECISION_SUPPORT.md`](docs/DISTRICT_DECISION_SUPPORT.md): Phase 8 district-level decision support, 748 vs 766 reconciliation, deterministic threshold categories, and prototype warning specifications.
- [`docs/FINAL_PROJECT_AUDIT.md`](docs/FINAL_PROJECT_AUDIT.md): Comprehensive forensic audit report.
- [`docs/END_TO_END_TRACEABILITY.md`](docs/END_TO_END_TRACEABILITY.md): Complete data and code traceability map.
- [`docs/DATA_LEAKAGE_AUDIT.md`](docs/DATA_LEAKAGE_AUDIT.md): Zero data leakage and chronological split certification.
- [`docs/MODEL_PIPELINE_VALIDATION.md`](docs/MODEL_PIPELINE_VALIDATION.md): Four-model benchmark hierarchy documentation.
- [`docs/SIH_KEY_RESULTS.md`](docs/SIH_KEY_RESULTS.md): Key scientific results for jury defense.
- [`docs/SIH26080_ARCHITECTURE.md`](docs/SIH26080_ARCHITECTURE.md): End-to-end architecture specification.
- [`docs/SIH_JUDGE_QA.md`](docs/SIH_JUDGE_QA.md): 25 concise judge defense answers.
- [`docs/FINAL_SIH_DEMO_SCRIPT.md`](docs/FINAL_SIH_DEMO_SCRIPT.md): 5-minute grand finale presentation script.
- [`docs/SIH_FINAL_PRESENTATION.md`](docs/SIH_FINAL_PRESENTATION.md): 12-slide pitch deck outline.
- [`docs/ONE_MINUTE_PITCH.md`](docs/ONE_MINUTE_PITCH.md): 60-second executive pitch.
- [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md): Transparent scientific and operational limitations.
- [`docs/OPERATIONAL_ROADMAP.md`](docs/OPERATIONAL_ROADMAP.md): Phase 6 NCMRWF operational deployment plan.
- [`docs/FINAL_VALIDATION_REPORT.md`](docs/FINAL_VALIDATION_REPORT.md): Final test certificate and smoke test results.


---

## License & Attribution
Developed for **Smart India Hackathon 2026** under the auspices of the **Ministry of Earth Sciences (MoES)** and the **National Centre for Medium Range Weather Forecasting (NCMRWF)**.
