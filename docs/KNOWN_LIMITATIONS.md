# KNOWN SCIENTIFIC & TECHNICAL LIMITATIONS

## SIH26080 — Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts
**Ministry of Earth Sciences (MoES) · National Centre for Medium Range Weather Forecasting (NCMRWF)**

---

### 1. Ingestion Feeds & Operational Gateway Dependency
* **Current Prototype State:** Operating outside the secure MoES/NCMRWF intranet, the prototype connects to open fallback feeds (NOAA GFS 0.25° via Open-Meteo, NASA POWER daily gauge reanalysis, RainViewer Doppler radar composites).
* **Operational Dependency:** Full operational deployment requires direct integration with NCMRWF's secure HPC data gateways for native NCUM (12km global, 4km regional) NetCDF/GRIB2 files.

---

### 2. Spatial Grid Resolution
* **Current Synoptic Resolution:** The platform currently processes data on a 0.25° (~25km) horizontal grid mesh.
* **Limitation:** While highly effective for regional and synoptic rainfall calibration, a 25km grid cannot fully resolve ultra-localized urban cloudbursts or microscale convective funnels (<5km) occurring within major metropolitan cities.

---

### 3. Probabilistic Ensemble Modeling
* **Current Implementation:** Uses single deterministic NWP forecasts with statistical ensemble variance approximation to generate P10–P90 uncertainty intervals.
* **Operational Target:** Full operational calibration should directly ingest all 22 members of the NCMRWF Ensemble Prediction System (NEPS) to compute raw empirical ensemble spreads.

---

### 4. Evaluation Dataset Scope
* **Current Benchmark Dataset:** Verification metrics (RMSE 5.68 mm, ETS 0.843, CSI 0.869) are evaluated on held-out prospective test seasons (2024–2025 JJAS, $n=800$ evaluation points).
* **Operational Validation Requirement:** While temporally isolated with zero data leakage, continuous multi-year operational validation across 10+ monsoon seasons is required before operational deployment.

---

### 5. Retraining & Climate Teleconnection Drift
* **Regime Shifts:** Multi-decadal climate variations (e.g. strong El Niño / La Niña, extreme positive Indian Ocean Dipole) can introduce novel circulation patterns outside the 2018–2022 training distribution.
* **Operational Protocol:** Requires scheduled post-monsoon annual retraining cycles (every October–November) to assimilate the latest seasonal observations into the historical calibration archive.

---

### 6. Independent Institutional Validation
* **External Verification:** Final operational certification requires formal, independent verification against IMD national automatic weather station (AWS) and rain-gauge networks conducted by NCMRWF scientists.
