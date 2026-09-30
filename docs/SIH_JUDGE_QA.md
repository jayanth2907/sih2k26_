# SIH26080 — FINAL JUDGE DEFENSE & 25 CONCISE ANSWERS

## Smart India Hackathon 2026 Grand Finale Defense Document
**Problem Statement:** SIH26080 — *Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts*  
**Ministry:** Ministry of Earth Sciences (MoES)  
**Department:** National Centre for Medium Range Weather Forecasting (NCMRWF)

---

### 1. Why post-processing instead of direct rainfall prediction?
**Answer (20s):**  
NWP models integrate the fundamental physical equations of atmospheric dynamics up to 10 days ahead. Direct deep learning lacks physical conservation laws and suffers beyond short horizons. Post-processing combines the best of both: NWP provides large-scale physical dynamics, while AI eliminates systematic, localized parameterization and terrain errors.

---

### 2. What exactly is your AI model predicting?
**Answer (15s):**  
Our model predicts the **NWP forecast error delta** ($\hat{\epsilon} = y_{\text{obs}} - y_{\text{NWP}}$). The final calibrated forecast is computed as $\hat{y} = \max(0, y_{\text{NWP}} + \hat{\epsilon})$, dynamically adjusting for under- or over-estimation.

---

### 3. Why use residual learning?
**Answer (20s):**  
Residual learning prevents phantom rainfall artifacts during dry conditions, guarantees physical conservation, converges faster during optimization, and allows operational meteorologists to inspect the exact bias delta added or subtracted by the AI.

---

### 4. Why are weather regimes necessary?
**Answer (20s):**  
NWP forecast errors are state-dependent. An active monsoon surge has severe orographic under-prediction biases along the Western Ghats, while a break spell has convective over-prediction biases over central India. Conditioning the AI on diagnosed weather regimes ensures corrections match the active physical precipitation mechanism.

---

### 5. Why multi-label regime classification?
**Answer (20s):**  
Monsoon dynamics are continuous and overlapping. In July, an *Active Monsoon* westerly surge frequently co-occurs with *Western Ghats Orographic Forcing* and a *Monsoon Low* over the Bay of Bengal. Multi-label classification models these overlapping physical processes realistically.

---

### 6. Why soft regime weighting?
**Answer (15s):**  
Hard classification switches create sharp, unphysical discontinuities across space and time. Soft posterior weighting ($\sum w_k = 1.0$) smoothly blends regime experts, ensuring continuous spatial isohyets.

---

### 7. Why include Empirical Quantile Mapping (EQM) in your benchmark?
**Answer (15s):**  
EQM is the traditional statistical standard in operational meteorology. Including it proves whether modern machine learning genuinely outperforms classical statistical distribution calibration.

---

### 8. Why include a Global ML baseline?
**Answer (15s):**  
Global ML uses the same gradient boosting architecture but without regime conditioning. Benchmarking against it directly isolates and quantifies the exact scientific value added by regime awareness.

---

### 9. What makes the Regime-Aware ML model superior?
**Answer (20s):**  
It achieves a **77.1% RMSE reduction** (24.83 mm $\rightarrow$ 5.68 mm) and increases the Critical Success Index (CSI) from 0.291 to **0.869** by adapting its learned error function to prevailing synoptic dynamics.

---

### 10. How did you prevent data leakage?
**Answer (20s):**  
Through strict chronological partitioning: training strictly on 2018–2022, validation on 2023, and testing on 2024–2025 JJAS. Ingestion pipelines enforce that for a forecast at time $T$, only observations up to $T-1\text{ day}$ ($D-1$) are accessible.

---

### 11. Why is a chronological split mandatory?
**Answer (15s):**  
Random cross-validation shuffles adjacent convective days between train and test sets, causing massive auto-correlation leakage. Chronological forward validation on unseen seasons is the only scientifically valid protocol.

---

