# SIH26080 — PHASE 5 FORENSIC AUDIT & SCIENTIFIC DEFICIENCY REPORT

**Problem Statement:** SIH26080 — Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts  
**Organization:** Ministry of Earth Sciences (MoES) / NCMRWF  
**Audit Date:** September 30, 2026  
**Auditor:** Antigravity AI Post-Processing Validation Suite  

---

## 1. CURRENT ARCHITECTURAL STATE

The repository has completed Phases 0–4:
- **Backend (`FastAPI`):** Endpoints for spatial prediction (`/api/v1/predict`), district forecasts (`/api/v1/postprocess/districts`), model registry (`/api/v1/postprocess/models`), 4-model comparison (`/api/v1/postprocess/compare`), and prospective verification (`/api/v1/postprocess/verification`). 193 automated tests pass cleanly.
- **Frontend (`Next.js 16 + Cesium 1.145`):** 3D geospatial visualization with 6 rainfall layers, 4-method evidence strip, interactive telemetry HUD, 748-district table, Tree SHAP explainability, and verification hub.
- **Evaluation Assets:** Real prospective evaluation report in `reports/postprocessing_evaluation.json` on held-out 2024–2025 JJAS test data ($n=800$).

---

## 2. FORENSIC AUDIT FINDINGS: INCONSISTENCIES & RISKS

### Finding 1: Model Naming Inconsistency
- **Issue:** In `EvidenceStrip.tsx`, the Global ML model was tagged as `"Global XGB"` even though the underlying backend implementation uses `HistGradientBoostingRegressor` (or scikit-learn ensemble).
- **Remedy:** Rename all UI references to **"GLOBAL ML"** / **"Global ML Model"** to remain implementation-agnostic and match the problem statement.
- **Issue:** In `EvidenceStrip.tsx`, Raw NWP was tagged as `"Direct GFS"` as its primary label.
- **Remedy:** Standardize primary label to **"RAW NWP"**, with provenance (`GFS Demo Fallback` or `NCMRWF NCUM`) displayed in metadata badges.

### Finding 2: Overclaiming Language
- **Issue:** Phrases such as `"Optimal Calibration"`, `"Best: regime_aware_ml"`, and `"100% Real"` appeared in parts of `EvidenceStrip.tsx` and `WhyAssessment.tsx`.
- **Remedy:** Replace with scientifically neutral, descriptive phrasing:
  - `"Optimal Calibration"` $\rightarrow$ `"ACTIVE MODEL"` or `"SELECTED MODEL"`
  - `"★ Best Skill"` $\rightarrow$ `"Selected Model Pipeline"`
  - `"100% Real Feeds"` $\rightarrow$ `"Validated Meteorological Telemetry & Regime Feeds"`

### Finding 3: Ambiguity in Data Provenance
- **Issue:** Labels like `"NCMRWF Calibration Mode"` in `MapHud.tsx` could lead judges to assume live, direct NCMRWF NCUM feeds are connected without checking provenance.
- **Remedy:** Change to `"NCMRWF-ALIGNED POST-PROCESSING"`. Standardize a single provenance data structure that explicitly tags fallback data as `DEMO DATA · SYNTHETIC / FALLBACK MODE`.

### Finding 4: Centralized Provenance Utility Requirement
- **Issue:** Provenance extraction logic was partially repeated across `AuditPanel.tsx`, `Header.tsx`, and `CesiumGlobe.tsx`.
- **Remedy:** Create a centralized provenance component/utility in `frontend/src/lib/provenance.ts` and `frontend/src/components/provenance/ProvenanceBadge.tsx`.

### Finding 5: Visual "Why AI Corrected" Physical Storyline
- **Issue:** While Tree SHAP drivers are visible, a direct, intuitive 5-step visual narrative (*Raw NWP $\rightarrow$ Weather Regime $\rightarrow$ Atmospheric/Terrain Drivers $\rightarrow$ Learned NWP Bias $\rightarrow$ AI-Corrected Rainfall*) was needed for fast judge comprehension in under 30 seconds.
- **Remedy:** Implement the 5-step physical causality breakdown card directly in `WhyAssessment.tsx`.

### Finding 6: District Hierarchy & Spatial Units
- **Issue:** Unit consistency across 748 districts must be strictly enforced ($mm/24h$, exceedance $\%$, and uncertainty $[P_{10} - P_{90}]\text{ mm}$).
- **Remedy:** Verify all table formatting and tooltip scales.

---

## 3. AUDIT ACTION PLAN FOR PHASE 5

1. **Create Unified Provenance Helper** (`frontend/src/lib/provenance.ts`).
2. **Refine UI Naming & Neutralize Claims** in `Header.tsx`, `EvidenceStrip.tsx`, `MapHud.tsx`, `WhyAssessment.tsx`, and `AuditPanel.tsx`.
3. **Embed 5-Step "Why AI Corrected" Visual Story** in `WhyAssessment.tsx`.
4. **Generate Comprehensive Validation & Demonstration Documents:**
   - `docs/MODEL_PIPELINE_VALIDATION.md`
   - `docs/SIH_KEY_RESULTS.md`
   - `docs/SIH26080_ARCHITECTURE.md`
   - `docs/SIH_JUDGE_QA.md`
   - `docs/PHASE_5_COMPLETION_REPORT.md`
5. **Run Full Regression Suite** (`pytest` and `npm run build`).
