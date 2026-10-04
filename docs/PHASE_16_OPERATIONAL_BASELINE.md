# PHASE 16 — OPERATIONAL BASELINE AUDIT
## SIH PS26080: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

**Document Version:** 1.0.0  
**Phase:** 16 (Operational Integration & NCMRWF/NEPS Readiness)  
**Evaluated At:** 2026-10-03 UTC  
**Institutional Target:** National Centre for Medium Range Weather Forecasting (NCMRWF) / Ministry of Earth Sciences (MoES)

---

### 1. Ingestion Architecture Overview

The PS26080 operational data ingestion layer is designed to bridge operational Numerical Weather Prediction (NWP) models and empirical observations into a unified, regime-aware post-processing pipeline.

```
+-----------------------------------------------------------------------------------+
|                        OPERATIONAL INGESTION PATHWAY                              |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [PRIMARY] NCMRWF NCUM 12km (GRIB2/NetCDF)  ───┐                                 |
|  [SECONDARY] NCMRWF NEPS 23-Member (GRIB2)  ──┼──> [GRIB2 Validator & Quarantine]|
|  [FALLBACK] NOAA GFS 0.25° (Open-Meteo REST) ─┤                    │              |
|  [STANDBY] Deterministic Calibrated Demo ─────┘                    ▼              |
|                                                     [Unit & Spatial/Temporal Norm]|
|                                                                    │              |
|                                                                    ▼              |
|                                                     [Meteorological Quality Control]|
|                                                                    │              |
|                                                                    ▼              |
|                                                     [Canonical Meteorological Record]
|                                                                    │              |
|                                                                    ▼              |
|                                                     [Atmospheric Feature Engineering]
|                                                                    │              |
|                                                                    ▼              |
|                                                     [Weather Regime Engine]       |
|                                                                    │              |
|                                                                    ▼              |
|                                                     [Spatial ConvNet Post-Process]|
|                                                                    │              |
|                                                                    ▼              |
|                                                     [748 District Polygon Aggregation]
+-----------------------------------------------------------------------------------+
```

---

### 2. Source Routing & Operational States

| Operational Source | Priority Tier | Operational State | Ingestion Protocol | Live Connected? | Fallback Trigger |
|---|---|---|---|---|---|
| **NCMRWF NCUM 12km** | PRIMARY | `LIVE_NCMRWF` / `DEMO_SYNTHETIC` | GRIB2 / NetCDF via OPeNDAP/FTP | NO (Adapter Ready) | `LIVE_NCMRWF_GATEWAY_NOT_CONFIGURED` |
| **NCMRWF NEPS 23M** | SECONDARY | `LIVE_NEPS` / `DEMO_SYNTHETIC` | GRIB2 Multi-member | NO (Adapter Ready) | `LIVE_NEPS_GATEWAY_NOT_CONFIGURED` |
| **NOAA GFS (Open-Meteo)** | DEV FALLBACK | `DEVELOPMENT_GFS` | REST API (JSON) | YES (Active Fallback) | Network/API Timeout |
| **Calibrated Demo Standby** | DEMO STANDBY | `DEMO_SYNTHETIC` | Deterministic Fixture | YES (Offline Standby) | Always Available |

**Governance Guarantee:**
1. Zero silent downgrades: every fallback transition records `requested_source`, `active_source`, and `fallback_reason`.
2. Explicit state reporting: Fallback data is never labeled as `LIVE_NCMRWF`.

---

### 3. GRIB2 Support & Strict Validation

Operational validation is enforced by `GRIB2Validator`:
- **Byte verification:** `GRIB` magic header prefix, GRIB Edition 2 indicator, and `7777` message termination check.
- **Envelope validation:** Latitude $[6^\circ\text{N}, 38^\circ\text{N}]$, Longitude $[68^\circ\text{E}, 98^\circ\text{E}]$.
- **Physical plausibility limits:**
  - Precipitation: $[0, 1500]\text{ mm/day}$
  - Temperature: $[180, 340]\text{ K}$ ($-93^\circ\text{C}\text{ to }+67^\circ\text{C}$)
  - Relative Humidity: $[0, 100]\%$
  - Atmospheric Pressure: $[300, 1085]\text{ hPa}$
  - Wind Speed: $[0, 120]\text{ m/s}$
  - CAPE: $[0, 8000]\text{ J/kg}$
- **Quarantine logic:** Corrupted headers or out-of-bounds parameters are quarantined (`QUARANTINED` status) rather than silently propagated.

---

### 4. Normalization Standards

- **Units (`UnitNormalizer`):**
  - Precipitation $\to\text{mm}$ (liquid equivalent)
  - Temperature $\to\text{Kelvin}$ (internal model state) / $^\circ\text{C}$ (display)
  - Pressure $\to\text{hPa}$
  - Wind $\to\text{m/s}$ and knots
  - Relative Humidity $\to [0, 100]\%$
- **Spatial (`SpatialTemporalNormalizer`):**
  - Longitude normalization $[0, 360] \to [-180, 180]$
  - Grid cell bounds and center coordinate verification
- **Temporal (`SpatialTemporalNormalizer`):**
  - Canonical ISO-8601 UTC representation (`YYYY-MM-DDTHH:MM:SSZ`)
  - Explicit IST offset conversion ($+05:30$) for district bulletins

---

### 5. Current Data Latency & Freshness Assumptions

- **Operational Cycle Ingestion:** 00 UTC, 06 UTC, 12 UTC, 18 UTC
- **Freshness Classification:**
  - `FRESH`: Age $\le 18\text{ hours}$
  - `AGING`: $18\text{ hours} < \text{Age} \le 30\text{ hours}$
  - `STALE`: $\text{Age} > 30\text{ hours}$
  - `UNAVAILABLE`: Feed unreachable or unparsed

---

### 6. Institutional Security & Verification State

- **Credential Exposure:** Zero secrets, API keys, or private internal URLs stored in code or configuration.
- **Operational Readiness Level:** **LEVEL 1 — ADAPTER ARCHITECTURE & LOCAL INGESTION**
- **Production Baseline Integrity:** Baseline models and Phase 15 verification numbers remain untouched.
