# HydroWatch (SIH26071) — Frontend Component Inventory

> **Document Status**: Complete Forensic Component Inventory  
> **Source Repository**: `frontend/src/components`  
> **Target Problem**: **SIH26080** (*"Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts"* - MoES / NCMRWF)

---

## Component Matrix Overview

| Component | File Path | Current HydroWatch Purpose | Reusability for SIH26080 | Modification Required for Target Domain |
| :--- | :--- | :--- | :--- | :--- |
| **`Header`** | `src/components/app-shell/Header.tsx` | Sticky top navigation, branding, location coordinate badge, stream health count | **Directly Reusable** (100% Structural Reuse) | Update brand title to SIH26080, subtitle to MoES/NCMRWF Regime-Aware Post-Processing, telemetry count to active NWP/Obs streams. |
| **`AnalysisCommand`** | `src/components/location/AnalysisCommand.tsx` | Floating command toolbar, preset location selector, custom WGS84 coordinate input, parameter settings drawer, run trigger | **Directly Reusable** (High Value) | Adapt presets to key meteorological verification domains (e.g. Western Ghats, Central India Monsoon Core Zone, Northeast, Northwest), replace cloud cover slider with regime model selection (e.g. Synoptic Circulation Regime, Active/Break Monsoon Phase, Lead Day $T+1 \dots T+5$). |
| **`CesiumGlobe`** | `src/components/map/CesiumGlobe.tsx` | High-DPI 3D WebGL digital twin, 3D world terrain, Esri satellite imagery, GeoJSON vector overlay, camera controllers | **Directly Reusable** (High Value) | Swap inundation polygon rendering with gridded/contour forecast overlays (Raw NWP precipitation vs AI Post-Processed calibrated precipitation grid vs IMD Ground Truth observations). |
| **`MapHud`** | `src/components/map/MapHud.tsx` | Floating map HUD over 3D terrain displaying composite risk, warning pill, inundation extent, and satellite baseline timestamp | **Directly Reusable** (High Value) | Transform metrics to show: Identified Monsoon Synoptic Regime (e.g. *Active Monsoon / Monsoon Low*), Mean Forecast Bias Correction ($\Delta$ mm), Skill Improvement Score (ETS / CSI / RMSE reduction). |
| **`WarningPanel`** | `src/components/warning/WarningPanel.tsx` | Prototype assessment early warning instrument with trigger criteria list, physical trigger evaluation cards, and validity window | **Directly Reusable** (High Value) | Transform into **"Regime Diagnosis & Forecast Reliability Alert"**: shows active monsoon regime triggers, extreme rainfall warning discrepancy between Raw NWP and AI-Calibrated Forecast, and reliability advisory. |
| **`EvidenceStrip`** | `src/components/common/EvidenceStrip.tsx` | 4-column physical telemetry matrix: Station Rain, Doppler Radar, NWP 24h meteogram, Sentinel-2 Inundation | **Directly Reusable** (High Value) | Re-align columns to 4 post-processing verification pillars: <br>1. **Raw NWP Model Forecast** (NCUM/NEPS/GFS precipitation accumulation & peak rate)<br>2. **Active Monsoon Regime Context** (Low-Level Jet index, Monsoon Trough axis position, OLR anomaly)<br>3. **AI Post-Processed Calibrated Forecast** (Regime-conditioned bias corrected grid & confidence interval)<br>4. **Ground Truth / Observation Reference** (IMD Gridded 0.25° / Radar QPE / Automatic Weather Station). |
| **`WhyAssessment`** | `src/components/explainability/WhyAssessment.tsx` | Multi-source evidence gallery, contribution waterfall stack, 6-column risk attribution table, Tree SHAP feature decomposition | **Directly Reusable** (Exceptional Value) | 1. **Operational Gallery**: Raw NWP Grid vs AI Corrected Grid vs IMD Observation vs Synoptic Regime Map.<br>2. **Attribution Table**: Bias correction decomposition across atmospheric predictors (Z500, U850, V850, Specific Humidity, Orography).<br>3. **XAI SHAP**: Feature importance showing why the AI adjusted the NWP rainfall upward/downward (e.g. orographic lift underestimation, convective scheme over-prediction). |
| **`FreshnessTimeline`** | `src/components/source-status/FreshnessTimeline.tsx` | Currency, age, latency, and status badges across all ingested data streams | **Directly Reusable** (100% Structural Reuse) | Update stream labels to: NCMRWF NCUM/NEPS Forecast Run (00Z/12Z), IMD Gridded Observations, Satellite QPE (GPM IMERG), Regime Classifier Engine. |
| **`AuditPanel`** | `src/components/provenance/AuditPanel.tsx` | Technical provenance accordion, model versions, configured thresholds, latency timing breakdown, raw JSON viewer & copy | **Directly Reusable** (100% Structural Reuse) | Update model provenance metadata to display AI Post-Processing Model Version (e.g. *Regime-Aware UNet/ResNet v2.1*), NWP Baseline Version, Skill Metrics, and Full Calibration JSON payload. |
| **`RadarModal`** | `src/components/radar/RadarModal.tsx` | Dedicated modal lightbox with live RainViewer interactive radar iframe, dBZ scale, Marshall-Palmer equation, telemetry bars | **Directly Reusable / Expandable** | Reuse modal architecture as a **"Spatial Verification & Grid Comparison Lightbox"** allowing side-by-side or slider comparison between Raw NWP, AI Corrected, and Radar/IMD Observed precipitation. |
| **`AnalysisProgress`** | `src/components/loading/AnalysisProgress.tsx` | Stepwise 7-stage execution monitor with active spinners and completed checks | **Directly Reusable** | Update stage descriptions to match post-processing pipeline: Ingesting NWP Grid $\to$ Extracting Atmospheric Predictors $\to$ Classifying Synoptic Regime $\to$ Applying AI Bias Correction $\to$ Computing Spatial Skill Metrics $\to$ Generating Reliability Assessment. |
| **`ErrorState`** | `src/components/common/ErrorState.tsx` | Resilient error card with retry callback and expandable diagnostics drawer | **Directly Reusable** (100% Structural Reuse) | No architectural changes required; handles NWP or observation API ingestion exceptions. |

