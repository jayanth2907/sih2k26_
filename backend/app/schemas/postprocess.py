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
    """District-level aggregated forecast and uncertainty."""
    district_name: str = Field(..., description="District identifier")
    state_name: str = Field(..., description="State identifier")
    raw_nwp_mm: float = Field(..., ge=0.0, description="Raw NWP accumulated rainfall (mm)")
    corrected_mm: float = Field(..., ge=0.0, description="Regime-aware corrected rainfall (mm)")
    correction_delta_mm: float = Field(..., description="Correction magnitude (mm)")
    uncertainty_lower_bound_mm: float = Field(..., ge=0.0, description="Uncertainty lower bound (mm)")
    uncertainty_upper_bound_mm: float = Field(..., ge=0.0, description="Uncertainty upper bound (mm)")
    ensemble_spread_mm: float = Field(..., ge=0.0, description="Ensemble spread (mm)")
    heavy_prob: float = Field(..., ge=0.0, le=1.0, description="Probability of heavy rain >= 64.5mm")
    very_heavy_prob: float = Field(..., ge=0.0, le=1.0, description="Probability of very heavy rain >= 115.6mm")
    extreme_prob: float = Field(..., ge=0.0, le=1.0, description="Probability of extreme rain >= 204.5mm")
    dominant_regime: WeatherRegimeType = Field(..., description="Dominant weather regime in district")


class VerificationMetricSet(BaseModel):
    """Standard spatial and categorical forecast verification metrics."""
    rmse_mm: float = Field(..., description="Root Mean Square Error in mm (lower is better)")
    ets: float = Field(..., ge=-0.33, le=1.0, description="Equitable Threat Score (higher is better, max 1.0)")
    csi: float = Field(..., ge=0.0, le=1.0, description="Critical Success Index / Threat Score (higher is better)")
    pod: float = Field(..., ge=0.0, le=1.0, description="Probability of Detection / Hit Rate")
    far: float = Field(..., ge=0.0, le=1.0, description="False Alarm Ratio (lower is better)")
    fss_50km: float = Field(..., ge=0.0, le=1.0, description="Fractions Skill Score at 50km neighborhood radius")


class VerificationResponse(BaseModel):
    """Verification benchmark comparing the 4 post-processing products across regimes."""
    evaluation_period: str = Field("2024 Monsoon Season (JJAS Verification)", description="Verification dataset / period")
    benchmark_metrics: Dict[str, VerificationMetricSet] = Field(..., description="Skill metrics for raw_nwp, quantile_mapping, global_ml, regime_aware_ml")
    regime_skill_gain_pct: Dict[str, float] = Field(..., description="Percentage improvement in CSI/ETS per regime")
    ground_truth_source: str = Field("IMD 0.25° Gridded Rainfall & DWR QPE Network", description="Verification observational reference")
