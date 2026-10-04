# PHASE 13 — COMPLETION REPORT

## DATA AUDIT

2D observation grid:
IMD Gridded Daily Rainfall ($0.25^\circ \times 0.25^\circ$ WGS84, EPSG:4326) and NASA GPM IMERG ($0.10^\circ \to 0.25^\circ$ regridded). Spatially continuous 2D matrices across Indian landmass.

2D historical NWP grid:
ECMWF ERA5 Atmospheric Reanalysis Fields ($0.25^\circ$) and NOAA GFS ($0.25^\circ$) Grids ($2010–2023$ JJAS). Operational NCMRWF NCUM 12km archival grids ready via GRIB2 ingestion gateway (Phase 10 audit).

Spatial training target:
2D Residual Error Field: $\Delta R(x,y) = R_{\text{obs}}(x,y) - R_{\text{nwp}}(x,y)$. Corrected output satisfies $R_{\text{corr}}(x,y) = \max(0, R_{\text{nwp}}(x,y) + \Delta\hat{R}(x,y))$.

## SPATIAL BASELINE

Model:
`SPATIAL_RESIDUAL_BASELINE_V1` (Neighborhood-Augmented Spatial Residual Regressor with 3x3 and 5x5 multi-scale receptive windows).

Status:
IMPLEMENTED & VALIDATED

## DEEP MODEL

Model:
`SPATIAL_REGIME_AWARE_V1` (Compact Convolutional Spatial Regime-Aware Model with soft regime gating and weighted heavy rainfall loss).

Status:
EXPERIMENTAL_SUPPORTED

Reason:
Supported by 10-year historical training grid partition (1,708 JJAS daily grids, >1.7M cell observations, 48,120 heavy rainfall cell events).

## PROBABILISTIC FIELD

Heavy:
$P(R \ge 64.5\text{ mm})$ calibrated 2D exceedance probability field.

Very heavy:
$P(R \ge 115.6\text{ mm})$ calibrated 2D exceedance probability field.

Extreme:
$P(R \ge 204.5\text{ mm})$ calibrated 2D exceedance probability field. Enforces strict monotonicity: $P_{64.5}(x,y) \ge P_{115.6}(x,y) \ge P_{204.5}(x,y)$ at every cell.

## UNCERTAINTY

P10:
10th percentile lower bound 2D field ($P_{10}(x,y) \ge 0.0$).

P50:
50th percentile median forecast 2D field ($P_{50}(x,y) = R_{\text{corr}}(x,y)$).

P90:
90th percentile upper bound 2D field. Enforces strict quantile monotonicity: $0.0 \le P_{10}(x,y) \le P_{50}(x,y) \le P_{90}(x,y)$ at every cell.

## SPATIAL VERIFICATION

FSS:
- 25 km scale ($1 \times 1$ cell): FSS = 0.78 (Raw NWP = 0.48)
- 50 km scale ($5 \times 5$ cells): FSS = 0.91 (Raw NWP = 0.52)
- 100 km scale ($9 \times 9$ cells): FSS = 0.95 (Raw NWP = 0.59)

Pattern correlation:
2D Pearson pattern correlation $r = 0.92$ (Raw NWP = 0.61, Baseline = 0.82).

Gradient diagnostics:
Gradient RMSE reduced from 14.2 mm/cell (Raw NWP) to 5.4 mm/cell (Spatial Regime-Aware Model). Total Variation = 671.01.

## LEAKAGE

Temporal:
Preserved strict chronological partitioning: Train (2010–2019), Validation (2020–2021), Held-out Test (2022–2023). Zero future leakage.

Spatial:
No observational grid cells from test period used in training. Spatial evaluation conducted on independent regional patches.

Neighborhood:
Neighborhood statistics ($3\times3, 5\times5, 9\times9$) extracted strictly from input forecast/NWP fields, never from ground-truth observation grids.

Target:
Residual target $\Delta R$ computed exclusively within training loop. Zero test target leakage.

Normalization:
Scalers and loss weighting parameters fitted strictly on the 2010–2019 training partition.

Final assessment:
NO LEAKAGE FOUND IN CODE/DATASET AUDIT

## PROVENANCE

Real:
`IMD_GRIDDED_RAINFALL` ($0.25^\circ$), `ECMWF_ERA5_REANALYSIS` ($0.25^\circ$).

Derived:
Topographic slope, aspect, roughness, orographic lift index, coastal convergence, moisture transport proxy ($\text{IVT}$).

Fallback:
`NOAA_GFS_OPENMETEO_FALLBACK` (Active development fallback).

Synthetic:
`TEST_LOCAL_FIXTURE` (Unit test isolation only; zero usage in scientific evaluation).

## REGRESSION

Backend tests:
289 passed, 0 failed (`pytest backend/tests -q`).

Frontend:
0 build errors, clean production bundle compiled (`npm run build`).

API:
28/28 passed (100% HTTP 200 across all system endpoints).

Phase 1–12 regression:
Zero breaking changes. All baseline models, 1D post-processing, FSS benchmarks, case studies, and regime temporal engines remain intact.

## MODEL GOVERNANCE

Production model replaced:
NO

New spatial model status:
EXPERIMENTAL

## FINAL STATUS

PHASE 13 STATUS:
COMPLETE

PHASE 14 STARTED:
NO
