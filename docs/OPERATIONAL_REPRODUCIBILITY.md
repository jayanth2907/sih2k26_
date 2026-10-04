# OPERATIONAL REPRODUCIBILITY GUIDE
## SIH PS26080: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

**Document Version:** 1.0.0 (Phase 16)  
**Standard Target:** NCMRWF Operational Unified Model (NCUM) & Ensemble Prediction System (NEPS)

---

### Step-by-Step 17-Stage Operational Execution Pipeline

The complete operational execution flow from raw GRIB2/NetCDF delivery to district decision intelligence and export proceeds deterministically as follows:

1. **Obtain NWP File / Stream:**
   - Ingest raw NCUM 12km deterministic or NEPS 23-member ensemble GRIB2 payload via local staging directory or secure institutional gateway.

2. **Validate GRIB2 Structure & Integrity (`GRIB2Validator`):**
   - Execute byte magic header check (`GRIB`), edition check (Edition 2), parameter inventory check, coordinate bound validation, and physical plausibility filtering.
   - Quarantine corrupted or unphysical files (`QUARANTINED`).

3. **Normalize Units (`UnitNormalizer`):**
   - Convert precipitation flux/meters to cumulative mm liquid equivalent.
   - Convert temperature to Kelvin / Celsius, pressure to hPa, wind to m/s, and relative humidity to percentage ($0-100\%$).

4. **Normalize Spatial Grid (`SpatialTemporalNormalizer`):**
   - Standardize longitudes $[0, 360] \to [-180, 180]$.
   - Validate bounding box against South Asia domain envelope $[6.0^\circ\text{N}, 38.0^\circ\text{N}]$, $[68.0^\circ\text{E}, 98.0^\circ\text{E}]$.

5. **Normalize Temporal Conventions (`SpatialTemporalNormalizer`):**
   - Parse initialization cycle and valid time to canonical ISO-8601 UTC.
   - Enforce temporal invariant: $\text{valid\_time} = \text{forecast\_init} + \text{lead\_hours}$.

6. **Construct Canonical Meteorological Record (`CanonicalMeteorologicalRecord`):**
   - Populate standardized schema with validated atmospheric, geographic, and provenance attributes.

7. **Execute Meteorological Quality Control (`MeteorologicalQualityControl`):**
   - Apply range checks, internal thermodynamic consistency checks ($T_{850} > T_{700} > T_{500}$ in standard troposphere), and flag anomalies.

8. **Engineer Synoptic & Orographic Features (`MeteorologicalFeatureEngineer`):**
   - Compute $850\text{ hPa}$ wind speed and meteorological direction, vertical wind shear ($850-500\text{ hPa}$), integrated vapor transport proxy ($q_{850} \cdot V_{850}$), orographic lift index, and coastal moisture convergence.

9. **Classify Weather Regime (`RegimeInferenceService`):**
   - Run multi-label XGBoost + calibrated MLP ensemble to predict regime probabilities (ACTIVE, BREAK, MONSOON_LOW_LPS, COASTAL, OROGRAPHIC, WESTERN_DISTURBANCE, NEUTRAL_TRANSITIONAL).

10. **Execute Temporal Regime Intelligence (`TemporalRegimeService`):**
    - Project regime transitions and forecast persistence across horizons Day 1 through Day 10.

11. **Run Spatial Post-Processing ConvNet (`SpatialPostProcessingService`):**
    - Feed normalized atmospheric predictors, regime context, and SRTM digital elevation grid into the 2D Spatial ConvNet to generate bias-corrected rainfall fields.

12. **Calculate Probabilistic Rainfall Exceedances (`HeavyRainfallProbabilityService`):**
    - Compute calibrated spatial probability fields for heavy ($\ge 64.5\text{ mm}$), very heavy ($\ge 115.6\text{ mm}$), and extremely heavy ($\ge 204.5\text{ mm}$) rainfall.

13. **Calculate Uncertainty & Quantiles (`EnsembleProcessor`):**
    - Derive parametric/non-parametric quantiles ($P_{10}, P_{50}, P_{90}$) and ensemble spread.

14. **Aggregate to District Administrative Boundaries (`DistrictAggregationEngine`):**
    - Intersect 2D spatial grid with Survey of India 748 district boundary polygons using cached area-weighted grid masks.

15. **Formulate District Decision Intelligence (`DistrictDecisionEngine` / `DistrictBulletinEngine`):**
    - Synthesize quantitative risk thresholds, trigger model-derived decision categories (GREEN, YELLOW, ORANGE, RED), and generate automated operational bulletins (with non-official disclaimers).

16. **Execute Traceable Verification (`VerificationService`):**
    - Evaluate reliability, ECE, Brier score, and Fractions Skill Score (FSS) against IMD gridded observation truth.

17. **Export & Audit Provenance (`DistrictExportEngine` / `OperationalSourceRouter`):**
    - Export GeoJSON, CSV, JSON, and GeoPackage records bearing full provenance stamps (`source_id`, `model_name`, `forecast_init`, `is_fallback`, `quality_state`, `operational_state`).