### 12. What is the source of ground truth?
**Answer (15s):**  
IMD 0.25° Daily Gridded Rainfall datasets combined with IMD Doppler Weather Radar (DWR) reflectivity composites and NASA POWER daily meteorological archives.

---

### 13. What is NCMRWF's role in this system?
**Answer (20s):**  
NCMRWF is India's premier medium-range modeling center operating the Unified Model (NCUM global 12km) and Ensemble Prediction System (NEPS). In operational deployment, NCMRWF provides the primary NWP boundary feeds to our post-processing engine.

---

### 14. Are you currently using live operational NCMRWF data?
**Answer (20s):**  
Our prototype uses NOAA GFS 0.25° seamless data via Open-Meteo as an approved open fallback feed. The platform is architected with modular connectors ready to switch to live NCMRWF NCUM/NEPS feeds when deployed on MoES networks.

---

### 15. What happens if operational NCMRWF data is unavailable?
**Answer (15s):**  
The platform automatically switches to GFS fallback mode, explicitly updating the UI with `DEMO DATA · SYNTHETIC / FALLBACK MODE` across all dashboard panels.

---

### 16. What does the forecast uncertainty mean?
**Answer (20s):**  
We provide calibrated **P10, P50, and P90 quantiles**. A narrow $P90 - P10$ width indicates high synoptic predictability; a wide interval alerts forecasters to high convective spread and uncertainty.

---

### 17. How are heavy rainfall probabilities generated?
**Answer (20s):**  
Calibrated exceedance probabilities for IMD thresholds ($P \ge 64.5\text{mm}$, $P \ge 115.6\text{mm}$, $P \ge 204.5\text{mm}$) are computed by integrating the calibrated post-processed distribution and ensemble spread.

---

### 18. How do you calculate Fractions Skill Score (FSS)?
**Answer (20s):**  
FSS is a spatial neighborhood metric that compares the fraction of grid points exceeding a threshold within a spatial window (e.g. 50 km) against observed radar/gauge fractions, rewarding forecasts that place rain in the correct vicinity.

---

### 19. Why provide district-level forecast products?
**Answer (15s):**  
Disaster management authorities (NDMA, SDMA) operate at the district administrative level. We provide area-weighted rainfall, exceedance probabilities, and risk tiers across all 748 Indian districts.

---

### 20. What is the main limitation of your prototype?
**Answer (20s):**  
The prototype operates on a 0.25° (~25km) synoptic grid. Resolving localized urban cloudbursts (<5km) requires high-resolution regional convective-permitting models (NCUM-R 4km) and sub-kilometer radar assimilation.

---

### 21. How would this become operational at NCMRWF?
**Answer (20s):**  
By containerizing the FastAPI inference microservice, establishing automated NetCDF/GRIB2 ingestion pipelines from NCMRWF HPC clusters (Pratyush/Mihir), and running automated post-processing cycles at 00Z and 12Z.

---

### 22. How would you retrain the model in operations?
**Answer (15s):**  
Through annual post-monsoon batch retraining (in October–November) incorporating the newly observed season's IMD gridded pairs into the historical training archive.

---

### 23. How would NCUM and NEPS be integrated?
**Answer (20s):**  
NCUM deterministic forecasts provide the primary baseline $y_{\text{raw}}$, while all 22 NEPS ensemble members feed the ensemble spread feature extractor to calibrate probabilistic uncertainty bands.

---

### 24. How would you validate the system operationally?
**Answer (20s):**  
By running automated daily WMO verification scripts tracking continuous RMSE, MAE, Mean Bias, and categorical CSI, ETS, POD, FAR against real-time IMD rain-gauge networks.

---

### 25. What differentiates this from ordinary rainfall prediction?
**Answer (20s):**  
Three things: (1) We condition post-processing on diagnosed synoptic regimes, (2) We use physics-guided residual learning on top of NWP rather than black-box prediction, and (3) We deliver multi-tier products with calibrated uncertainty across 748 districts.
