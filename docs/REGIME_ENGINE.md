# Weather Regime Intelligence Engine (PS26080)
**Smart India Hackathon 2026 — Problem Statement SIH26080**  
**Organization:** Ministry of Earth Sciences (MoES)  
**Department:** National Centre for Medium Range Weather Forecasting (NCMRWF)

---

## 1. Executive Summary & Synoptic Context

Numerical Weather Prediction (NWP) precipitation forecasts over the South Asian Summer Monsoon (SASM) domain suffer from substantial state-dependent systematic biases. In particular, stationary post-processing methods (such as simple statistical downscaling or unconditioned quantile mapping) fail because the underlying physical mechanisms generating rainfall vary dramatically across synoptic and mesoscale weather regimes.

The PS26080 Weather Regime Intelligence Engine (`backend/app/regime/`) provides an objective, multi-label diagnostic and probabilistic classification layer. It decomposes the complex atmospheric flow into 6 distinct physical regimes, derives calibrated probability distributions and regime confidences, and produces grounded explainability (XAI) drivers.

```
+---------------------------------------------------------------------------------------------------+
|                            CANONICAL ATMOSPHERIC STATE & NWP PREDICTORS                           |
|  - 850 / 700 / 500 hPa Geopotential, Temperature, Humidity, Wind Vectors (u, v)                   |
|  - Mean Sea Level Pressure (MSLP) & Surface Pressure                                              |
|  - Convective Available Potential Energy (CAPE) & Vertical Velocity (Omega)                       |
|  - Topographic Predictors: Elevation (m), Slope (°), Aspect (°), Distance to Coast (km)           |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                 SYNOPTIC FEATURE EXTRACTION                                       |
|  - Low-Level Jet (LLJ) speed (kts) & direction (°)        - Mid-Tropospheric Vorticity (10⁻⁵ s⁻¹) |
|  - Monsoon Trough Latitude & Axial Orientation            - Outgoing Longwave Radiation (OLR)     |
|  - Integrated Vapor Transport (IVT) Proxy                 - Barometric MSLP Departure (hPa)       |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                             PARALLEL MODULAR REGIME DETECTORS                                     |
|  +------------------------+  +------------------------+  +------------------------+               |
|  | Active/Break Detector  |  |   Monsoon LPS / Dep    |  |  Coastal Convergence   |               |
|  | (LLJ > 28kts, OLR<210) |  | (Vorticity, MSLP Anom) |  | (d_coast<150km, Onshore|               |
|  +------------------------+  +------------------------+  +------------------------+               |
|  +------------------------+  +------------------------+  +------------------------+               |
|  |  Orographic Lifting    |  |  Western Disturbance   |  |   Neutral Baseline     |               |
|  | (Slope, V_normal, OLI) |  | (500hPa Trough, N.Ind) |  | (Suppressed Activity)  |               |
|  +------------------------+  +------------------------+  +------------------------+               |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                       MULTI-LABEL REGIME ARBITRATION & CALIBRATION                                |
|  - Probability Distribution: P(Active), P(Break), P(LPS), P(Coastal), P(Orographic), P(WD), P(Neut)|
|  - Primary Regime Selection & Multi-Label Secondary Regime Identification                         |
|  - Calibrated Confidence Score derived from Signal Margin & Strength                              |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                         GROUNDED EXPLAINABILITY (XAI) & NARRATIVE                                 |
|  - Quantified Atmospheric Drivers (Feature, Observed Value, Normalized Importance)                |
|  - Scientifically Grounded Physical Meteorological Diagnostic Narrative                           |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Weather Regime Taxonomy & Physical Criteria

The South Asian monsoon comprises distinct physical phenomena that must NOT be treated as mutually exclusive:

### A. Active Monsoon (`ACTIVE_MONSOON`)
* **Synoptic Trigger:** Strong cross-equatorial Low-Level Jet (LLJ $\ge 28\text{ kts}$ at 850 hPa), active monsoon trough positioned south of its normal climatological position ($21.5^\circ - 24.5^\circ\text{N}$), deep convection ($\text{OLR} \le 210\text{ W/m}^2$), and high moisture transport.
* **Precipitation Character:** Widespread, persistent heavy rainfall across the core monsoon zone (Central India and Peninsular west coast).

### B. Break Monsoon (`BREAK_MONSOON`)
* **Synoptic Trigger:** Monsoon trough shifted northwards to the Himalayan foothills ($\ge 27.0^\circ\text{N}$), suppressed peninsular westerlies (LLJ $\le 15\text{ kts}$), dry continental air intrusion ($\text{RH}_{850} < 60\%$), and suppressed convection ($\text{OLR} \ge 240\text{ W/m}^2$).
* **Precipitation Character:** Severe rainfall cessation over Central India, with localized heavy precipitation confined to the Himalayan foothills and Northeast India.

### C. Monsoon Low Pressure System / Depression (`MONSOON_LOW_LPS`)
* **Synoptic Trigger:** Organized cyclonic vortex in the lower-to-mid troposphere ($\zeta_{850} \ge 3.5 \times 10^{-5}\text{ s}^{-1}$), significant barometric MSLP depression ($\Delta P \le -4.0\text{ hPa}$), and intense spiral moisture convergence.
* **Kinematics:** Tracks typically west-northwestward from the Head Bay of Bengal across Odisha, West Bengal, and Central India at speeds of $12 - 25\text{ km/h}$.

### D. Coastal Convergence (`COASTAL_CONVERGENCE`)
* **Synoptic Trigger:** Proximity to coastline ($d_{\text{coast}} \le 150\text{ km}$), onshore wind vector ($\theta_{\text{wind}} \in [210^\circ, 310^\circ]$ for West Coast / $[50^\circ, 150^\circ]$ for East Coast), and boundary layer friction differential.
* **Precipitation Character:** Nocturnal-to-morning offshore trough showers and intense coastal convergence bands.

### E. Orographic Rainfall Enhancement (`OROGRAPHIC_RAINFALL`)
* **Synoptic Trigger:** Topographic elevation ($\ge 250\text{ m}$), steep slope ($\ge 1.8^\circ$), high slope-normal wind component ($V_{\text{normal}} = V_{850} \cdot |\cos(\theta_{\text{wind}} - \theta_{\text{aspect}})| \ge 7.0\text{ m/s}$), and near-saturated boundary layer moisture ($\text{RH}_{850} \ge 75\%$).
* **Precipitation Character:** Mechanical forced adiabatic ascent, rapid condensation, and localized extreme precipitation cores along the Western Ghats windward escarpment and Khasi Hills.

### F. Western Disturbance (`WESTERN_DISTURBANCE`)
* **Synoptic Trigger:** Extratropical upper-tropospheric wave over North/Northwest India ($24^\circ - 38^\circ\text{N}, 68^\circ - 88^\circ\text{E}$), deep 500 hPa geopotential height trough ($\Delta \Phi_{500} \le -40\text{ gpm}$), and strong subtropical westerly jet stream core ($u_{500} \ge 25\text{ m/s}$).
* **Seasonality:** Peak in winter/spring (Oct–Apr); occasional destructive interaction with summer monsoon westerlies (e.g. Kedarnath 2013, Himachal 2023).

---

## 3. Objective Thresholds Configuration (`config/regime.yaml`)

All physical thresholds are declaratively defined in `config/regime.yaml` ensuring zero hardcoded magic numbers:

```yaml
version: "2.0.0"