---

## Detailed Component Specifications

### 1. `Header` (`src/components/app-shell/Header.tsx`)
- **Props**:
  - `locationName: string`
  - `latitude: number`
  - `longitude: number`
  - `generatedAt?: string | null`
  - `isBackendHealthy: boolean`
  - `streamsOnlineCount?: number`
- **State**: None (Stateless Presentational Component)
- **Dependencies**: `lucide-react` (`Activity`, `Globe`, `Radio`), `@/lib/formatters`
- **Reuse Rating**: **100% Direct Reuse**

---

### 2. `AnalysisCommand` (`src/components/location/AnalysisCommand.tsx`)
- **Props**:
  - `selectedLocation: PresetLocation | null`
  - `onSelectPreset: (preset: PresetLocation) => void`
  - `onSelectCustom: (lat: number, lon: number, name: string) => void`
  - `onRunAnalysis: () => void`
  - `isLoading: boolean`
  - `predictionDate: string`
  - `onChangeDate: (date: string) => void`
  - `nwpHorizonHours: number`
  - `onChangeNwpHorizon: (hours: number) => void`
  - `satelliteMaxCloud: number`
  - `onChangeSatelliteMaxCloud: (val: number) => void`
- **State**:
  - `isDropdownOpen: boolean`
  - `isCustomMode: boolean`
  - `customLat: string`, `customLon: string`, `customName: string`
  - `customError: string | null`
  - `showSettings: boolean`
- **Dependencies**: `lucide-react` (`Play`, `Settings2`, `MapPin`, `ChevronDown`, `Check`, `AlertCircle`, `Loader2`), `@/lib/constants`, `@/lib/formatters`, `@/lib/types`
- **Modification for SIH26080**:
  - Update presets to meteorological river basins / monsoon meteorological subdivisions (e.g., Konkan & Goa, Coastal Karnataka, Vidarbha, Gangetic West Bengal, Assam).
  - Add forecast model selector (NCUM 12km, NEPS 4km, GFS 0.25°) and lead-time selector (Day 1 to Day 7).

---

### 3. `CesiumGlobe` (`src/components/map/CesiumGlobe.tsx`)
- **Props**:
  - `latitude: number`
  - `longitude: number`
  - `locationName: string`
  - `geojson?: GeoJSONFeatureCollection | null`
  - `polygonCount?: number`
- **State**:
  - `isInitializing: boolean`
  - `terrainLoaded: boolean`
  - `satelliteLoaded: boolean`
  - `errorMessage: string | null`
  - `isFullscreen: boolean`
  - `selectedPolygonMeta: Record<string, unknown> | null`
- **Dependencies**: `cesium` (dynamic client-side import), `lucide-react` (`Compass`, `Maximize2`, `Minimize2`, `Layers`, `ZoomIn`, `ZoomOut`, `Crosshair`, `MapPin`, `AlertTriangle`), `@/lib/formatters`
- **Modification for SIH26080**:
  - Support raster imagery tiles / GeoJSON contour polygons representing calibrated rainfall isohyets ($<10\text{ mm}$, $10-50\text{ mm}$, $50-100\text{ mm}$, $>100\text{ mm}$ heavy downpour zones) and regime synoptic wind vectors.

---

### 4. `MapHud` (`src/components/map/MapHud.tsx`)
- **Props**:
  - `locationName: string`
  - `latitude: number`, `longitude: number`
  - `riskScore?: number | null`
  - `riskLevel?: RiskLevel | null`
  - `warningStatus?: WarningStatus | null`
  - `warningUrgency?: WarningUrgency | null`
  - `floodedAreaKm2?: number | null`
  - `floodedPercentage?: number | null`
  - `polygonCount?: number | null`
  - `satelliteAcquisitionTime?: string | null`
