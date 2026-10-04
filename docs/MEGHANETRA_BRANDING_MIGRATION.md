# MEGHANETRA — Complete Branding Migration

## Previous Project Branding
HydroWatch AI

## New Project Branding
MEGHANETRA

## Official Title
MEGHANETRA — Regime-Aware AI for Probabilistic Monsoon Rainfall Intelligence

## Tagline
Seeing the Regime Behind the Rain

## Short Description
MEGHANETRA is a regime-aware AI platform for probabilistic monsoon rainfall intelligence, NWP post-processing, spatial verification, and district-level decision support.

## SIH Problem Statement
PS26080 — Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

---

## Migration Summary by Component

### Frontend
- **Header:** Rebranded visible badge from `HydroWatch AI` to `MEGHANETRA` while maintaining `MoES · NCMRWF` institutional tags, `Demo Mode` indicator, and `PS26080` subtitle.
- **Layout & Metadata:** Updated HTML `<title>` to `MEGHANETRA | Regime-Aware Monsoon Rainfall Intelligence`, added OpenGraph titles, and updated application descriptions.
- **Page Component & Logging:** Renamed main dashboard component to `MeghanetraDashboard` and updated browser console prefixes from `[HydroWatch]` to `[MEGHANETRA]`.
- **Modals & HUD:** Replaced references in NWP operational disclaimer (`NwpModal.tsx`), Case Studies (`HistoricalCaseStudies.tsx`), and Cesium 3D Globe (`CesiumGlobe.tsx`).
- **Error Handling & Types:** Standardized network error fallbacks in `src/lib/api.ts` and header comments in `src/lib/types.ts`.

### Backend
- **Operational Endpoints:** Updated data catalog and NWP endpoint disclaimers in `backend/app/api/v1/endpoints/data.py` to identify the service as MEGHANETRA.
- **API Contracts:** Preserved all functional REST endpoints (`/api/v1/predict`, `/api/v1/regime`, `/api/v1/districts`, `/api/v1/verification/*`, `/api/v1/operational/*`, `/health`) with zero breaking changes.

### Documentation
- **Root README:** Updated main title to `MEGHANETRA`, added official tagline and description, and maintained all four-model benchmark verification tables.
- **Reports & Audits:** Updated Phase 4, Phase 5, and final forensic audit reports to reflect MEGHANETRA (PS26080) while preserving historical reference notes regarding baseline adaptation.
- **Pitch & Presentation Decks:** Updated `ONE_MINUTE_PITCH.md`, `SIH_DEMO_FLOW.md`, and `SIH_FINAL_PRESENTATION.md` to feature MEGHANETRA.

### Configuration & Deployment
- **Docker & Compose:** Updated container names in `docker-compose.yml` to `meghanetra-backend` and `meghanetra-frontend`.
- **Environment Templates:** Updated `APP_NAME=MEGHANETRA_PS26080` in `.env.example`.

### Scientific & Mathematical Logic
- **Algorithms Unchanged:** Raw NWP, Empirical Quantile Mapping (EQM), Global ML, and Regime-Aware AI Mixture of Experts remain 100% untouched.
- **Metrics & Benchmarks:** Verification datasets (2024–2025 JJAS held-out evaluation, $n=800$), RMSE, MAE, Bias, POD, FAR, CSI, ETS, and FSS scores are strictly preserved.
- **Provenance & Warning Governance:** `DEMO DATA · FALLBACK MODE` indicators, IMD warning governance (`is_official_imd_warning = false`), and NCMRWF institutional gateway disclaimers remain fully intact.