active_break:
  monsoon_trough_lat_normal: 24.5
  monsoon_trough_active_south_threshold: 22.0
  monsoon_trough_break_foothill_threshold: 27.0
  low_level_jet_850_critical_speed_kts: 28.0
  low_level_jet_850_break_speed_kts: 15.0
  olr_convective_active_w_m2: 210.0
  olr_suppressed_break_w_m2: 240.0
  core_monsoon_rainfall_active_mm: 12.0
  core_monsoon_rainfall_break_mm: 4.0

lps_detector:
  mslp_depression_threshold_hpa: 996.0
  mslp_low_threshold_hpa: 1002.0
  pressure_gradient_threshold_hpa_deg: 2.0
  vorticity_850_threshold_1e5_s: 3.5
  geopotential_anomaly_850_gpm: -25.0
  search_radius_km: 450.0

coastal_detector:
  max_distance_to_coast_km: 120.0
  min_onshore_wind_speed_850_ms: 6.0
  min_relative_humidity_850_pct: 75.0
  coastal_convergence_index_min: 0.35

orographic_detector:
  min_elevation_m: 250.0
  min_slope_degrees: 1.8
  min_wind_perpendicular_speed_ms: 7.0
  min_moisture_flux_g_kg_ms: 80.0
  orographic_lift_index_threshold: 0.40

