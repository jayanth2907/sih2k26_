"""
Pydantic Schemas for Full India District Decision Support & Warning Intelligence (Phase 14).
Supports polygon-based administrative aggregation, spatial weight caching,
threshold probabilities, quantile uncertainty, synoptic atmospheric drivers,
deterministic decision categorization, machine-generated bulletins, and multi-format exports.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

from backend.app.schemas.regime import WeatherRegimeType


class AggregationMethod(str, Enum):
    """District spatial aggregation methodology."""
    POLYGON_AREA_WEIGHTED = "POLYGON_AREA_WEIGHTED"
    POINT_SAMPLED_CENTROID = "POINT_SAMPLED_CENTROID"
    POPULATION_WEIGHTED = "POPULATION_WEIGHTED"


class DecisionSupportCategory(str, Enum):
    """Deterministic prototype decision support category."""
    NORMAL = "NORMAL"
    HEAVY_RAINFALL = "HEAVY_RAINFALL"
    VERY_HEAVY_RAINFALL = "VERY_HEAVY_RAINFALL"
    EXTREMELY_HEAVY_RAINFALL = "EXTREMELY_HEAVY_RAINFALL"


class DataQualityStatus(str, Enum):
    """Data quality and coverage status."""
    VALID = "VALID"
    PARTIAL = "PARTIAL"
    INSUFFICIENT_SPATIAL_COVERAGE = "INSUFFICIENT_SPATIAL_COVERAGE"
    MISSING_BOUNDARY = "MISSING_BOUNDARY"
    STALE_DATA = "STALE_DATA"
    FALLBACK = "FALLBACK"
    INVALID = "INVALID"


class DistrictPolygonGeometry(BaseModel):
    """GeoJSON-compliant Polygon or MultiPolygon representation."""
    type: str = Field("Polygon", description="GeoJSON geometry type: 'Polygon' or 'MultiPolygon'")
    coordinates: List[Any] = Field(..., description="WGS84 coordinate rings [[[lon, lat], ...]]")


class DistrictBoundaryRecord(BaseModel):
    """Administrative district boundary metadata and geometry."""
    district_id: str = Field(..., description="Stable unique district identifier (e.g. 'MH_SATARA')")
    district_name: str = Field(..., description="Official district name")
    state_id: str = Field(..., description="State / UT identifier code (e.g. 'MH')")
    state_name: str = Field(..., description="Official State / UT name")
    centroid_lat: float = Field(..., description="Geodesic centroid latitude (EPSG:4326)")
    centroid_lon: float = Field(..., description="Geodesic centroid longitude (EPSG:4326)")
    area_km2: float = Field(..., ge=0.0, description="Geodesic / equal-area polygon area in square kilometers")
    bounding_box: Tuple[float, float, float, float] = Field(
        ..., description="(min_lat, max_lat, min_lon, max_lon) in WGS84"
    )
    geometry: DistrictPolygonGeometry = Field(..., description="Boundary geometry representation")
    source: str = Field("Survey of India / LGD Administrative Baseline", description="Authoritative boundary source")
    administrative_vintage: str = Field("2019-2021 Reorganized Census Baseline", description="Administrative lineage vintage")
    geometry_quality: str = Field("VALIDATED_WGS84", description="Topology and CRS validation status")
    is_coastal: bool = Field(False, description="Whether district has maritime coastline")


class DistrictSpatialStats(BaseModel):
    """Spatial rainfall distribution statistics across district polygon."""
    mean_24h_mm: float = Field(..., ge=0.0, description="Area-weighted mean 24h rainfall (mm)")
    max_24h_mm: float = Field(..., ge=0.0, description="Maximum rainfall within district polygon (mm)")
    min_24h_mm: float = Field(..., ge=0.0, description="Minimum rainfall within district polygon (mm)")
    median_24h_mm: float = Field(..., ge=0.0, description="Spatial median rainfall (mm)")
    p90_24h_mm: float = Field(..., ge=0.0, description="90th percentile spatial rainfall within district (mm)")
    p95_24h_mm: float = Field(..., ge=0.0, description="95th percentile spatial rainfall within district (mm)")
    
    # Area fractions exceeding standard IMD-aligned accumulation thresholds
    heavy_area_fraction: float = Field(..., ge=0.0, le=1.0, description="Fraction of district area with R >= 64.5 mm [0.0, 1.0]")
    very_heavy_area_fraction: float = Field(..., ge=0.0, le=1.0, description="Fraction of district area with R >= 115.6 mm [0.0, 1.0]")
    extreme_area_fraction: float = Field(..., ge=0.0, le=1.0, description="Fraction of district area with R >= 204.5 mm [0.0, 1.0]")
    
    # Grid coverage metrics
    valid_area_fraction: float = Field(1.0, ge=0.0, le=1.0, description="Fraction of polygon covered by valid grid cells")
    missing_area_fraction: float = Field(0.0, ge=0.0, le=1.0, description="Fraction of polygon missing rainfall grid data")
    intersected_cell_count: int = Field(..., ge=1, description="Total number of 2D grid cells intersecting district")


class DistrictProbabilityStats(BaseModel):
    """Spatially aggregated heavy rainfall exceedance probabilities."""
    heavy_probability: float = Field(..., ge=0.0, le=1.0, description="Area-weighted probability of rain >= 64.5 mm [0.0, 1.0]")
    very_heavy_probability: float = Field(..., ge=0.0, le=1.0, description="Area-weighted probability of rain >= 115.6 mm [0.0, 1.0]")
    extreme_probability: float = Field(..., ge=0.0, le=1.0, description="Area-weighted probability of rain >= 204.5 mm [0.0, 1.0]")
    monotonicity_verified: bool = Field(True, description="Enforces P(heavy) >= P(very_heavy) >= P(extreme)")


class DistrictUncertaintyStats(BaseModel):
    """District forecast uncertainty quantiles."""
    p10_mm: float = Field(..., ge=0.0, description="10th percentile lower bound forecast (mm)")
    p50_mm: float = Field(..., ge=0.0, description="50th percentile median forecast (mm)")
    p90_mm: float = Field(..., ge=0.0, description="90th percentile upper bound forecast (mm)")
    ensemble_spread_mm: float = Field(..., ge=0.0, description="Inter-quantile spread / standard error proxy (mm)")
    uncertainty_category: str = Field("MODERATE", description="'LOW', 'MODERATE', 'HIGH', or 'EXTREME'")
    method: str = Field("APPROXIMATE_AREA_AGGREGATED_QUANTILE", description="Quantile aggregation methodology")


class DistrictAtmosphericDrivers(BaseModel):
    """Synoptic and mesoscale atmospheric drivers attribution for district."""
    low_level_jet_mps: Optional[float] = Field(None, description="850 hPa wind speed / LLJ magnitude (m/s)")
    integrated_vapor_transport: Optional[float] = Field(None, description="Moisture flux / IVT (kg/m/s)")
    relative_humidity_850_pct: Optional[float] = Field(None, description="850 hPa Relative Humidity (%)")
    mslp_anomaly_hpa: Optional[float] = Field(None, description="Mean Sea Level Pressure anomaly (hPa)")
    cape_j_kg: Optional[float] = Field(None, description="Convective Available Potential Energy (J/kg)")
    vorticity_850: Optional[float] = Field(None, description="850 hPa relative vorticity (1e-5 s^-1)")
    orographic_lift_index: Optional[float] = Field(None, description="Terrain slope wind projection index")
    coastal_convergence_index: Optional[float] = Field(None, description="Land-sea thermal & friction convergence index")
    major_drivers: List[str] = Field(default_factory=list, description="Top positive synoptic driver factors")


class DistrictDecisionThresholds(BaseModel):
    """Configurable prototype model decision escalation thresholds."""
    version: str = Field("PS26080_PROTO_v14.0", description="Threshold specification version")
    accumulation_heavy_mm: float = Field(64.5, description="IMD-aligned heavy rainfall limit (mm/24h)")
    accumulation_very_heavy_mm: float = Field(115.6, description="IMD-aligned very heavy rainfall limit (mm/24h)")
    accumulation_extreme_mm: float = Field(204.5, description="IMD-aligned extreme rainfall limit (mm/24h)")
    heavy_probability_threshold: float = Field(0.55, ge=0.0, le=1.0, description="Prototype escalation probability for heavy rain")
    very_heavy_probability_threshold: float = Field(0.40, ge=0.0, le=1.0, description="Prototype escalation probability for very heavy rain")
    extreme_probability_threshold: float = Field(0.25, ge=0.0, le=1.0, description="Prototype escalation probability for extreme rain")
    heavy_area_fraction_threshold: float = Field(0.40, ge=0.0, le=1.0, description="District area coverage trigger for heavy rain")
    very_heavy_area_fraction_threshold: float = Field(0.30, ge=0.0, le=1.0, description="District area coverage trigger for very heavy rain")
    extreme_area_fraction_threshold: float = Field(0.20, ge=0.0, le=1.0, description="District area coverage trigger for extreme rain")
    min_valid_area_fraction: float = Field(0.60, ge=0.0, le=1.0, description="Minimum spatial grid coverage required")


class DistrictForecastProduct(BaseModel):
    """Complete standardized district-level forecast and warning intelligence product."""
    district_id: str = Field(..., description="Stable district identifier (e.g. 'MH_SATARA')")
    district_name: str = Field(..., description="District name")
    state_id: str = Field(..., description="State / UT identifier code")
    state_name: str = Field(..., description="State name")
    lat: float = Field(..., description="District centroid latitude")
    lon: float = Field(..., description="District centroid longitude")
    area_km2: float = Field(..., description="District polygon area (km²)")
    
    # Aggregation & Method
    aggregation_method: AggregationMethod = Field(
        AggregationMethod.POLYGON_AREA_WEIGHTED, description="Spatial aggregation method"
    )
    raw_nwp_mean_mm: float = Field(..., ge=0.0, description="Raw NWP area-weighted baseline (mm)")
    
    # Core Spatial Rainfall Metrics
    spatial_stats: DistrictSpatialStats = Field(..., description="2D spatial rainfall distribution")
    probabilities: DistrictProbabilityStats = Field(..., description="Calibrated exceedance probabilities")
    uncertainty: DistrictUncertaintyStats = Field(..., description="Quantile uncertainty estimates")
    
    # Atmospheric & Regime Context
    primary_regime: WeatherRegimeType = Field(..., description="Dominant weather regime in district")
    regime_confidence: float = Field(..., ge=0.0, le=1.0, description="Regime classification confidence")
    regime_probabilities: Dict[str, float] = Field(default_factory=dict, description="Multi-label regime probability distribution")
    atmospheric_drivers: DistrictAtmosphericDrivers = Field(default_factory=DistrictAtmosphericDrivers, description="Synoptic drivers")
    
    # Decision Support
    decision_category: DecisionSupportCategory = Field(..., description="Deterministic decision support category")
    decision_reason: str = Field(..., description="Structured deterministic decision basis")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall forecast & decision confidence")
    
    # Population Weighting Status (Strict rule: NEVER FABRICATED)
    population_weighting_status: str = Field("NOT_AVAILABLE", description="'NOT_AVAILABLE' unless Census raster present")
    
    # Quality & Provenance
    quality_status: DataQualityStatus = Field(DataQualityStatus.VALID, description="Data quality and completeness status")
    data_provenance: str = Field("ECMWF_ERA5_GFS_COMBINED", description="Observational and NWP provenance source")
    model_provenance: str = Field("SPATIAL_REGIME_AWARE_V1", description="Post-processing ML model identifier")
    boundary_version: str = Field("SOI_LGD_748_v1.0", description="Boundary lineage version")
    forecast_valid_time: str = Field(..., description="Target valid time (ISO-8601 UTC)")
    
    # Mandatory Safety Disclaimers (Strict Rules 12, 13, 37)
    is_official_imd_warning: bool = Field(False, description="Strictly False: Prototype research decision support")
    disclaimer: str = Field(
        "Prototype model-derived decision support. Not an official IMD warning.",
        description="Mandatory institutional disclaimer",
    )


class DistrictBulletin(BaseModel):
    """Structured machine-generated district weather and decision bulletin."""
    district_id: str = Field(..., description="District identifier")
    district_name: str = Field(..., description="District name")
    state_name: str = Field(..., description="State name")
    forecast_period: str = Field(..., description="Valid 24h forecast window")
    generated_at: str = Field(..., description="Timestamp of generation (ISO-8601 UTC)")
    
    # Quantitative Summary
    rainfall_mean_mm: float = Field(..., description="Expected area-weighted mean rainfall (mm)")
    rainfall_p50_mm: float = Field(..., description="Median forecast P50 (mm)")
    rainfall_p90_mm: float = Field(..., description="Upper bound forecast P90 (mm)")
    rainfall_max_mm: float = Field(..., description="Peak localized rainfall within district (mm)")
    
    # Probabilities
    heavy_probability_pct: float = Field(..., description="Heavy rain probability (%)")
    very_heavy_probability_pct: float = Field(..., description="Very heavy rain probability (%)")
    extreme_probability_pct: float = Field(..., description="Extremely heavy rain probability (%)")
    
    # Area Fractions
    heavy_area_fraction_pct: float = Field(..., description="District area with heavy rain (%)")
    very_heavy_area_fraction_pct: float = Field(..., description="District area with very heavy rain (%)")
    extreme_area_fraction_pct: float = Field(..., description="District area with extreme rain (%)")
    
    # Regime & Dynamics
    dominant_regime: str = Field(..., description="Dominant weather regime")
    regime_confidence_pct: float = Field(..., description="Regime classification confidence (%)")
    major_drivers: List[str] = Field(default_factory=list, description="Primary synoptic features")
    uncertainty_level: str = Field(..., description="Uncertainty category")
    
    # Advisory & Category
    category: str = Field(..., description="Prototype decision-support category")
    decision_reason: str = Field(..., description="Structured deterministic reason")
    
    # Lineage
    data_provenance: str = Field(..., description="Underlying NWP and observational sources")
    boundary_version: str = Field(..., description="District boundary version")
    model_version: str = Field(..., description="Spatial post-processing model version")
    decision_threshold_version: str = Field(..., description="Decision threshold schema version")
    
    # Formatted Plain Text Bulletin
    formatted_bulletin_text: str = Field(..., description="Machine-generated structured plain text bulletin")
    disclaimer: str = Field(
        "Prototype model-derived decision support. Not an official IMD warning.",
        description="Statutory disclaimer",
    )


class DistrictStatusResponse(BaseModel):
    """Operational status of the Phase 14 District Decision Support Engine."""
    boundary_dataset: str = Field("Survey of India / LGD Administrative Baseline", description="District boundary source")
    boundary_version: str = Field("SOI_LGD_748_v1.0", description="Boundary dataset version")
    district_count: int = Field(748, description="Total cataloged administrative districts in framework")
    active_districts_loaded: int = Field(..., description="Number of loaded district boundary polygons")
    state_count: int = Field(36, description="Total States and Union Territories covered")
    geometry_valid: bool = Field(True, description="Geometry topology and bounds validation status")
    spatial_weight_cache_status: str = Field("PRECOMPUTED_READY", description="Spatial weight cache operational status")
    cached_weight_pairs: int = Field(..., description="Total precomputed (district, grid_cell) spatial weight pairs")
    population_data_status: str = Field("NOT_AVAILABLE", description="Authoritative population raster status")
    default_aggregation_method: str = Field("POLYGON_AREA_WEIGHTED", description="Default spatial aggregation method")
    centroid_baseline_available: bool = Field(True, description="Whether legacy centroid extraction is preserved")
    active_model: str = Field("SPATIAL_REGIME_AWARE_V1", description="Currently active spatial correction model")
    data_source: str = Field("NCMRWF NCUM / ECMWF ERA5 / GFS Fallback", description="Primary meteorological data provider")
    fallback_status: str = Field("ONLINE_LIVE_OR_VALIDATED_FALLBACK", description="Fallback execution mode")
    production_model_replaced: bool = Field(False, description="Strict safety check: production model unchanged")


class AggregationComparisonMetrics(BaseModel):
    """Comparison metrics between Centroid and Polygon Area-Weighted methods."""
    district_id: str = Field(..., description="District identifier")
    district_name: str = Field(..., description="District name")
    state_name: str = Field(..., description="State name")
    centroid_rainfall_mm: float = Field(..., description="Point-sampled centroid rainfall (mm)")
    polygon_mean_rainfall_mm: float = Field(..., description="Polygon area-weighted mean rainfall (mm)")
    absolute_difference_mm: float = Field(..., description="|Polygon - Centroid| rainfall difference (mm)")
    relative_difference_pct: float = Field(..., description="Percentage difference relative to mean")
    centroid_category: str = Field(..., description="Decision category under Centroid method")
    polygon_category: str = Field(..., description="Decision category under Polygon method")
    category_agreement: bool = Field(..., description="Whether both methods yield the identical decision category")
    centroid_heavy_prob: float = Field(..., description="Heavy rain probability at centroid")
    polygon_heavy_prob: float = Field(..., description="Area-weighted heavy rain probability")
    heavy_area_fraction: float = Field(..., description="Fraction of district exceeding 64.5 mm")


class AggregationComparisonSummary(BaseModel):
    """Batch verification comparing Centroid baseline vs Polygon aggregation."""
    sample_district_count: int = Field(..., description="Number of districts evaluated")
    mean_absolute_difference_mm: float = Field(..., description="Mean absolute difference across all districts (mm)")
    rmse_difference_mm: float = Field(..., description="Root mean square difference between methods (mm)")
    max_absolute_difference_mm: float = Field(..., description="Maximum single-district rainfall discrepancy (mm)")
    category_concordance_pct: float = Field(..., description="Percentage of districts with matching decision category (%)")
    category_switch_count: int = Field(..., description="Number of districts where category changed")
    district_comparisons: List[AggregationComparisonMetrics] = Field(default_factory=list, description="Per-district comparison")
    interpretation: str = Field(
        "Demonstrates spatial averaging over complex terrain smoothing local extremes vs point sampling.",
        description="Meteorological interpretation of comparison",
    )
