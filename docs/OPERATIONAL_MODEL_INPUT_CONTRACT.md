# OPERATIONAL MODEL INPUT CONTRACT
## SIH PS26080: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

**Standard Version:** 1.0.0 (Phase 16)  
**Applies to:** NCUM 12km, NEPS Ensemble, GFS Fallback, and Statistical / ML Post-Processing Models

---

### 1. Purpose & Contract Principles

The Operational Model Input Contract strictly defines mandatory, optional, derived, and unavailable features required by the PS26080 AI post-processing engine. 

**Core Rules:**
1. **No Silent Zero-Filling:** If a `REQUIRED` feature is absent, the pipeline aborts inference and returns `MODEL_INPUT_INCOMPLETE`.
2. **Explicit Derivations:** Derived indices are computed only from physically appropriate thermodynamic and kinematic state variables.
3. **Transparent Substitution Guard:** Unrelated variables cannot be substituted to satisfy missing feature names.

---

### 2. Feature Specification Matrix

| Feature Key | Classification | Expected Physical Units | Permissible Range | Description |
|---|---|---|---|---|
| `rainfall` / `tp` | **REQUIRED** | mm liquid equiv. | $[0.0, 1500.0]$ | NWP raw accumulated precipitation |
| `u850` | **REQUIRED** | $\text{m/s}$ | $[-80.0, 80.0]$ | 850 hPa zonal wind component |
| `v850` | **REQUIRED** | $\text{m/s}$ | $[-80.0, 80.0]$ | 850 hPa meridional wind component |
| `temperature_850` | **REQUIRED** | Kelvin | $[250.0, 320.0]$ | 850 hPa thermodynamic temperature |
| `relative_humidity_850` | **REQUIRED** | $\%$ | $[0.0, 100.0]$ | 850 hPa relative humidity |
| `mslp` | **REQUIRED** | $\text{hPa}$ | $[900.0, 1050.0]$ | Mean Sea Level Pressure |
| `latitude` | **REQUIRED** | decimal degrees | $[6.0, 38.0]$ | Grid cell or point latitude |
| `longitude` | **REQUIRED** | decimal degrees | $[68.0, 98.0]$ | Grid cell or point longitude |
| `lead_time_hours` | **REQUIRED** | hours | $[0, 240]$ | Forecast step horizon |
| `u700` | **OPTIONAL** | $\text{m/s}$ | $[-80.0, 80.0]$ | 700 hPa zonal wind component |
| `v700` | **OPTIONAL** | $\text{m/s}$ | $[-80.0, 80.0]$ | 700 hPa meridional wind component |
| `u500` | **OPTIONAL** | $\text{m/s}$ | $[-100.0, 100.0]$ | 500 hPa zonal wind component |
| `v500` | **OPTIONAL** | $\text{m/s}$ | $[-100.0, 100.0]$ | 500 hPa meridional wind component |
| `temperature_700` | **OPTIONAL** | Kelvin | $[240.0, 310.0]$ | 700 hPa thermodynamic temperature |
| `temperature_500` | **OPTIONAL** | Kelvin | $[220.0, 290.0]$ | 500 hPa thermodynamic temperature |
| `relative_humidity_700`| **OPTIONAL** | $\%$ | $[0.0, 100.0]$ | 700 hPa relative humidity |
| `relative_humidity_500`| **OPTIONAL** | $\%$ | $[0.0, 100.0]$ | 500 hPa relative humidity |
| `vertical_velocity` | **OPTIONAL** | $\text{Pa/s}$ | $[-5.0, 5.0]$ | Mid-tropospheric omega |
| `cape_j_kg` | **OPTIONAL** | $\text{J/kg}$ | $[0.0, 8000.0]$ | Convective Available Potential Energy |
| `elevation` | **STATIC** | meters | $[-50.0, 8848.0]$| SRTM topographic elevation |
| `slope` | **STATIC** | degrees | $[0.0, 60.0]$ | Digital Elevation Model terrain gradient |
| `aspect` | **STATIC** | degrees | $[0.0, 360.0]$ | Terrain downslope direction |
| `distance_to_coast` | **STATIC** | km | $[0.0, 2000.0]$ | Shortest distance to Indian coastline |
| `wind_speed_850` | **DERIVED** | $\text{m/s}$ | $[0.0, 120.0]$ | $\sqrt{u_{850}^2 + v_{850}^2}$ |
| `wind_direction_850` | **DERIVED** | degrees | $[0.0, 360.0]$ | $(270 - \text{atan2}(v_{850}, u_{850})) \pmod{360}$ |
| `vertical_wind_shear`| **DERIVED** | $\text{m/s}$ | $[0.0, 100.0]$ | $\sqrt{(u_{500}-u_{850})^2 + (v_{500}-v_{850})^2}$ |
| `moisture_transport` | **DERIVED** | $\text{g/kg}\cdot\text{m/s}$ | $[0.0, 500.0]$ | $q_{850} \cdot V_{850}$ |
| `orographic_lift` | **DERIVED** | dimensionless | $[0.0, 50.0]$ | $(V_{850} \cdot |\cos(\theta_{wind}-\theta_{aspect})| \tan(\alpha)) \cdot \frac{z}{1000}$ |
| `coastal_indicator` | **DERIVED** | dimensionless | $[0.0, 50.0]$ | $(V_{850} \cdot \frac{\text{RH}_{850}}{100}) \cdot e^{-d_{\text{coast}}/75}$ |
| `ensemble_spread` | **NEPS ONLY** | mm | $[0.0, 500.0]$ | $P_{90} - P_{10}$ or $2\sigma$ across members |
| `imd_observation` | **VERIFICATION** | mm | $[0.0, 1500.0]$| Ground truth target (never used in inference) |

---

### 3. Missing Feature Behavior & Diagnostic Codes

When input records fail contract validation:
```json
{
  "status": "MODEL_INPUT_INCOMPLETE",
  "is_inference_ready": false,
  "source": "NCMRWF_NCUM",
  "forecast_time": "2026-10-01T00:00:00Z",
  "required_features_present": ["rainfall", "temperature_850", "mslp"],
  "missing_features": ["u850", "v850", "relative_humidity_850"],
  "error_message": "Model input feature contract violation: missing mandatory fields ['u850', 'v850', 'relative_humidity_850']"
}
```
