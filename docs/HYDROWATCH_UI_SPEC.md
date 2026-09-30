# HydroWatch (SIH26071) — UI/UX Forensic Specification & Design System

> **Document Status**: Complete Forensic Analysis  
> **Source Repository**: `https://github.com/Daksh-create349/Hydrowatch-SIH26071.git`  
> **Purpose**: Serves as the authoritative visual, layout, interactive, and structural UI/UX specification to enable 100% aesthetic and experiential reuse for **SIH26080** (*"Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts"* - MoES / NCMRWF).

---

## 1. Executive Visual Style & Aesthetic Philosophy

HydroWatch is built with an **institutional, high-density aerospace/meteorological command console** design aesthetic. It avoids consumer-grade rounded cartoons, synthetic gamification, emojis, and decorative placeholders. The interface communicates high-stakes operational readiness through precision typography, restrained glowing accents, dark glassmorphism surfaces, and exact mathematical data displays.

### Visual Foundations Summary
- **Color Temperature**: Deep cold obsidian dark mode (`#08090C`, `#0A0C12`, `#10141E`)
- **Accents**: High-visibility electric cyan (`#00E5FF`), deep sky blue (`#0284C7`), vivid emerald (`#10B981`), amber watch (`#F59E0B`), and warning crimson (`#EF4444`)
- **Elevation & Surface Treatment**: Subtle 1px borders (`#1E2638`), 85–95% opacity dark backdrops with backdrop blur (`backdrop-blur-md`), deep ambient drop shadows (`0 8px 32px rgba(0, 0, 0, 0.6)`)
- **Typography Pairing**: Standard sans-serif system stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto`) for UI labels paired with rigorous monospace (`ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "JetBrains Mono"`) for all numeric telemetry, coordinates, latencies, dates, and mathematical expressions.

---

## 2. Color Palette & Token System

All CSS variables and color tokens are declared in `frontend/src/app/globals.css` and reinforced via Tailwind CSS utility classes:

### Surface & Background Tokens
| Token / Variable | Hex / RGBA Code | Usage Context |
| :--- | :--- | :--- |
| `--bg-primary` | `#08090C` | Root page background, full-screen canvas backdrop |
| `--bg-secondary` | `#0F1219` | Surface cards, floating toolbars, modal backgrounds |
| `--bg-tertiary` | `#161B26` | Card headers, table rows on hover, active input containers |
| `--bg-card` | `rgba(16, 21, 32, 0.85)` | Glassmorphism floating HUD and command bar backdrops |
| `--bg-hud` | `rgba(11, 14, 22, 0.90)` | Floating Map HUD overlay (`MapHud.tsx`) |
| `--bg-modal` | `#0C0F17` / `#0C1017` | Fullscreen and dialog overlay containers |

### Border & Divider Tokens
| Token / Variable | Hex Code | Usage Context |
| :--- | :--- | :--- |
| `--border-subtle` | `#1E2638` | Default card borders, grid dividers, table row separations |
| `--border-strong` | `#2C3850` / `#2A3449` | Interactive button borders, input borders on rest state |
| `--border-accent` | `rgba(0, 229, 255, 0.40)` | Active focus outlines, selected dropdown items, active stream cards |

### Text & Content Tokens
| Token / Variable | Hex Code | Usage Context |
| :--- | :--- | :--- |
| `--text-primary` | `#F1F5F9` / `#FFFFFF` | Primary headlines, metric values, emphasized coordinates |
| `--text-secondary` | `#94A3B8` / `#CBD5E1` | Secondary labels, descriptions, timestamps, table cells |
| `--text-muted` | `#64748B` | Section sub-headers, axis labels, disclaimers, metadata keys |

