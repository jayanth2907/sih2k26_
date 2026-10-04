# NCMRWF / NEPS DATA CONTRACT
## SIH PS26080: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

**Document Version:** 1.0.0 (Phase 16)  
**Standard Authority:** Ministry of Earth Sciences (MoES) / NCMRWF  
**Target Systems:** NCUM-R (Regional 12km) & NEPS-R (Ensemble Prediction System 12km)

---

### 1. Meteorological Variable Ingestion Catalog

| Parameter | Standard Name | WMO GRIB2 Disc/Cat/Num | NCUM GRIB ShortName | Isobaric Levels (hPa) | Raw Units | Normalized SI Units |
|---|---|---|---|---|---|---|
| **Total Precipitation** | `total_precipitation` | 0 / 1 / 8 | `tp` / `precip` | Surface | $\text{kg/m}^2$ | $\text{mm}$ (liquid depth) |
| **Zonal Wind** | `u_component_of_wind` | 0 / 2 / 2 | `u` / `u850` | 850, 700, 500 | $\text{m/s}$ | $\text{m/s}$ |
| **Meridional Wind** | `v_component_of_wind` | 0 / 2 / 3 | `v` / `v850` | 850, 700, 500 | $\text{m/s}$ | $\text{m/s}$ |
| **Air Temperature** | `air_temperature` | 0 / 0 / 0 | `t` / `t850` | 850, 700, 500 | $\text{K}$ | $\text{K}$ (int) / $^\circ\text{C}$ (ext) |
| **Relative Humidity** | `relative_humidity` | 0 / 1 / 1 | `r` / `rh850` | 850, 700, 500 | $\%$ $[0-100]$ | $\%$ $[0.0-100.0]$ |
| **Geopotential Height**| `geopotential_height` | 0 / 3 / 5 | `gh` / `z` | 850, 700, 500 | $\text{gpm}$ / $\text{m}^2/\text{s}^2$ | $\text{meters (gpm)}$ |
| **Vertical Velocity** | `lagrangian_tendency_of_pressure` | 0 / 2 / 8 | `w` / `omega` | 700, 500 | $\text{Pa/s}$ | $\text{Pa/s}$ |
| **Mean Sea Level Pressure** | `pressure_reduced_to_msl` | 0 / 3 / 1 | `msl` / `mslp` | MSL (0m) | $\text{Pa}$ | $\text{hPa}$ |
| **Surface Pressure** | `surface_air_pressure` | 0 / 3 / 0 | `sp` | Surface | $\text{Pa}$ | $\text{hPa}$ |
| **CAPE** | `convective_available_potential_energy` | 0 / 7 / 6 | `cape` | Surface / Layer | $\text{J/kg}$ | $\text{J/kg}$ |

---

### 2. NEPS Ensemble Member Invariant

- **Member Allocation:** Control Member (`mbr_00`) + 22 Perturbed Members (`mbr_01` to `mbr_22`) = **23 total members**.
- **Ensemble Policy:**
  - If fewer than 23 members are delivered (e.g. late network delivery of 18 members), calculate statistics across actual available members ($N=18$) and explicitly record `member_count: 18`.
  - **NEVER** fabricate missing members or duplicate members to artificially achieve 23 members.
- **Parametric & Non-Parametric Metrics:**
  - Ensemble Mean: $\mu = \frac{1}{N}\sum_{i=1}^N x_i$
  - Ensemble Standard Deviation: $\sigma = \sqrt{\frac{1}{N-1}\sum_{i=1}^N (x_i - \mu)^2}$
  - Non-parametric Quantiles: $P_{10}, P_{25}, P_{50}\text{ (Median)}, P_{75}, P_{90}$
  - Exceedance Probabilities: $\text{Prob}(X \ge 64.5\text{ mm}), \text{Prob}(X \ge 115.6\text{ mm}), \text{Prob}(X \ge 204.5\text{ mm})$

---

### 3. Spatial Domain & Grid Specifications

- **Coordinate Reference System (CRS):** Standard WGS84 (`EPSG:4326`)
- **Spatial Coverage:** Latitude $6.0^\circ\text{N} - 38.0^\circ\text{N}$, Longitude $68.0^\circ\text{E} - 98.0^\circ\text{E}$
- **Grid Spacing:** $0.12^\circ \times 0.12^\circ$ (~12 km resolution)
- **Cell Indexing:** North-to-South row-major indexing with $(0,0)$ at $(38.0^\circ\text{N}, 68.0^\circ\text{E})$.
