"""Unified end-to-end prediction schemas and contracts for PS26080 (MoES / NCMRWF)."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.common import Coordinates
from backend.app.schemas.nwp import NWPForecastSummary
from backend.app.schemas.postprocess import (
    DistrictForecast,
    HeavyRainfallProbabilities,
    PostProcessingComparison,
    VerificationResponse,
)
from backend.app.schemas.prediction import RainfallXaiSummary
from backend.app.schemas.regime import RegimeResponse
from backend.app.schemas.risk import (
    FusionMetadata,
    RiskLevel,
    SourceExplanation,
)
from backend.app.schemas.warning import WarningDecision, WarningProvenance


class UnifiedPredictionRequest(BaseModel):
    """Request payload for unified end-to-end regime-aware rainfall post-processing."""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Target latitude in decimal degrees (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Target longitude in decimal degrees (-180 to 180)")
    prediction_date: Optional[str] = Field(None, description="Target forecast date in YYYY-MM-DD format (default: today)")
    analysis_datetime: Optional[str] = Field(None, description="Optional ISO 8601 UTC analysis timestamp")
    nwp_horizon_hours: Optional[int] = Field(default=24, ge=1, le=168, description="NWP forecast window in hours (1-168)")
    nwp_source_preference: Optional[str] = Field(default="auto", description="Source preference ('ncmrwf_ncum', 'ncmrwf_neps', 'gfs_fallback', 'auto')")
    location_name: Optional[str] = Field(None, description="Optional descriptive location name")
    include_geojson_contours: Optional[bool] = Field(default=True, description="Whether to include WGS84 GeoJSON precipitation isohyet contours")
    satellite_date: Optional[str] = Field(None, description="Optional satellite observation date in YYYY-MM-DD format")
    satellite_max_cloud: Optional[float] = Field(default=30.0, ge=0.0, le=100.0, description="Maximum acceptable cloud coverage percentage")
    min_polygon_area_sq_m: Optional[float] = Field(default=100.0, ge=0.0, description="Minimum polygon area threshold in square meters")


class SourceStatusDetail(BaseModel):
    """Operational health, latency, and status for an individual meteorological data stream."""
    available: bool = Field(..., description="Whether evidence stream was successfully ingested")
    status: str = Field(..., description="'success', 'unavailable', or 'failed'")
    source: str = Field(..., description="Provider or pipeline identifier")
    latency_ms: float = Field(..., description="Subtask execution duration in milliseconds")
    timestamp: Optional[str] = Field(None, description="Data acquisition or observation timestamp")
    error: Optional[str] = Field(None, description="Sanitized error description if stream failed")
    is_operational_ncmrwf: Optional[bool] = Field(False, description="Whether stream is live NCMRWF operational vs fallback")

    @field_validator("timestamp", mode="before")
    @classmethod
    def convert_dt_to_iso(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return str(v)


class UnifiedRainfallSummary(BaseModel):
    """Summary of observational weather, heavy rainfall classification, and SHAP XAI."""
    probability: float = Field(..., ge=0.0, le=1.0, description="Predicted heavy rainfall probability [0.0, 1.0]")
    predicted: bool = Field(..., description="Binary classification (probability >= threshold)")
    threshold: float = Field(default=0.81, description="Applied operational decision threshold")
    observation_date: str = Field(..., description="Latest meteorological observation date used (D-1)")
    model_version: str = Field(default="heavy_rainfall_xgboost_v2", description="Model architecture")
    historical_records_used: int = Field(default=30, ge=30, description="Historical weather records used")
    latest_precipitation_mm: float = Field(..., ge=0.0, description="Observed precipitation on D-1 in mm/day")
    xai: Optional[RainfallXaiSummary] = Field(None, description="Explainable AI attribution decomposition")


class UnifiedNwpSummary(BaseModel):
    """Summary of Numerical Weather Prediction (NCMRWF NCUM / GFS Fallback)."""
    source: str = Field(default="NCMRWF NCUM 12km (Open-Meteo GFS Fallback)", description="NWP provider")
    model_name: str = Field(default="NCUM_12km_Regional", description="Numerical model identifier")
    forecast_summary: NWPForecastSummary = Field(..., description="Horizon aggregate meteorological statistics")
    forecast_horizon_hours: int = Field(..., gt=0, description="Forecast duration in hours")
    valid_times: List[str] = Field(default_factory=list, description="Hourly forecast valid timestamps")
    peak_hourly_precipitation_mm_hr: float = Field(..., ge=0.0, description="Peak hourly rainfall intensity (mm/hr)")
    accumulated_precipitation_mm: float = Field(..., ge=0.0, description="Total accumulated rainfall over horizon (mm)")
    max_cape_j_kg: Optional[float] = Field(None, ge=0.0, description="Peak CAPE value (J/kg)")
    hourly_precipitation: List[float] = Field(default_factory=list, description="Chronological hourly forecast precipitation rates (mm/hr)")
    is_operational_ncmrwf: bool = Field(False, description="Whether this feed is verified live NCMRWF")


class UnifiedRadarSummary(BaseModel):
    """Summary of Doppler Weather Radar observations (IMD Radar Network / RainViewer Composite)."""
    source: str = Field(default="IMD Doppler Weather Radar Network (RainViewer Composite)", description="Radar data provider")
    timestamp: Optional[str] = Field(None, description="Scan acquisition timestamp (ISO 8601 UTC)")
    max_reflectivity_dbz: float = Field(..., description="Peak observed radar reflectivity in dBZ")
    mean_reflectivity_dbz: float = Field(..., description="Mean active echo reflectivity in dBZ")
    estimated_rain_rate_mm_hr: float = Field(..., ge=0.0, description="Estimated peak rainfall rate (mm/hr)")
    coverage_percentage: float = Field(..., ge=0.0, le=100.0, description="Precipitation echo coverage percentage")
    tile_url: Optional[str] = Field(None, description="Direct HTTPS URI to radar raster tile")


class UnifiedSpatialContours(BaseModel):
    """Calibrated precipitation isohyet contours for Cesium 3D map."""
    contour_levels_mm: List[float] = Field(default_factory=lambda: [10.0, 35.0, 64.5, 115.6, 204.5], description="Isohyet threshold steps")
    geojson: Dict[str, Any] = Field(..., description="WGS84 GeoJSON FeatureCollection of calibrated precipitation isohyets")
    polygon_count: int = Field(0, description="Count of isohyet polygons")
    max_calibrated_mm: float = Field(0.0, description="Max calibrated precipitation in domain (mm)")


class UnifiedRiskSummary(BaseModel):
    """Multi-source integrated forecast confidence score and explainability."""
    score: float = Field(..., ge=0.0, le=1.0, description="Composite forecast confidence score [0.0, 1.0]")
    level: RiskLevel = Field(..., description="Categorized severity level (LOW, MODERATE, HIGH, EXTREME)")
    thresholds: Dict[str, float] = Field(..., description="Active category boundaries")
    fusion: FusionMetadata = Field(..., description="Fusion policy, weights, and source availability metadata")
    explanations: List[SourceExplanation] = Field(..., description="Explainability decomposition per component")


class UnifiedTimingDetail(BaseModel):
    """High-resolution timing breakdown across pipeline stages in milliseconds."""
    weather_model1_ms: Optional[float] = Field(0.0, ge=0.0, description="Model 1 weather observation latency (ms)")
    satellite_model2_ms: Optional[float] = Field(0.0, ge=0.0, description="Model 2 satellite processing latency (ms)")
    fusion_ms: Optional[float] = Field(0.0, ge=0.0, description="Multi-source risk fusion latency (ms)")
    nwp_ms: Optional[float] = Field(0.0, ge=0.0, description="NWP ingestion execution time (ms)")
    radar_ms: Optional[float] = Field(0.0, ge=0.0, description="Radar ingestion execution time (ms)")
    regime_classification_ms: Optional[float] = Field(0.0, ge=0.0, description="Weather regime classification time (ms)")
    post_processing_ms: Optional[float] = Field(0.0, ge=0.0, description="AI post-processing & bias calibration time (ms)")
    probability_estimation_ms: Optional[float] = Field(0.0, ge=0.0, description="Heavy rainfall probability estimation time (ms)")
    verification_ms: Optional[float] = Field(0.0, ge=0.0, description="Verification metric computation time (ms)")
    warning_ms: Optional[float] = Field(0.0, ge=0.0, description="Warning decision execution time (ms)")
    total_ms: float = Field(..., ge=0.0, description="Total end-to-end execution time (ms)")


class UnifiedInundationSummary(BaseModel):
    """Summary of Sentinel-2 multispectral imagery (backward compatibility)."""
    source: str = Field(default="Sentinel-2 L2A via Element 84 Earth Search", description="Satellite provider")
    scene: Dict[str, Any] = Field(default_factory=dict, description="Metadata of analyzed Sentinel-2 scene")
    flooded_area_sq_km: float = Field(0.0, ge=0.0, description="Estimated area in square kilometers")
    valid_area_sq_km: float = Field(0.0, ge=0.0, description="Total analyzed ground area in square kilometers")
    flooded_percentage: float = Field(0.0, ge=0.0, le=100.0, description="Percentage of valid ground area")
    polygon_count: int = Field(0, ge=0, description="Number of vector polygons detected")
    geojson: Dict[str, Any] = Field(default_factory=dict, description="WGS84 GeoJSON FeatureCollection")


class UnifiedPredictionResponse(BaseModel):
    """Complete unified PS26080 response for frontend consumption."""
    status: str = Field(default="success", description="Overall execution status")
    request: Dict[str, Any] = Field(..., description="Echo of input request parameters")
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="UTC timestamp of response generation")
    
    # Core PS26080 Intelligence
    regime: RegimeResponse = Field(..., description="Hierarchical synoptic weather regime classification")
    post_processing: PostProcessingComparison = Field(..., description="4-Product forecast comparison (Raw vs QM vs Global ML vs Regime ML)")
    probabilities: HeavyRainfallProbabilities = Field(..., description="Multi-threshold heavy rainfall probabilities (>=64.5, >=115.6, >=204.5 mm)")
    district_forecast: DistrictForecast = Field(..., description="District-level forecast, uncertainty bounds, and probabilities")
    verification: VerificationResponse = Field(..., description="Verification skill benchmark metrics comparing all 4 products")
    
    # Observations & Meteorological Feeds
    rainfall_prediction: Optional[UnifiedRainfallSummary] = Field(None, description="Observational weather and XAI feature attributions")
    nwp: Optional[UnifiedNwpSummary] = Field(None, description="Raw NWP model baseline forecast")
    radar: Optional[UnifiedRadarSummary] = Field(None, description="Doppler radar telemetry and nowcast")
    contours: Optional[UnifiedSpatialContours] = Field(None, description="Calibrated precipitation isohyets for Cesium 3D Globe")
    inundation: Optional[UnifiedInundationSummary] = Field(None, description="Optional baseline reference")
    
    # Severe Weather Alert / Outlook & Diagnostics
    risk: UnifiedRiskSummary = Field(..., description="Forecast severity index and attribution weights")
    warning: WarningDecision = Field(..., description="Severe rainfall outlook and physical trigger evaluation")
    source_status: Dict[str, SourceStatusDetail] = Field(..., description="Telemetry source health and NCMRWF attribution")
    timing: UnifiedTimingDetail = Field(..., description="Execution latency breakdown in milliseconds")
    provenance: WarningProvenance = Field(..., description="Model versioning and threshold configuration audit trail")