### Semantic Status & Metric Tokens
| Semantic Role | Primary Color | Background Tint | Border Tint | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Cyan Accent** | `#00E5FF` | `rgba(0, 229, 255, 0.10)` | `rgba(0, 229, 255, 0.40)` | Telemetry highlight, vectors, primary brand glow |
| **Blue Primary** | `#0284C7` | `rgba(2, 132, 199, 0.15)` | `rgba(2, 132, 199, 0.35)` | Action buttons, primary progress bars |
| **Normal / Success** | `#10B981` | `rgba(16, 185, 129, 0.12)` | `rgba(16, 185, 129, 0.35)` | Low Risk, Normal threshold, Live stream online |
| **Watch / Moderate** | `#06B6D4` | `rgba(6, 182, 212, 0.12)` | `rgba(6, 182, 212, 0.35)` | Moderate Risk, Monitor status, 20–35 dBZ radar |
| **Alert / Warning** | `#F59E0B` | `rgba(245, 158, 11, 0.12)` | `rgba(245, 158, 11, 0.35)` | High Risk, Prepare status, 35–50 dBZ radar |
| **Action / Danger** | `#EF4444` | `rgba(239, 68, 68, 0.12)` | `rgba(239, 68, 68, 0.35)` | Extreme Risk, Action status, >50 dBZ radar, Errors |

---

## 3. Typography & Hierarchy

### Font Families
1. **Primary UI Sans**: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
2. **Telemetry & Code Monospace**: `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace`

### Typographic Scale & Application
- **Display 1 / Big Number**: `text-2xl` (24px) / `font-bold` / `font-mono` — Used for primary quantitative outputs (e.g. `96.9%`, `50.1 dBZ`, `16.25 km²`, `3.8 mm`).
- **Section Headers (H2/H3)**: `text-sm` (14px) / `font-bold` / `tracking-wider` / `uppercase` / `text-white` — Accompanied by 16px Lucide icons and subtitle metadata.
- **Card Subheaders & Badges**: `text-[10px]`–`text-[11px]` (10–11px) / `font-mono` / `font-semibold` / `uppercase` / `tracking-widest` — Categorical badges and stream labels.
- **Data Labels & Tooltips**: `text-xs` (12px) / `text-[#cbd5e1]` or `text-[#94a3b8]` / `font-medium`.
- **System Disclaimers & Footnotes**: `text-[9px]`–`text-[10px]` / `font-mono` / `text-[#64748b]`.

---

## 4. Spacing, Layout Grid & Structural Container

### Global Layout Structure
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STICKY HEADER: Brand · Location Badge · Analysis Cycle · Telemetry Radio  │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────────────┐
│  FLOATING COMMAND BAR: Location Preset / WGS84 Coords · Settings · Run Btn  │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────────────┐
│  3D CESIUM HERO GLOBE (540px–620px height)                                  │
│  ├─ [Top-Right] 3D Camera Controls (Center, Fit Polygons, North, Zoom, Full) │
│  ├─ [Top-Left Overlay] Floating Map HUD (Score, Level, Urgency, Area, Age)   │
│  └─ [Bottom-Left Overlay] 4-Layer Active Map Legend                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────────────┐
│  PROTOTYPE EARLY WARNING INSTRUMENT (Color Banner, Triggers, Rationale)    │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHYSICAL TELEMETRY EVIDENCE MATRIX (4-Column Responsive Grid)             │
│  [Col 1: Model 1 Rain]  [Col 2: Radar]  [Col 3: NWP 24h]  [Col 4: Inundation]│
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────────────┐
│  EXPLAINABILITY SUITE (WHY THIS ASSESSMENT)                                 │
│  ├─ Operational Feeds Gallery (Sentinel-2, ML Vectors, Radar Sweep, NWP)   │
│  ├─ Multi-Source Contribution Waterfall & 6-Column Normalized Table        │
│  └─ Model 1 Tree SHAP Feature Attribution Decomposition (Log-Odds Impact)   │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────────────┐
│  SOURCE FRESHNESS & LATENCY TIMELINE (4 Streams: Age, Latency ms, Health)  │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────────────┐
│  TECHNICAL PROVENANCE & DIAGNOSTIC AUDIT DRAWER (Versions, Config, JSON)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dimensions & Breakpoints
- **Max Width**: `max-w-7xl` (1280px) centered with `mx-auto`.
- **Horizontal Margins/Padding**: `p-3 sm:p-5` with `space-y-5` vertical rhythmic separation.
- **Card Padding**: Standard `p-3.5` (14px) to `p-4` (16px).
- **Corner Radii**:
  - Small elements / Badges: `rounded` (4px) or `rounded-sm` (2px)
  - Inputs & Action Buttons: `rounded-md` (6px)
  - Dashboard Cards & Modals: `rounded-lg` (8px) to `rounded-xl` (12px)

