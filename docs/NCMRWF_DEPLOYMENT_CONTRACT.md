# NCMRWF DEPLOYMENT CONTRACT
## SIH PS26080: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

**Standard Target:** NCMRWF High-Performance Computing (HPC) & Automated Operations  
**Evaluation Status:** PHASE 16 AUDIT (Operational Integration & Readiness)  
**Readiness Level:** LEVEL 1 (Adapter Architecture + Local GRIB2 Ingestion)

---

### 1. Operational Deployment Requirements & Readiness Matrix

| Requirement Component | Operational Specification | Target Facility | Current Status | Notes / Remediation |
|---|---|---|---|---|
| **NWP Model Core** | NCUM Regional 12km Deterministic | NCMRWF Cray XC40 / Mihir HPC | **IMPLEMENTED (ADAPTER)** | Adapter & GRIB2 reader fully functional |
| **Ensemble Model Core**| NEPS 23-member Ensemble 12km | NCMRWF HPC | **IMPLEMENTED (ADAPTER)** | Non-parametric quantile calculations validated |
| **GRIB2 Ingestion & Parser** | WMO GRIB Edition 2 Decoder | Local / Cloud Engine | **IMPLEMENTED** | Byte-level header & parameter validation active |
| **Quarantine Subsystem** | Automatic corrupted file isolation | Local Staging | **IMPLEMENTED** | Magic header & domain bounds filtering |
| **Operational Gateway** | Dedicated MoES / NCMRWF Secure API / OPeNDAP | NCMRWF Noida Gateway | **PENDING** | Requires institutional network credentials |
| **Authentication / Keys** | TLS Mutual Auth / VPN Tunnel | MoES Network Operations | **PENDING** | Environment secret isolation enforced |
| **Forecast Cycles** | 00Z, 06Z, 12Z, 18Z UTC Ingestion | Operational Cron / Trigger | **IMPLEMENTED (SCHEDULE)** | Cycle tracking endpoint active |
| **Variable Mapping** | 12 Mandatory Upper-Air & Surface Fields | NCUM Variable Table | **IMPLEMENTED** | Normalizer maps NCUM GRIB parameter IDs |
| **Spatial Resolution** | 12km (~0.12°) Regional Grid | South Asia Domain | **IMPLEMENTED** | Spatial domain normalizer active |
| **Latency SLA** | Inference < 200ms per point, < 2.5s for Full India Grid | Production Server | **IMPLEMENTED (MEASURED)**| Pipeline benchmark: 108.5ms per step |
| **Operational Provenance** | Unambiguous source attribution & fallback | Inference Response Schema | **IMPLEMENTED** | Provenance stamped on every object |
| **Staleness Monitoring** | Alert on forecasts > 30 hours old | Operational Router | **IMPLEMENTED** | Freshness tracker active (FRESH/AGING/STALE) |

---

### 2. Live Ingestion Deployment Checklist

To transition from **Level 1** (Adapter/Local Ingestion) to **Level 4** (Live Operational Connected Pipeline):

1. [ ] Configure institutional MoES / NCMRWF OPeNDAP or SFTP endpoint in `.env` (kept secure from git).
2. [ ] Establish automated file polling daemon for 00Z, 06Z, 12Z, and 18Z cycles.
3. [ ] Activate live GRIB2 byte-stream verification with `GRIB2Validator.validate_grib_bytes`.
4. [ ] Enable `primary_enabled=True` in `OperationalSourceRouter`.
5. [ ] Ensure automatic non-silent downgrade to `NOAA_GFS_OPENMETEO_FALLBACK` if gateway latency exceeds 15 seconds.
