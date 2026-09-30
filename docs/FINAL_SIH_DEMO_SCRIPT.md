# FINAL 5-MINUTE SIH GRAND FINALE DEMONSTRATION SCRIPT

## Problem Statement: SIH26080 — Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts
**Ministry of Earth Sciences (MoES) · National Centre for Medium Range Weather Forecasting (NCMRWF)**  
**Target Duration:** 5 Minutes (300 Seconds)

---

### [0:00 – 0:30] 1. The Operational Challenge (The "Why")

> *"Respected Judges and Evaluators from the Ministry of Earth Sciences and NCMRWF.*
>
> *Numerical Weather Prediction models like NCMRWF's NCUM and GFS are the scientific bedrock of monsoon forecasting. However, raw NWP forecasts suffer from persistent, systematic errors over India:*
> * *Underestimating extreme rainfall on the windward slopes of the Western Ghats;*
> * *Displacing convective cores in Monsoon Lows;*
> * *Smearing intense coastal storms inland.*
>
> *Traditional static post-processing fails because these biases change dynamically depending on whether India is experiencing an active monsoon surge, an LPS vortex, or a dry break spell."*

---

### [0:30 – 1:00] 2. The Core Innovation (The "How")

> *"Our solution for Problem Statement SIH26080 introduces a fundamental paradigm:*
> 
> ***We do NOT attempt to replace NWP with a black-box AI model.***
> 
> *Instead, our system respects the atmospheric physics simulated by NWP, automatically diagnoses the prevailing large-scale **Weather Regime**, and uses a **soft-conditioned AI post-processor** to learn and correct the state-dependent forecast error:*
> $$\hat{y} = \max(0, y_{\text{NWP}} + \hat{\epsilon}_{\text{regime}})$$
> 
> *Let us walk you through the operational dashboard."*

---

### [1:00 – 1:45] 3. The Weather Regime Intelligence Engine

*(Presenter clicks on Mumbai / Konkan Coast on the dashboard)*

> *"On the upper HUD and Evidence Strip, you can see our Phase 2 **Weather Regime Intelligence Engine** in action.*
>
> *Rather than a simplistic single label, our engine computes continuous multi-label posterior probabilities across **six South Asian monsoon regimes**:*
> * *Active Monsoon (diagnosed by strong Low-Level Jet westerlies >30 knots and a deep Monsoon Trough);*
> * *Western Ghats Orographic Forcing;*
> * *Coastal Convergence;*
> * *Monsoon Lows and LPS;*
> * *Break Monsoon;*
> * *Western Disturbances.*
>
> *Notice that here in the Konkan Coast, both **Active Monsoon** and **Orographic Forcing** co-exist. Our **soft mixture-of-experts** model allows these regimes to overlap continuously, preventing artificial spatial step-discontinuities."*

---

### [1:45 – 2:30] 4. The 4-Model Post-Processing Benchmark

*(Presenter switches models on the Header Switcher and points to the Evidence Strip)*

> *"To scientifically evaluate the regime-aware approach, our platform concurrently executes a **Four-Model Benchmark Hierarchy**:*
> 1. ***Raw NWP Baseline:*** *Direct uncalibrated numerical output — here predicting 38.5 mm.*
> 2. ***Empirical Quantile Mapping (EQM):*** *Standard statistical CDF transformation — predicting 44.3 mm.*
> 3. ***Global ML:*** *A stationary Pan-India gradient boosting regressor — predicting 48.1 mm.*
> 4. ***Regime-Aware AI (Target SIH26080):*** *Soft-conditioned on the diagnosed active surge and orographic lift, the model learns that NWP has an under-prediction bias of +17.3 mm, correcting the forecast to **55.8 mm**.*
>
> *Because we use **residual learning**, if NWP predicts clear skies, the model outputs zero, guaranteeing zero phantom rainfall artifacts."*

---

### [2:30 – 3:15] 5. 3D Geospatial Visualization & The 6 Layers

*(Presenter interacts with the Cesium 3D Globe, toggling between layers)*

> *"In the center of the dashboard is our **Cesium 3D geospatial engine**, rendering high-resolution terrain with six synchronized operational layers:*
> 1. ***AI Calibrated Rainfall:*** *Showing high-resolution WGS84 precipitation isohyets.*
> 2. ***Raw NWP Baseline:*** *The uncorrected numerical grid.*
> 3. ***Bias Delta ($\Delta$):*** *Where the AI enhanced or dampened rainfall.*
> 4. ***Heavy Rainfall Probability:*** *Direct calibrated exceedance ($P \ge 64.5\text{ mm} = 78\%$).*
> 5. ***Monsoon Regime Map:*** *Spatial distribution of synoptic circulation.*
> 6. ***Uncertainty Width:*** *Visualizing the calibrated $P90 - P10$ uncertainty interval.*
>
> *All layers are dynamically bounded and tied to the backend data stream."*

---

### [3:15 – 4:00] 6. District-Level Forecast Products

*(Presenter scrolls to DistrictForecastTable and clicks on a district)*

> *"Operational forecasters require actionable administrative products. Below the globe is our **District Forecast Hierarchy Table**, covering Indian administrative districts:*
> * *Area-weighted mean precipitation;*
> * *Dominant synoptic regime;*
> * *Calibrated IMD severity categories (Heavy, Very Heavy, Extreme);*
> * *Calibrated uncertainty intervals [$P10 - P90$].*
>
> *Clicking on any district — like Satara or Ratnagiri — immediately flies the 3D camera to the district terrain and recalculates local orographic and coastal diagnostics in real-time."*

---

### [4:00 – 4:30] 7. Scientific Verification & Zero-Leakage Assurance

*(Presenter clicks on "Verification Hub" in the Header)*

> *"Let us open the **Verification Hub**. These metrics are evaluated on an independent, held-out prospective test dataset (2024–2025 JJAS seasons, $n=800$ cases):*
> * ***RMSE Reduction:*** *24.83 mm (Raw NWP) $\rightarrow$ **5.68 mm** (Regime-Aware AI) — a **77.1% error reduction**.*
> * ***Critical Success Index (CSI $\ge 64.5$mm):*** *0.291 $\rightarrow$ **0.869** (*$+198.6\%$ gain*).*
> * ***Equitable Threat Score (ETS):*** *0.250 $\rightarrow$ **0.843** (*$+237.2\%$ gain*).*
> * ***Spatial Fractions Skill Score (FSS @ 50km):*** *Reaches **0.957**, proving exceptional spatial alignment.*
>
> *We enforce a strict **chronological validation protocol** (2018–2022 train, 2023 validation, 2024–2025 test) with zero temporal data leakage."*

---

### [4:30 – 5:00] 8. Summary, Transparency & Future Operational Deployment

*(Presenter opens the Audit Drawer)*

> *"In conclusion, HydroWatch SIH26080 delivers:
> 1. Soft multi-label regime conditioning;
> 2. Physics-guided residual post-processing;
> 3. Calibrated exceedance probabilities and uncertainty bounds;
> 4. District-level products and 3D geospatial intelligence.
>
> **Operational Transparency:** As shown in our Data Provenance ledger, our prototype connects to approved open fallback feeds (NOAA GFS 0.25° / NASA POWER / RainViewer) with modular connectors engineered for direct plug-and-play integration with NCMRWF NCUM global and NEPS ensemble feeds on MoES HPC clusters.
>
> *Thank you. We are now ready for the jury's questions."*

---
*(End of 5-Minute Demonstration)*
