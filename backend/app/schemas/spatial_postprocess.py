"""
Pydantic Schemas for Spatial Regime-Aware Rainfall Post-Processing (Phase 13).
Supports 2D spatial grid definitions, multi-channel feature tensors, probabilistic heavy rainfall fields,
spatial quantiles (P10/P50/P90), multi-scale Fractions Skill Score (FSS), and forensic spatial provenance.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class SpatialGridDefinition(BaseModel):
    """Canonical 2D geographic grid representation (EPSG:4326 WGS84)."""
    grid_name: str = Field("IMD_ERA5_0.25deg_Canonical", description="Identifier for grid layout")
    resolution_deg: float = Field(0.25, description="Spatial resolution in degrees (0.25° ~ 27.75 km)")
    crs: str = Field("EPSG:4326", description="Coordinate reference system")
    latitudes: List[float] = Field(..., description="1D array of latitude coordinates (degrees North)")
    longitudes: List[float] = Field(..., description="1D array of longitude coordinates (degrees East)")
    grid_shape: Tuple[int, int] = Field(..., description="(height_lat, width_lon) dimensions")
    extent_bbox: Tuple[float, float, float, float] = Field(
        ..., description="(min_lat, max_lat, min_lon, max_lon) bounding box"
    )
    dx_km_mean: float = Field(26.5, description="Mean zonal grid cell spacing in kilometers")
    dy_km: float = Field(27.75, description="Meridional grid cell spacing in kilometers (constant)")
    orientation: str = Field("NORTH_TO_SOUTH", description="Row index orientation: 'NORTH_TO_SOUTH' or 'SOUTH_TO_NORTH'")


class SpatialRainfallSample(BaseModel):
    """Multi-channel spatial meteorological sample for 2D post-processing."""
    timestamp: str = Field(..., description="Forecast initialization timestamp (ISO-8601 UTC)")
    valid_time: str = Field(..., description="Target valid verification timestamp (ISO-8601 UTC)")
    lead_time_hours: int = Field(24, ge=0, description="Forecast lead time in hours")
    grid: SpatialGridDefinition = Field(..., description="2D spatial grid metadata")
    
    # Primary rainfall fields [H, W]
    raw_nwp_grid: List[List[float]] = Field(..., description="Raw NWP precipitation field (mm/day)")
    observed_grid: Optional[List[List[float]]] = Field(None, description="Ground truth observed rainfall field (mm/day)")
    
    # Atmospheric predictor channels [H, W]
    atmospheric_channels: Dict[str, List[List[float]]] = Field(
        default_factory=dict,
        description="Atmospheric feature grids (u850, v850, rh850, rh700, mslp, cape, vorticity, ivt, etc.)"
    )
    
    # Topographic & orographic channels [H, W]
    terrain_channels: Dict[str, List[List[float]]] = Field(
        default_factory=dict,
        description="Topographic grids (elevation, slope, aspect, orographic_lift, coastal_convergence)"
    )
    
    # Synoptic and temporal regime conditioning
    regime_probabilities: Dict[str, float] = Field(
        default_factory=lambda: {
            "ACTIVE_MONSOON": 0.5,
            "BREAK_MONSOON": 0.05,
            "MONSOON_LOW_LPS": 0.15,
            "COASTAL_CONVERGENCE": 0.1,
            "OROGRAPHIC_RAINFALL": 0.15,
            "WESTERN_DISTURBANCE": 0.02,
            "NEUTRAL": 0.03,
        },
        description="Multi-label regime probability distribution"
    )
    temporal_regime_features: Dict[str, float] = Field(
        default_factory=lambda: {
            "day1_regime_prob": 0.52,
            "day2_regime_prob": 0.50,
            "persistence_prob": 0.61,
            "transition_prob": 0.39,
            "forecast_horizon_days": 1.0,
        },
        description="Temporal regime context from Phase 12 transition engine"
    )
    
    provenance_source: str = Field("ECMWF_ERA5_GFS_COMBINED", description="Data source provenance")
    is_fallback: bool = Field(False, description="Whether fallback synthetic/reanalysis data is used")


class SpatialSmoothnessDiagnostics(BaseModel):
    """Physical and numerical spatial smoothness metrics for 2D rainfall fields."""
    total_variation: float = Field(..., description="Total Variation (L1 norm of spatial gradients)")
    mean_gradient: float = Field(..., description="Mean magnitude of 2D spatial gradient (mm/cell)")
    laplacian_variance: float = Field(..., description="Variance of 2D Laplacian operator (discontinuity indicator)")
    max_gradient: float = Field(..., description="Maximum local gradient step between adjacent cells (mm/cell)")


class SpatialPredictionOutput(BaseModel):
    """Complete 2D spatially corrected rainfall forecast response."""
    grid: SpatialGridDefinition = Field(..., description="2D spatial grid metadata")
    
    # Deterministic 2D Fields [H, W]
    raw_nwp_grid: List[List[float]] = Field(..., description="Raw NWP input rainfall grid (mm/day)")
    corrected_grid: List[List[float]] = Field(..., description="Regime-aware spatially corrected rainfall grid (mm/day)")
    residual_delta_grid: List[List[float]] = Field(..., description="Spatial correction delta field (corrected - raw) in mm")
    
    # Spatial Quantile Uncertainty Fields [H, W] (P10 <= P50 <= P90)
    p10_grid: Optional[List[List[float]]] = Field(None, description="10th percentile lower rainfall bound field (mm)")
    p50_grid: Optional[List[List[float]]] = Field(None, description="50th percentile median rainfall field (mm)")
    p90_grid: Optional[List[List[float]]] = Field(None, description="90th percentile upper rainfall bound field (mm)")
    
    # Calibrated Heavy Rainfall Exceedance Probability Fields [H, W] (P64.5 >= P115.6 >= P204.5)
    prob_heavy_ge_64_5_grid: List[List[float]] = Field(
        ..., description="Probability of Heavy Rainfall >= 64.5 mm/day [0.0, 1.0]"
    )
    prob_very_heavy_ge_115_6_grid: List[List[float]] = Field(
        ..., description="Probability of Very Heavy Rainfall >= 115.6 mm/day [0.0, 1.0]"
    )
    prob_extreme_ge_204_5_grid: List[List[float]] = Field(
        ..., description="Probability of Extremely Heavy Rainfall >= 204.5 mm/day [0.0, 1.0]"
    )
    
    # Synoptic Context & Diagnostics
    dominant_regime: str = Field(..., description="Dominant synoptic weather regime")
    regime_probabilities: Dict[str, float] = Field(..., description="Multi-label regime probabilities")
    smoothness_diagnostics: SpatialSmoothnessDiagnostics = Field(..., description="Spatial field smoothness diagnostics")
    
    # Model Metadata & Provenance
    model_id: str = Field(..., description="Model identifier (e.g. 'SPATIAL_REGIME_AWARE_V1')")
    model_version: str = Field("SpatialRegimeML_v1.0", description="Model architecture version")
    uncertainty_status: str = Field("CALIBRATED_EMPIRICAL_RESIDUALS", description="Quantile generation method")
    probability_method: str = Field("RESIDUAL_DISTRIBUTION_LOGISTIC_MAPPING", description="Probability calibration method")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Execution and training provenance metadata")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SpatialVerificationSummary(BaseModel):
    """Forensic spatial and multi-scale verification benchmark across models."""
    model_id: str = Field(..., description="Model identifier")
    model_name: str = Field(..., description="Human-readable model name")
    sample_count: int = Field(..., description="Total evaluated 2D spatial grid instances")
    total_grid_cells: int = Field(..., description="Total evaluated individual grid cells")
    
    # Continuous Error Metrics
    rmse_mm: float = Field(..., description="Continuous Root Mean Square Error across all cells (mm)")
    mae_mm: float = Field(..., description="Mean Absolute Error (mm)")
    mean_bias_mm: float = Field(..., description="Mean Bias Error (mm)")
    
    # Categorical Scores at Heavy Rain Threshold (>= 64.5 mm)
    csi_64_5: float = Field(..., description="Critical Success Index at 64.5 mm")
    ets_64_5: float = Field(..., description="Equitable Threat Score at 64.5 mm")
    pod_64_5: float = Field(..., description="Probability of Detection at 64.5 mm")
    far_64_5: float = Field(..., description="False Alarm Ratio at 64.5 mm")
    
    # Multi-Scale Fractions Skill Score (FSS)
    fss_25km: Optional[float] = Field(None, description="FSS at 25km neighborhood scale (1x1 window)")
    fss_50km: Optional[float] = Field(None, description="FSS at 50km neighborhood scale (5x5 window)")
    fss_100km: Optional[float] = Field(None, description="FSS at 100km neighborhood scale (9x9 window)")
    
    # Spatial Field Diagnostics
    pattern_correlation: float = Field(..., description="Spatial 2D Pearson pattern correlation with ground truth")
    gradient_rmse: float = Field(..., description="Root Mean Square Error of spatial gradient vector field")
    total_variation: float = Field(..., description="Mean Total Variation of predicted field")
    
    status: str = Field("EXPERIMENTAL_EVALUATION", description="Verification benchmark status")


class SpatialStatusResponse(BaseModel):
    """Operational status of Phase 13 spatial post-processing engine."""
    status: str = Field("OPERATIONAL_READY", description="Engine operational status")
    phase: str = Field("PHASE_13_SPATIAL_INTELLIGENCE", description="System phase identifier")
    registered_spatial_models: List[str] = Field(..., description="List of registered 2D spatial models")
    active_dashboard_model: str = Field(..., description="Currently active production model")
    production_model_replaced: bool = Field(False, description="Strict safety check: production model unchanged")
    canonical_grid: SpatialGridDefinition = Field(..., description="Canonical 0.25° target grid definition")
    deep_spatial_model_status: str = Field("EXPERIMENTAL_SUPPORTED", description="Status of deep convolutional / U-Net spatial models")
    mode: str = Field("SPATIAL_NWP_POSTPROCESSING", description="Current execution mode")
