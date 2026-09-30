# HydroWatch (SIH26071) — Current Architecture & Forensic Flow Map

> **Document Status**: Complete Forensic Architecture Specification  
> **Source Repository**: `backend/` and `frontend/`  
> **Scope**: End-to-end data flow, API architecture, ML topologies, caching, and external provider integration.

---

## 1. End-to-End System Architecture Map

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   PRESENTATION TIER                                    │
│       Next.js 16.3.5 (App Router, Turbopack) + React 19.2.8 Client ('use client')      │
│       CesiumJS 1.145 (3D WebGL) │ Vanilla CSS Design Tokens │ Lucide Icons             │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP POST /api/v1/predict
                                            │ Native fetch + TypeScript Interfaces (types.ts)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   API GATEWAY TIER                                     │
│       FastAPI 0.115+ │ Uvicorn (Port 8001) │ Pydantic v2.8 Validation Schemas          │
│       Centralized CORS Middleware │ Global Exception Handlers (errors.py)              │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  Routing Architecture (api/v1/router.py):                                              │
│  ├── GET  /health                      -> Direct health status                         │
│  ├── GET  /api/v1/models/health        -> ML model memory & checkpoint diagnostics     │
│  ├── POST /api/v1/predict              -> Unified multi-source prediction orchestrator │
│  ├── POST /api/v1/predict/rainfall     -> Model 1 standalone heavy rain inference      │
│  ├── POST /api/v1/predict/inundation   -> Model 2 standalone FloodUNet segmentation   │
│  ├── POST /api/v1/predict/risk         -> Multi-source risk fusion engine              │
│  ├── POST /api/v1/predict/warning      -> Deterministic warning decision state machine │
│  ├── GET  /api/v1/data/nwp             -> NOAA GFS 0.25° point forecast meteogram      │
│  └── GET  /api/v1/data/radar           -> Doppler radar composite & Z-R rain rate      │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             BACKEND SERVICE ORCHESTRATION                              │
│       UnifiedPredictionService (Concurrent In-Process Execution via asyncio.gather)    │
└───────┬──────────────────────────┬─────────────────────────┬───────────────────┬───────┘
        │                          │                         │                   │
        ▼                          ▼                         ▼                   ▼
┌───────────────────────┐ ┌──────────────────┐ ┌───────────────────────┐ ┌───────────────┐
│ WeatherObservationSvc │ │   NWPService     │ │    RadarService       │ │ SatelliteSvc  │
│ (FeatureBuilder + XAI)│ │ (GFS Time Series)│ │ (Marshall-Palmer Z-R) │ │ (RasterProc)  │
└───────┬───────────────┘ └────────┬─────────┘ └──────────┬────────────┘ └───────┬───────┘
        │                          │                      │                      │
        ▼                          │                      │                      ▼
┌───────────────────────────────┐  │                      │  ┌───────────────────────────┐
│         ML INFERENCE          │  │                      │  │       ML INFERENCE        │
│ Model 1: XGBoost v2           │  │                      │  │ Model 2: PyTorch FloodUNet│
│ 37 Atmospheric Features       │  │                      │  │ 6-Band Multispectral COGs │
│ Tree SHAP Log-Odds Margins    │  │                      │  │ 512x512 Windowing + GDAL  │
│ Threshold: 0.81 (Acc: 92.6%)  │  │                      │  │ Threshold: 0.5 (Acc:94.2%)│
└───────┬───────────────────────┘  │                      │  └───────────┬───────────────┘
        │                          │                      │              │
        └──────────────────────────┼──────────────────────┴──────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DETERMINISTIC MULTI-SOURCE RISK FUSION                          │
│   RiskFusionService: Composite Score = 0.35·P_rain + 0.25·S_nwp + 0.20·S_radar + 0.20·S_sat│
│   Dynamic Renormalization Policy: >=2 available streams required (or 422 degradation)  │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        WARNING DECISION STATE MACHINE (WarningService)                 │
│   States: NO_ALERT (<0.30) │ MONITOR (0.30-0.60) │ PREPARE (0.60-0.80) │ ACTION (>=0.80)│
│   Physical Trigger Rule Verification │ Validity Window Calculation │ Disclaimer Bar    │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             EXTERNAL DATA PROVIDERS & CACHE                            │
│  ├── NASA POWER Daily Point API (Meteorological reanalysis for 37 features)           │
│  ├── Open-Meteo GFS API (NOAA GFS 0.25° Seamless hourly precipitation & CAPE)         │
│  ├── RainViewer Radar Network API (Global Doppler radar composite sweeps & tiles)     │
│  ├── AWS Element 84 Earth Search STAC API (Sentinel-2 L2A Cloud Optimized GeoTIFFs)   │
│  └── Local File Cache (`data_cache/` + in-memory `@lru_cache` & singleton instances)  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tier-by-Tier Forensic Breakdown

