# PS26080 — Frontend Component Mapping & Migration Plan

> **Target Problem Statement**: SIH26080  
> **Title**: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts  
> **Organization**: Ministry of Earth Sciences (MoES)  
> **Department**: National Centre for Medium Range Weather Forecasting (NCMRWF)  
> **Reference Baseline**: HydroWatch (SIH26071)

---

## 1. Executive Strategy

To maintain **100% visual and experiential consistency** with the HydroWatch platform while migrating the underlying meteorological domain from *Flood Inundation Early Warning* (PS26071) to *Regime-Aware NWP Rainfall Post-Processing* (PS26080), every frontend component is mapped into one of four categories:
- **`KEEP`**: Preserved with identical layout, CSS design tokens, and structure.
- **`MODIFY`**: Preserved visually, but props, data bindings, metrics, and labels are adapted to PS26080.
- **`REPLACE`**: The underlying domain logic/geometry is replaced (e.g., flood polygon vectors $\to$ calibrated precipitation isohyets/grid cells).
- **`NEW`**: Domain-specific subcomponents added within existing containers (e.g., 4-Product comparison selector).

---

## 2. Component-by-Component Mapping Table

| Component | File Path | Category | Existing HydroWatch Domain (PS26071) | Target PS26080 Domain (MoES / NCMRWF) | Visual & Interaction Changes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`Header`** | `src/components/app-shell/Header.tsx` | **`MODIFY`** | HydroWatch v2.0 PRO / Geospatial Flood Intelligence | HydroWatch AI · NCMRWF Regime-Aware Monsoon Post-Processing Console | Preserves top bar, obsidian dark backdrop, coordinate badge, and stream counter (`4/4 STREAMS ACTIVE`). |
| **`AnalysisCommand`** | `src/components/location/AnalysisCommand.tsx` | **`MODIFY`** | Metro location presets, lat/lon inputs, cloud slider, run analysis button | Meteorological Zone presets (Western Ghats, Monsoon Core, Northeast, Coast), forecast lead time ($T+24\text{h}$ to $T+72\text{h}$), post-processing mode selector | Preserves floating command bar container, WGS84 manual inputs, calendar picker, and `RUN ANALYSIS` action button. |
| **`CesiumGlobe`** | `src/components/map/CesiumGlobe.tsx` | **`REPLACE` (Domain)** | 3D terrain globe with clamped flood inundation polygons | 3D terrain globe with precipitation isohyets, grid contours, and station verification pins | Preserves 3D Cesium camera controls, Retina resolution scale, zero-watermark styling, bounding box auto-fit, and popover inspection. |
| **`MapHud`** | `src/components/map/MapHud.tsx` | **`MODIFY`** | Composite flood risk score, warning level, flooded $\text{km}^2$, satellite acquisition time | Primary Monsoon Regime, AI Correction Delta ($\Delta\text{ mm}$), Heavy Rain Probability %, Forecast Skill Metric | Preserves floating glassmorphism card over 3D terrain, layout boxes, typography, and color badges. |
| **`WarningPanel`** | `src/components/warning/WarningPanel.tsx` | **`MODIFY`** | Flood disaster warning instrument (`NO_ALERT`, `MONITOR`, `PREPARE`, `ACTION`) | Severe Monsoon Rainfall & Forecast Reliability Outlook (`NORMAL`, `WATCH`, `HEAVY_RAINFALL`, `VERY_HEAVY_RAINFALL`, `EXTREME_RAINFALL`) | Preserves color-coded alert banner, physical trigger cards grid, validity window, and prototype disclaimer. |
| **`EvidenceStrip`** | `src/components/common/EvidenceStrip.tsx` | **`MODIFY`** | 4-column physical matrix: Model 1 Rain, Radar, NWP 24h meteogram, Inundation $\text{km}^2$ | 4-column verification matrix: <br>1. **Raw NWP Baseline**<br>2. **Monsoon Regime Dynamics**<br>3. **AI Post-Processed Forecast**<br>4. **Observation / Verification Benchmark** | Preserves 4-column card grid, linear probability bar, interactive SVG meteogram with hover tooltips, and footer metadata. |
| **`WhyAssessment`** | `src/components/explainability/WhyAssessment.tsx` | **`MODIFY`** | Operational evidence gallery, flood risk fusion waterfall, 6-column attribution table, Tree SHAP | Operational feeds gallery (Synoptic Map, Raw NWP, AI Corrected, Verification Error), 4-product forecast comparison (Raw vs QM vs Global ML vs Regime ML), Tree SHAP feature attribution | Preserves 4-card operational feeds gallery, maximized lightbox modals, waterfall stack, structured table, and expandable SHAP list. |
| **`FreshnessTimeline`** | `src/components/source-status/FreshnessTimeline.tsx` | **`MODIFY`** | Telemetry freshness for NASA POWER, NWP, Radar, Sentinel-2 | Ingestion freshness for NCMRWF/GFS NWP run, IMD Gridded Obs, Doppler Radar, and Regime Classifier | Preserves 4-card timeline grid, status badges, latency indicators, and age formatters. |
| **`AuditPanel`** | `src/components/provenance/AuditPanel.tsx` | **`MODIFY`** | Provenance for Model 1/2 versions, trigger thresholds, raw JSON viewer | Provenance for Regime Classifier version, Bias Correction Engine, Skill Metrics, and raw calibrated forecast JSON | Preserves accordion drawer, diagnostic layout, latency timing display, and one-click JSON copy. |
| **`RadarModal`** | `src/components/radar/RadarModal.tsx` | **`KEEP`** | RainViewer Doppler radar iframe, dBZ scale, Marshall-Palmer formula | Doppler Radar & Spatial Verification Lightbox | Preserves interactive modal, telemetry metric bars, dBZ color scale, and fullscreen capability. |
| **`AnalysisProgress`** | `src/components/loading/AnalysisProgress.tsx` | **`MODIFY`** | 7-stage flood prediction progress monitor | 7-stage regime-aware post-processing pipeline execution monitor | Preserves animated spinners, step-by-step progress checklist, and dark glass card. |
| **`ErrorState`** | `src/components/common/ErrorState.tsx` | **`KEEP`** | Resilient error card with retry callback and stack trace | Diagnostic error card for forecast or observation API failures | Preserves red-tinted alert card, diagnostic dropdown, and retry button. |

---

## 3. Preservation of Non-Negotiable UI/UX Assets

1. **Design Tokens (`globals.css`)**: Deep cold obsidian dark palette (`#08090C`, `#0F1219`, `#161B26`), electric cyan accents (`#00E5FF`), deep sky blue (`#0284C7`), status emerald (`#10B981`), amber (`#F59E0B`), and danger crimson (`#EF4444`).
2. **Typography Hierarchy**: Standard UI Sans headers paired with strict Monospace numerals for all meteorological metrics, probabilities, and latencies.
3. **Cesium 3D Globe**: Clamped vector layers, 1.4x terrain exaggeration, Retina high-DPI scaling, and institutional zero-watermark styling.
