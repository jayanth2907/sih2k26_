"""Post-processing products, probability, district, and verification schemas for PS26080."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.regime import WeatherRegimeType


class ProductDetail(BaseModel):
    """Details for a single forecast product."""
    product_name: str = Field(..., description="Human-readable product name")
    accumulated_24h_mm: float = Field(..., ge=0.0, description="Total 24h accumulated precipitation in mm")
    peak_hourly_rate_mm_hr: float = Field(..., ge=0.0, description="Peak hourly rainfall rate in mm/h")
    correction_delta_mm: Optional[float] = Field(None, description="Difference from raw NWP (corrected - raw) in mm")
    uncertainty_lower_bound_mm: Optional[float] = Field(None, ge=0.0, description="10th percentile / lower forecast bound in mm")
    uncertainty_upper_bound_mm: Optional[float] = Field(None, ge=0.0, description="90th percentile / upper forecast bound in mm")
    ensemble_spread_mm: Optional[float] = Field(None, ge=0.0, description="Ensemble spread / standard deviation in mm")
    hourly_series: List[float] = Field(default_factory=list, description="24-hour chronological hourly precipitation rates (mm/h)")
    is_operational_ncmrwf: bool = Field(False, description="Whether data is direct from operational NCMRWF (vs fallback)")
    data_source: str = Field("NCMRWF NCUM / GFS Fallback", description="Data provider or model source")


class PostProcessingComparison(BaseModel):
    """The 4-product forecast comparison demonstrating post-processing skill."""
    raw_nwp: ProductDetail = Field(..., description="1. Raw NWP Forecast Baseline")
    quantile_mapping: ProductDetail = Field(..., description="2. Empirical Quantile Mapping (EQM)")
    global_ml_correction: ProductDetail = Field(..., description="3. Global ML Post-Processing (Standard Non-Regime)")
    regime_aware_ml_correction: ProductDetail = Field(..., description="4. Regime-Aware AI Post-Processing (Target Architecture)")


class ProbabilityTier(BaseModel):
    """Heavy rainfall probability tier."""
    probability: float = Field(..., ge=0.0, le=1.0, description="Estimated event probability [0.0, 1.0]")
    predicted: bool = Field(..., description="Whether probability exceeds operational alert threshold")
    threshold_mm: float = Field(..., description="Physical threshold limit (e.g. 64.5, 115.6, 204.5 mm/day)")
    category: str = Field(..., description="Category label")


class HeavyRainfallProbabilities(BaseModel):
    """Multi-threshold heavy rainfall probability package (IMD definitions)."""
    heavy_rainfall_ge_64_5mm: ProbabilityTier = Field(..., description="Heavy Rainfall (64.5 - 115.5 mm/day)")
    very_heavy_rainfall_ge_115_6mm: ProbabilityTier = Field(..., description="Very Heavy Rainfall (115.6 - 204.4 mm/day)")
    extremely_heavy_rainfall_ge_204_5mm: ProbabilityTier = Field(..., description="Extremely Heavy Rainfall (>= 204.5 mm/day)")


class DistrictForecast(BaseModel):
    """District-level aggregated forecast, uncertainty, probabilities, and prototype decision support."""
    district_id: Optional[str] = Field(None, description="Stable unique district identifier (e.g. 'MH_SATARA')")
    district_name: str = Field(..., description="District identifier")
    state_name: str = Field(..., description="State identifier")
    lat: Optional[float] = Field(None, description="District centroid latitude")
    lon: Optional[float] = Field(None, description="District centroid longitude")
    raw_nwp_mm: float = Field(..., ge=0.0, description="Raw NWP accumulated rainfall (mm)")
    corrected_mm: float = Field(..., ge=0.0, description="Regime-aware corrected rainfall / P50 forecast (mm)")
    correction_delta_mm: float = Field(..., description="Correction magnitude (mm)")
    uncertainty_lower_bound_mm: float = Field(..., ge=0.0, description="Uncertainty lower bound / P10 forecast quantile (mm)")
    uncertainty_upper_bound_mm: float = Field(..., ge=0.0, description="Uncertainty upper bound / P90 forecast quantile (mm)")
    ensemble_spread_mm: float = Field(..., ge=0.0, description="Ensemble spread / standard deviation (mm)")
    heavy_prob: float = Field(..., ge=0.0, le=1.0, description="Calibrated probability of heavy rain >= 64.5mm [0.0, 1.0]")
    very_heavy_prob: float = Field(..., ge=0.0, le=1.0, description="Calibrated probability of very heavy rain >= 115.6mm [0.0, 1.0]")
    extreme_prob: float = Field(..., ge=0.0, le=1.0, description="Calibrated probability of extreme rain >= 204.5mm [0.0, 1.0]")
    dominant_regime: WeatherRegimeType = Field(..., description="Dominant weather regime in district")
    regime_confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Confidence in dominant regime assignment")
    aggregation_method: str = Field(default="POINT_SAMPLED_CENTROID", description="Spatial aggregation method (e.g. 'POINT_SAMPLED_CENTROID')")
    decision_support_category: str = Field(default="NORMAL", description="Deterministic category: 'NORMAL', 'HEAVY_RAINFALL', 'VERY_HEAVY_RAINFALL', 'EXTREMELY_HEAVY_RAINFALL'")
    decision_basis: str = Field(default="Forecast median evaluated against IMD-aligned threshold criteria.", description="Explicit scientific basis for decision support classification")
    provenance_status: str = Field(default="HELD_OUT_PROTOTYPE_EVALUATION", description="Provenance tracking label")
    is_official_imd_warning: bool = Field(default=False, description="Strictly False: Prototype decision support, not an official IMD warning")
    disclaimer: str = Field(default="Prototype model-derived decision support. Not an official IMD warning.", description="Mandatory operational disclaimer")



class VerificationMetricSet(BaseModel):
    """Standard spatial and categorical forecast verification metrics."""
    rmse_mm: float = Field(..., description="Root Mean Square Error in mm (lower is better)")
    mae_mm: Optional[float] = Field(None, description="Mean Absolute Error in mm (lower is better)")
    mean_bias_mm: Optional[float] = Field(None, description="Mean Bias in mm")
    ets: float = Field(..., ge=-0.33, le=1.0, description="Equitable Threat Score (higher is better, max 1.0)")
    csi: float = Field(..., ge=0.0, le=1.0, description="Critical Success Index / Threat Score (higher is better)")
    pod: float = Field(..., ge=0.0, le=1.0, description="Probability of Detection / Hit Rate")
    far: float = Field(..., ge=0.0, le=1.0, description="False Alarm Ratio (lower is better)")
    fss_50km: Optional[float] = Field(None, description="Fractions Skill Score at 50km neighborhood radius (null if not available at regime level)")
    sample_count: Optional[int] = Field(None, description="Number of evaluated samples")
    heavy_event_count: Optional[int] = Field(None, description="Number of observed heavy rain >= 64.5mm events")


class RegimeVerificationEntry(BaseModel):
    """Regime-stratified verification scorecard entry."""
    regime_name: str = Field(..., description="Machine regime key (e.g. 'ACTIVE_MONSOON')")
    display_name: str = Field(..., description="Human-readable regime name")
    sample_count: int = Field(..., ge=0, description="Number of held-out samples in this regime")
    heavy_event_count: int = Field(..., ge=0, description="Number of observed heavy rainfall (>=64.5mm) events")
    status: str = Field("SUFFICIENT", description="'SUFFICIENT', 'INSUFFICIENT_SAMPLE', or 'NO_EVALUATION_SAMPLES'")
    fss_available: bool = Field(False, description="Whether spatial FSS is genuinely available at regime level")
    interpretation: Optional[str] = Field(None, description="Factual meteorological regime description")
    raw_nwp: Optional[VerificationMetricSet] = Field(None, description="Raw NWP Forecast baseline metrics")
    quantile_mapping: Optional[VerificationMetricSet] = Field(None, description="Empirical Quantile Mapping metrics")
    global_ml: Optional[VerificationMetricSet] = Field(None, description="Global ML post-processing metrics")
    regime_aware_ml: Optional[VerificationMetricSet] = Field(None, description="Regime-Aware AI post-processing metrics")


class FssScaleResult(BaseModel):
    """Multi-scale Fractions Skill Score result for a single spatial neighborhood scale."""
    scale_km: int = Field(..., description="Spatial neighborhood diameter / scale in kilometers (25, 50, 100)")
    window_size_cells: int = Field(..., description="Derived filter window size in grid cells")
    raw_nwp: Optional[float] = Field(None, description="Raw NWP Forecast FSS score")
    quantile_mapping: Optional[float] = Field(None, description="Empirical Quantile Mapping FSS score")
    global_ml: Optional[float] = Field(None, description="Global ML post-processing FSS score")
    regime_aware_ml: Optional[float] = Field(None, description="Regime-Aware AI post-processing FSS score")
    threshold_mm: float = Field(default=64.5, description="Applied heavy rainfall threshold in mm / 24h")
    status: str = Field(default="VALID", description="'VALID', 'NO_EVENT_REFERENCE', or 'INSUFFICIENT_SPATIAL_DATA'")
    valid_grid_cells: Optional[int] = Field(None, description="Total evaluated valid grid cells in domain")
    event_cells_observed: Optional[int] = Field(None, description="Total observed event grid cells (>= threshold)")


class MultiScaleFssReport(BaseModel):
    """Multi-scale spatial Fractions Skill Score (FSS) package across 25km, 50km, and 100km."""
    threshold_mm: float = Field(default=64.5, description="Precipitation threshold limit in mm / 24h")
    grid_resolution_km: float = Field(default=25.0, description="Nominal grid spacing in km (IMD 0.25° ~ 25km)")
    evaluation_domain: str = Field(default="South Asian Monsoon Domain (0.25° Gridded IMD / DWR Target)", description="Spatial domain description")
    scales: Dict[str, FssScaleResult] = Field(default_factory=dict, description="FSS results keyed by scale ('25km', '50km', '100km')")


class VerificationResponse(BaseModel):
    """Verification benchmark comparing the 4 post-processing products across regimes and spatial scales."""
    evaluation_period: str = Field("2024–2025 Monsoon Season (Held-out Prospective Evaluation)", description="Verification dataset / period")
    sample_count: int = Field(default=800, description="Total number of evaluated held-out test samples")
    threshold_mm: float = Field(default=64.5, description="Applied heavy rainfall evaluation threshold in mm")
    benchmark_metrics: Dict[str, VerificationMetricSet] = Field(..., description="Overall skill metrics for raw_nwp, quantile_mapping, global_ml, regime_aware_ml")
    regime_stratified: Dict[str, RegimeVerificationEntry] = Field(default_factory=dict, description="Regime-stratified verification scorecard")
    multi_scale_fss: Optional[MultiScaleFssReport] = Field(None, description="Multi-scale spatial Fractions Skill Score (FSS) at 25km, 50km, and 100km")
    regime_skill_gain_pct: Dict[str, float] = Field(..., description="Percentage improvement in CSI/ETS per regime")
    ground_truth_source: str = Field("IMD 0.25° Gridded Rainfall & DWR QPE Network", description="Verification observational reference")
    provenance_status: str = Field("HELD_OUT_PROTOTYPE_EVALUATION", description="Provenance tracking label")