### 2.1. Presentation Tier (Frontend)
- **Framework**: Next.js 16.3.5 with Turbopack, App Router (`src/app`).
- **Core Library**: React 19.2.8 (`'use client'` pattern on all interactive pages).
- **Geospatial Engine**: CesiumJS 1.145.0 dynamically imported with SSR disabled (`dynamic(() => import(...), { ssr: false })`) to eliminate Node WebGL/canvas SSR initialization errors.
- **State Architecture**:
  - Centralized single-source-of-truth state in `src/app/page.tsx`.
  - Strict synchronous `setData(null)` on location or coordinate changes to prevent stale data contamination.
  - AbortController cancellation on rapid parameter updates.
- **API Client**: Strongly typed wrapper in `src/lib/api.ts` communicating with `POST /api/v1/predict` and `GET /health`.

---

### 2.2. API Gateway & Middleware Tier
- **Framework**: FastAPI 0.115.0+ running under Uvicorn 0.30+ ASGI server.
- **Configuration Management**: Pydantic `BaseSettings` (`backend/app/core/config.py`) loading from `.env`.
- **Validation**: Strict Pydantic v2 schemas across all requests, responses, and intermediate data transfers.
- **CORS Configuration**: Configurable origins supporting standard local development ports (`3000`, `5173`).
- **Error Handling**: Centralized exception handler mapping domain errors (`WeatherObservationValidationError`, `ModelNotLoadedError`, `MissingSourceDegradationError`) to standard RFC 7807 JSON responses.

---

### 2.3. Machine Learning Components

#### Model 1: Heavy Rainfall Classifier (XGBoost v2)
- **Artifacts**: `models/best_heavy_rain_xgboost_v2.json` and `.pkl`.
- **Architecture**: Gradient Boosted Decision Tree (XGBoost).
- **Input Dimension**: 37 features extracted strictly from antecedent dates ($D-1$ backward) to prevent lookahead leakage.
- **Decision Threshold**: $\tau = 0.81$ (optimized for high recall disaster prevention).
- **Explainability**: Integrated Tree SHAP (`xgb.Booster.predict(..., pred_contribs=True)`) computing marginal log-odds feature attributions with directional impact (`increases_risk` / `decreases_risk`).

#### Model 2: Surface Water Segmentation (PyTorch FloodUNet)
- **Artifacts**: `models/best_model.pth` (7,763,905 parameters), `models/unet_model_config.json`, `models/best_model_metadata.json`.
- **Architecture**: Custom 4-level deep convolutional U-Net with skip connections.
- **Input Channels (6 bands)**: $B_2$ (Blue), $B_3$ (Green), $B_4$ (Red), $B_8$ (NIR), $B_{11}$ (SWIR-1), $B_{12}$ (SWIR-2).
- **Preprocessing**: Reflectance normalization ($\div 10000.0$), non-finite replacement with 0.0, clipping to $[0.0, 1.0]$.
- **Inference Strategy**: $512 \times 512$ sliding window inference with edge blending and seamless mosaic reconstruction.
- **Vectorization**: Real-time raster-to-vector polygon extraction via GDAL / Rasterio (`rasterio.features.shapes`), reprojected to WGS84 (`EPSG:4326`) and serialized into RFC 7946 GeoJSON.

---

### 2.4. Data Ingestion & Integration Tier

| Stream | Remote Source | Client Service | Ingestion Protocol |
| :--- | :--- | :--- | :--- |
| **Meteorological History** | NASA POWER Daily Point API | `NasaPowerClient` / `WeatherObservationService` | HTTP REST querying 30+ days historical atmospheric time series |
| **NWP Forecast** | Open-Meteo NOAA GFS 0.25° | `NwpClient` / `NWPService` | HTTP REST querying hourly precipitation, temperature, wind, CAPE |
| **Doppler Radar** | RainViewer Radar Network | `RadarClient` / `RadarService` | HTTP REST querying global composite reflectivity metadata & tiles |
| **Multispectral Satellite** | AWS Earth Search STAC | `SentinelClient` / `SatelliteImageryService` | STAC API search + Cloud Optimized GeoTIFF (COG) windowed HTTP range reads |

---

### 2.5. Multi-Source Risk Fusion & Early Warning State Machine
- **Fusion Formulation**:
  $$R = w_{\text{rain}} \cdot S_{\text{rain}} + w_{\text{nwp}} \cdot S_{\text{nwp}} + w_{\text{radar}} \cdot S_{\text{radar}} + w_{\text{sat}} \cdot S_{\text{sat}}$$
- **Missing Stream Degradation Policy**:
  - 4 Available Streams: Standard weights ($0.35, 0.25, 0.20, 0.20$).
  - 2 or 3 Available Streams: Dynamic weight renormalization to sum to 1.0; policy marked `PARTIAL_EVIDENCE`.
  - $< 2$ Available Streams: Raises `MissingSourceDegradationError` (HTTP 422).
- **Warning State Mapping**:
  - `NO_ALERT`: $R < 0.30$
  - `MONITOR`: $0.30 \le R < 0.60$
  - `PREPARE`: $0.60 \le R < 0.80$
  - `ACTION`: $R \ge 0.80$