- **State**: None (Stateless Presentational Component)
- **Dependencies**: `lucide-react` (`Shield`, `Droplets`, `Satellite`, `AlertCircle`), `@/lib/constants`, `@/lib/formatters`, `@/lib/types`
- **Modification for SIH26080**:
  - Transform display boxes to:
    1. **Synoptic Monsoon Regime** (e.g., *Active Offshore Trough*, *Monsoon Depression*)
    2. **AI Correction Delta** (e.g., *+34.2 mm Post-Processed vs Raw NWP*)
    3. **Reliability Index / Verification Skill** (e.g., *Critical Success Index: 0.88*)

---

### 5. `WarningPanel` (`src/components/warning/WarningPanel.tsx`)
- **Props**:
  - `warning?: WarningDecision | null`
- **State**: None
- **Dependencies**: `lucide-react` (`AlertTriangle`, `Clock`, `ShieldCheck`, `ChevronRight`, `Info`), `@/lib/constants`, `@/lib/formatters`, `@/lib/types`
- **Modification for SIH26080**:
  - Transform into **"Forecast Reliability & Extreme Rainfall Discrepancy Alert"**:
    - Highlights when Raw NWP model significantly misses extreme convective localized bursts (e.g. *Raw NWP predicts 12 mm/h, AI regime-correction elevates to 68 mm/h due to strong Low-Level Jet & orographic moisture convergence*).
    - Lists active physical triggers (Low-Level Jet speed > 30 kts, Offshore trough gradient, CAPE > 2500 J/kg, Antecedent soil wetness).

---

### 6. `EvidenceStrip` (`src/components/common/EvidenceStrip.tsx`)
- **Props**:
  - `rainfall?: UnifiedRainfallSummary | null`
  - `radar?: UnifiedRadarSummary | null`
  - `nwp?: UnifiedNwpSummary | null`
  - `inundation?: UnifiedInundationSummary | null`
  - `onOpenRadarModal: () => void`
- **State**:
  - `hoveredNwpIndex: number | null`
- **Dependencies**: `lucide-react` (`CloudRain`, `Radio`, `TrendingUp`, `Droplets`, `ExternalLink`, `Satellite`, `Calendar`), `@/lib/formatters`, `@/lib/types`
- **Modification for SIH26080**:
  - Card 1: **Raw NWP Baseline Forecast** (Raw 24h accumulation, peak intensity)
  - Card 2: **Large-Scale Monsoon Regime Index** (Active/Break spell, LLJ speed, Monsoon Trough position)
  - Card 3: **AI Post-Processed Calibrated Forecast** (Calibrated 24h meteogram with uncertainty bounds)
  - Card 4: **Observation / Verification Benchmark** (IMD Gridded / Radar QPE reference)

---

### 7. `WhyAssessment` (`src/components/explainability/WhyAssessment.tsx`)
- **Props**:
  - `risk?: UnifiedRiskSummary | null`
  - `xai?: RainfallXaiSummary | null`
  - `inundation?: UnifiedInundationSummary | null`
  - `radar?: UnifiedRadarSummary | null`
  - `nwp?: UnifiedNwpSummary | null`
  - `lat?: number`, `lon?: number`
  - `onOpenRadarModal?: () => void`
- **State**:
  - `showAllShap: boolean`
  - `imgFallback: boolean`
  - `maximizedModal: 'satellite' | 'vector' | 'nwp' | null`
- **Dependencies**: `lucide-react` (`BrainCircuit`, `BarChart3`, `Layers`, `Info`, `ChevronDown`, `ChevronUp`, `ArrowUpRight`, `ArrowDownRight`, `Radio`, `ExternalLink`, `Maximize2`, `X`), `@/lib/formatters`, `@/lib/types`
- **Modification for SIH26080**:
  - Operational Gallery: Shows (1) Synoptic Circulation Map (850 hPa wind & geopotential height), (2) Raw NWP Precipitation Field, (3) AI Bias Corrected Field, (4) Verification Error/Skill Field.
  - Explainability Table: Shows mathematical correction weights applied to dynamical model components.
  - Tree SHAP / Feature Attribution: Displays atmospheric feature drivers (Zonal wind U850, Meridional wind V850, Specific humidity, Orographic slope, Total Precipitable Water).

---

### 8. `AuditPanel` (`src/components/provenance/AuditPanel.tsx`)
- **Props**:
  - `data?: UnifiedPredictionResponse | null`
- **State**:
  - `isOpen: boolean`
  - `copied: boolean`
- **Dependencies**: `lucide-react` (`Terminal`, `ChevronDown`, `ChevronUp`, `Copy`, `Check`, `FileJson`, `ShieldCheck`), `@/lib/types`
- **Reuse Rating**: **100% Direct Structural Reuse**

---

### 9. `FreshnessTimeline` (`src/components/source-status/FreshnessTimeline.tsx`)
- **Props**:
  - `sourceStatus?: Record<string, SourceStatusDetail> | null`
  - `timing?: UnifiedTimingDetail | null`
- **State**: None
- **Dependencies**: `lucide-react` (`Clock`, `CheckCircle2`, `XCircle`, `AlertCircle`), `@/lib/formatters`, `@/lib/types`
- **Reuse Rating**: **100% Direct Structural Reuse**