western_disturbance:
  target_lat_min: 24.0
  target_lat_max: 38.0
  target_lon_min: 68.0
  target_lon_max: 88.0
  active_months: [1, 2, 3, 4, 10, 11, 12]
  monsoon_interaction_months: [6, 7, 8, 9]
  upper_trough_500hpa_geopotential_anomaly_gpm: -40.0
  jet_streak_200hpa_wind_speed_ms: 45.0
```

---

## 4. Multi-Label Classification & Probabilistic Calibration

### Multi-Label Architecture
Meteorological regimes frequently co-occur. For example, during an **Active Monsoon** spell, intense precipitation at Mahabaleshwar or Agumbe is simultaneously driven by **Orographic Lifting** and **Coastal Convergence**. 

The classifier computes:
1. $P(\text{regime}_i) \in [0.0, 1.0]$ for all 6 regimes + Neutral.
2. $\text{Primary Regime} = \arg\max_i P(\text{regime}_i)$.
3. $\text{Secondary Regimes} = \{ \text{regime}_j \mid P(\text{regime}_j) \ge 0.28, j \ne \text{Primary} \}$.

### Confidence Formulation
Confidence is not a static constant ($0.9$); it is derived from signal strength and the probabilistic margin of victory:
$$\text{Margin} = P(\text{Primary}) - P(\text{Runner-Up})$$
$$\text{Confidence} = \text{clamp}\left(0.70 \cdot P(\text{Primary}) + 0.30 \cdot \text{Margin} + 0.15, \quad [0.40, 0.98]\right)$$

---

## 5. Grounded Explainability (XAI) Output

Every regime classification produces an array of quantified `AtmosphericDriver` objects grounded exclusively in features used during diagnosis:

```json
{
  "primary_regime": "OROGRAPHIC_RAINFALL",
  "confidence": 0.91,
  "secondary_regimes": ["ACTIVE_MONSOON", "COASTAL_CONVERGENCE"],
  "probabilities": {
    "ACTIVE_MONSOON": 0.68,
    "BREAK_MONSOON": 0.05,
    "MONSOON_LOW_LPS": 0.22,
    "COASTAL_CONVERGENCE": 0.54,
    "OROGRAPHIC_RAINFALL": 0.88,
    "WESTERN_DISTURBANCE": 0.03,
    "NEUTRAL": 0.12
  },
  "drivers": [
    {
      "feature": "terrain_elevation",
      "value": 1350.0,
      "importance": 0.35,
      "description": "High topographic barrier triggering forced adiabatic ascent"
    },
    {
      "feature": "850_hPa_wind_speed",
      "value": 18.4,
      "importance": 0.28,
      "description": "Perpendicular onshore wind vector impinging on mountain ridge"
    },
    {
      "feature": "orographic_lift_index",
      "value": 0.742,
      "importance": 0.22,
      "description": "Strong slope-normal velocity condensation potential"
    },
    {
      "feature": "relative_humidity_850",
      "value": 92.0,
      "importance": 0.15,
      "description": "Near-saturated inflow at cloud base level"
    }
  ],
  "regime_narrative": "Orographic Lifting Rainfall Enhancement (91% confidence). Strong moist onshore inflow (18.4 m/s) impinging upon elevated terrain inducing mechanical adiabatic expansion, saturated ascent, and heavy localized precipitation. Co-occurring secondary physical mechanisms: ACTIVE MONSOON, COASTAL CONVERGENCE.",
  "model_version": "RegimeClassifier_v2.0_Hybrid",
  "data_source": "NCMRWF_NCUM",
  "is_demo": false,
  "timestamp": "2026-09-30T12:00:00Z"
}
```

---

## 6. Scientific Data Transparency Rules

1. **Explicit `is_demo` Flag:** When actual NCMRWF feeds are in development or offline, the system sets `is_demo: true` and `data_source: "NCMRWF_NCUM_DEMO_SYNTHESIS"` or `"NOAA_GFS_OPENMETEO_FALLBACK"`.
2. **Attribution Integrity:** GFS fallback data are never labeled as NCMRWF observations.
3. **Reproducibility:** Demo datasets use fixed seeds (`seed=42`) and are never used to make claims of empirical operational accuracy.
