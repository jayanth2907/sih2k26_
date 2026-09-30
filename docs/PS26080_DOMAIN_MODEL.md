# PS26080 — Domain Model & Meteorological Ontology

> **Target Problem Statement**: SIH26080  
> **Title**: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts  
> **Organization**: Ministry of Earth Sciences (MoES)  
> **Department**: National Centre for Medium Range Weather Forecasting (NCMRWF)

---

## 1. Domain Entities & Class Taxonomy

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 MONSOON WEATHER REGIME                                 │
│  ├── Primary Regime (Enum)                                                             │
│  ├── Secondary Regimes (List[Enum])                                                    │
│  ├── Confidence Score (0.0 to 1.0)                                                     │
│  └── Synoptic Signatures (LLJ speed, Trough position, OLR anomaly, Moisture flux)      │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ conditions
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              POST-PROCESSING METHOD TIER                               │
│  ├── Product 1: Raw NWP (Baseline NCUM / GFS Fallback)                                 │
│  ├── Product 2: Empirical Quantile Mapping (EQM Statistical Benchmark)                │
│  ├── Product 3: Global ML Correction (Standard ResNet/XGBoost non-regime)              │
│  └── Product 4: Regime-Aware AI Post-Processing (Target MoES/NCMRWF Architecture)      │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ yields
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             CALIBRATED PRECIPITATION METRICS                           │
│  ├── Corrected 24h Accumulated Rainfall (mm)                                           │
│  ├── Peak Hourly Precipitation Intensity (mm/h)                                        │
│  ├── Forecast Uncertainty Bounds (Lower bound, Upper bound, Ensemble spread mm)        │
│  ├── 24-Hour Chronological Meteogram Time Series                                       │
│  └── Isohyet Vector Contours (RFC 7946 GeoJSON)                                        │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ evaluates
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                           HEAVY RAINFALL PROBABILISTIC TIERS                           │
│  ├── Heavy Rainfall Probability (>= 64.5 mm/day)                                       │
│  ├── Very Heavy Rainfall Probability (>= 115.6 mm/day)                                 │
│  └── Extremely Heavy Rainfall Probability (>= 204.5 mm/day)                            │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ assesses
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        VERIFICATION SKILL & RELIABILITY BENCHMARK                      │
│  ├── Deterministic Error: Root Mean Square Error (RMSE mm)                             │
│  ├── Categorical Scores: Equitable Threat Score (ETS), Critical Success Index (CSI)    │
│  ├── Skill Ratios: Probability of Detection (POD), False Alarm Ratio (FAR)             │
│  └── Spatial Verification: Fractions Skill Score (FSS at 25km, 50km, 100km radii)      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Weather Regime Definitions & Hierarchical Structure

In the South Asian Summer Monsoon (SASM), rainfall is driven by distinct multi-scale meteorological mechanisms:

| Regime ID | Classification Name | Synoptic Characteristics | Common Secondary Co-Occurrences |
| :--- | :--- | :--- | :--- |
| `ACTIVE_MONSOON` | Active Monsoon Spell | Strong low-level monsoon westerlies ($>30\text{ kts}$ at 850 hPa), southern shift of the monsoon trough, intense regional convection. | `OROGRAPHIC_RAINFALL`, `COASTAL_CONVERGENCE` |
| `BREAK_MONSOON` | Break Monsoon Spell | Monsoon trough shifts north to Himalayan foothills; rainfall suppressed over central India, confined to Northeast and Himalayan slopes. | `OROGRAPHIC_RAINFALL`, `NEUTRAL` |
| `MONSOON_LOW_LPS` | Monsoon Low / Depression | Low Pressure System (LPS) forming over Bay of Bengal / Arabian Sea moving inland along the monsoon trough, producing torrential rainfall cores. | `ACTIVE_MONSOON`, `COASTAL_CONVERGENCE` |
| `COASTAL_CONVERGENCE` | Coastal Rainfall / Offshore Trough | Trough of low pressure off the West Coast of India (Konkan to Kerala), triggering intense low-level onshore moisture convergence. | `ACTIVE_MONSOON`, `OROGRAPHIC_RAINFALL` |
| `OROGRAPHIC_RAINFALL` | Orographic Precipitation | Mechanical uplift of moist monsoon flow against Western Ghats, Meghalaya plateau, or Himalayan foothills. | `ACTIVE_MONSOON`, `BREAK_MONSOON` |
| `WESTERN_DISTURBANCE` | Western Disturbance | Mid-latitude upper-tropospheric trough moving eastward across northwest India, interacting with monsoonal moisture. | `NEUTRAL` |
| `NEUTRAL` | Neutral / Climatological | Weak or transition circulation without dominant synoptic forcing. | None |

---

## 3. Four Post-Processing Products

1. **Raw NWP Baseline**: Direct deterministic/ensemble grid output from numerical models (NCMRWF NCUM 12km or GFS 0.25° fallback) suffering from spatial displacement and extreme event underestimation.
2. **Empirical Quantile Mapping (EQM)**: Statistical correction mapping cumulative distribution functions (CDFs) of NWP predictions to historical ground observations.
3. **Global ML Correction**: Machine learning model (e.g. standard deep CNN or XGBoost) trained across all seasons and regions without circulation regime conditioning.
4. **Regime-Aware AI Post-Processing**: The target MoES/NCMRWF state-of-the-art approach where correction weights and spatial bias kernels are conditioned on the identified synoptic regime, dramatically improving skill in extreme localized downbursts.

---

## 4. Heavy Rainfall Probabilistic Thresholds (IMD Standards)

- **Heavy Rainfall**: $\ge 64.5\text{ mm/day}$
- **Very Heavy Rainfall**: $\ge 115.6\text{ mm/day}$
- **Extremely Heavy Rainfall**: $\ge 204.5\text{ mm/day}$

---

## 5. Severe Rainfall Outlook States (Transforming Warning Panel)

- **`NORMAL`**: Rainfall $<64.5\text{ mm}$, probability of heavy rain $<30\%$.
- **`WATCH`**: Enhanced moisture or moderate accumulation ($30\%\le P < 60\%$).
- **`HEAVY_RAINFALL`**: High probability ($\ge 60\%$) of heavy precipitation ($\ge 64.5\text{ mm}$).
- **`VERY_HEAVY_RAINFALL`**: High probability ($\ge 40\%$) of very heavy rainfall ($\ge 115.6\text{ mm}$).
- **`EXTREME_RAINFALL`**: Convective extreme downburst signature with significant probability of $\ge 204.5\text{ mm/day}$.