---

## 5. Component Style Specifications

### 5.1. Cards & Containers
- **Background**: `#0B0E16` or `#0E121A` (opaque dark carbon).
- **Border**: `1px solid #1E2638`.
- **Shadow**: `shadow-xl` / `shadow-2xl` (`0 20px 25px -5px rgba(0, 0, 0, 0.5)`).
- **Hover State**: Border shifts smoothly to `border-[#00E5FF]/40` or category color on hoverable items (`transition-colors duration-200`).

### 5.2. Badges & Status Pills
- Compact inline pills with uppercase monospace text:
  - `bg-[#1E2638] text-[#94A3B8] text-[10px] font-mono px-1.5 py-0.5 rounded tracking-widest`
  - Warning Status Pill: Dynamic background `rgba(R, G, B, 0.15)` with matching `1px solid rgba(R, G, B, 0.40)` border and vivid text color.

### 5.3. Buttons & Action Triggers
- **Primary Execution Button (`#run-analysis-button`)**:
  - `bg-[#0284C7] hover:bg-[#0369A1] active:scale-[0.98] text-white font-semibold text-xs tracking-wider px-5 py-2 rounded-md shadow-lg shadow-[#0284C7]/20`
  - Disabled State: `opacity-50 cursor-not-allowed`
  - Loading State: Embedded spinning `<Loader2 className="animate-spin" />` with label `SYNTHESIZING...`
- **Ghost / Utility Buttons**:
  - `bg-[#141824] border border-[#2A3449] hover:border-[#00E5FF]/50 text-[#94A3B8] hover:text-white p-2 rounded-md`

### 5.4. Form Inputs & Selectors
- **Date / Range / Text Inputs**:
  - `bg-[#141824] border border-[#2A3449] rounded px-2.5 py-1.5 text-white font-mono text-xs focus:border-[#00E5FF] focus:outline-none`
- **Sliders**:
  - `accent-[#0284C7] w-full bg-[#1E2638]`

### 5.5. Tables
- **Header Row**: `text-[10px] font-mono uppercase text-[#64748B] border-b border-[#1E2638] py-2 px-2`
- **Body Rows**: `divide-y divide-[#1E2638]/60 hover:bg-[#121622]/60 transition-colors`
- **Numeric Alignment**: Numeric values right-aligned with monospace font; labels left-aligned.

---

## 6. Micro-Animations, Transitions & Interactive States

### 6.1. Custom CSS Keyframes
Declared in `frontend/src/app/globals.css`:
```css
@keyframes pulse-subtle {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.animate-pulse-subtle {
  animation: pulse-subtle 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
```

### 6.2. Interactive Transitions
- **Hover Transitions**: `transition-colors duration-200 ease-in-out` on all clickable cards, buttons, and table rows.
- **Accordion Drawers**: Smooth expansion in `AuditPanel.tsx` and advanced settings drawers.
- **Modal Backdrops**: `bg-black/80 backdrop-blur-sm animate-in fade-in duration-200`.
- **Chart Hover Tooltips**: Positioned tooltips appearing dynamically over SVG chart columns on `onMouseEnter` / `onMouseLeave`.

---

## 7. Geospatial 3D Map Implementation (CesiumJS)

### 7.1. Cesium Configuration & Overrides
- **Renderer**: WebGL2 with `resolutionScale = min(window.devicePixelRatio, 2.0)` for Retina sharpness.
- **Screen Space Error**: `maximumScreenSpaceError = 1.25` for sharp satellite tile textures without blurring.
- **3D World Terrain**: `Cesium.createWorldTerrainAsync` with water mask and vertex normals.
- **Basemap**: High-resolution Esri World Imagery (`ArcGIS World_Imagery MapServer`) with zoom up to level 18.
- **Watermark Suppression**: CSS rules in `globals.css` completely hide `.cesium-viewer-bottom`, `.cesium-widget-credits`, and error panels to ensure a zero-watermark institutional console appearance.
- **Vector Overlay Clamping**: GeoJSON polygons clamped directly to 3D terrain normals (`clampToGround: true`), styled with `#00E5FF` outline (width 2.5) and `rgba(0, 180, 216, 0.42)` translucent fill.
- **Location Pin Entity**: Clamped point marker (`#00E5FF`, pixelSize 10) with bold monospace uppercase label offset by -12px.

---

## 8. Major Page Specification (`src/app/page.tsx`)

| Attribute | Forensic Documentation |
| :--- | :--- |
| **Page Name** | `HydroWatchDashboard` (`src/app/page.tsx`) |
| **Route** | `/` |
| **Purpose** | Single-page real-time geospatial intelligence, early warning, and multi-source environmental diagnostic operations center. |
| **Major Subcomponents** | `Header`, `AnalysisCommand`, `CesiumGlobe`, `MapHud`, `WarningPanel`, `EvidenceStrip`, `WhyAssessment`, `FreshnessTimeline`, `AuditPanel`, `RadarModal`, `AnalysisProgress`, `ErrorState` |
| **Data Shown** | 3D terrain & vector overlays, composite risk score, warning state, 4 physical telemetry matrix columns, 4 operational evidence cards, 6-field multi-source risk attribution table, Tree SHAP feature waterfall & narrative, latency timeline, complete raw JSON provenance. |
| **User Actions** | 1. Select preset metro or input custom WGS84 coordinates.<br>2. Configure prediction date, NWP horizon (12/24/48/72h), max cloud cover %.<br>3. Execute `RUN ANALYSIS` pipeline.<br>4. Interact with 3D Cesium camera (Zoom, Pan, Tilt, Fullscreen, Center, Fit Polygons).<br>5. Click on inundation polygons to inspect surface area, perimeter, and granule ID.<br>6. Open interactive Doppler radar modal.<br>7. Maximize satellite scene, vector mask, or NWP meteogram modal views.<br>8. Expand SHAP feature list and inspect JSON audit payload. |
| **API Calls** | `GET /health` (on initial mount)<br>`POST /api/v1/predict` (on `RUN ANALYSIS`) |
| **State Dependencies** | `selectedLocation`, `latitude`, `longitude`, `locationName`, `predictionDate`, `nwpHorizonHours`, `satelliteMaxCloud`, `isLoading`, `data` (`UnifiedPredictionResponse`), `error`, `isBackendHealthy`, `isRadarModalOpen` |
| **State Isolation Policy** | Strict synchronous `setData(null)` on location change to prevent cross-location telemetry contamination before new network payload arrives. |

---

## 9. Loading, Empty, and Error States

### 9.1. Loading State (`AnalysisProgress.tsx`)
- Appears when `isLoading === true`.
- Renders a 7-stage stepwise execution monitor (NASA POWER weather, XGBoost inference, NOAA GFS NWP, RainViewer radar, Sentinel-2 STAC & FloodUNet, Multi-source fusion, State machine warning).
- Shows live spinning loader (`Loader2 animate-spin`) on active step, green checkmark on completed steps, and clock on pending steps.

### 9.2. Empty State
- Before first execution, `WarningPanel` displays: *"Awaiting analysis execution for prototype early warning assessment."*
- `EvidenceStrip` columns display: *"Stream Pending Analysis"* / *"Radar Ingestion Standby"* / *"NWP Forecast Standby"*.
- `WhyAssessment` displays: *"Awaiting multi-source risk fusion output to generate mathematical explainability."*

### 9.3. Error State (`ErrorState.tsx`)
- Red accent card (`bg-[#120F14] border-[#EF4444]/40`) with `AlertCircle` icon.
- Displays human-readable error title, diagnostic message, expandable stack trace drawer, and `RETRY ANALYSIS` callback trigger.
