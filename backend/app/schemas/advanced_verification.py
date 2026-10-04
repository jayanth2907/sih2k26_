"""
Pydantic Schemas for Advanced Verification, Probabilistic Calibration & Reliability (Phase 15).
Supports continuous metrics, categorical contingency tables, threshold stratification,
regime & multi-label breakdowns, reliability diagrams, ECE/MCE, sharpness,
uncertainty interval coverage, quantile crossing, bootstrap confidence intervals,
and fair-comparison model trade-off matrices.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field


class EvaluationNamespace(str, Enum):
    """Provenance namespaces for verification benchmarks."""
    ADVANCED_VERIFICATION_V1 = "ADVANCED_VERIFICATION_V1"
    HELD_OUT_PROTOTYPE_EVALUATION = "HELD_OUT_PROTOTYPE_EVALUATION"
    REAL_DATA_TRAINING_EVALUATION = "REAL_DATA_TRAINING_EVALUATION"
    SPATIAL_EXPERIMENTAL_VERIFICATION = "SPATIAL_EXPERIMENTAL_VERIFICATION"


class MetricConfidenceInterval(BaseModel):
    """Bootstrap confidence interval for a verification metric."""
    point_estimate: float = Field(..., description="Sample point estimate")
    lower_ci_95: float = Field(..., description="95% Bootstrap lower confidence bound (2.5th percentile)")
    upper_ci_95: float = Field(..., description="95% Bootstrap upper confidence bound (97.5th percentile)")
    bootstrap_iterations: int = Field(1000, description="Number of bootstrap replications")
    method: str = Field("PERCENTILE_BOOTSTRAP", description="Bootstrap methodology")


class ContinuousVerificationMetrics(BaseModel):
    """Continuous precipitation error metrics (mm/24h)."""
    rmse_mm: float = Field(..., description="Root Mean Square Error: sqrt(mean((f - o)^2)) in mm")
    mae_mm: float = Field(..., description="Mean Absolute Error: mean(|f - o|) in mm")
    mean_bias_mm: float = Field(..., description="Mean Bias: mean(f - o) in mm (Positive = Overprediction)")
    sample_count: int = Field(..., ge=0, description="Total evaluated sample instances")
    rmse_ci: Optional[MetricConfidenceInterval] = Field(None, description="95% CI for RMSE")
    mae_ci: Optional[MetricConfidenceInterval] = Field(None, description="95% CI for MAE")


class CategoricalContingencyMetrics(BaseModel):
    """Categorical skill scores at a specific rainfall threshold."""
    threshold_mm: float = Field(..., description="Rainfall threshold (64.5, 115.6, 204.5 mm)")
    hits: int = Field(..., ge=0, description="True Positives (Hits, a)")
    false_alarms: int = Field(..., ge=0, description="False Alarms (b)")
    misses: int = Field(..., ge=0, description="False Negatives (Misses, c)")
    correct_negatives: int = Field(..., ge=0, description="True Negatives (d)")
    total_events_observed: int = Field(..., ge=0, description="Total observed event occurrences (a + c)")
    
    pod: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability of Detection: a / (a + c)")
    far: Optional[float] = Field(None, ge=0.0, le=1.0, description="False Alarm Ratio: b / (a + b)")
    csi: Optional[float] = Field(None, ge=0.0, le=1.0, description="Critical Success Index: a / (a + b + c)")
    ets: Optional[float] = Field(None, ge=-0.33, le=1.0, description="Equitable Threat Score")
    csi_ci: Optional[MetricConfidenceInterval] = Field(None, description="95% CI for CSI")
    status: str = Field("VALID", description="'VALID', 'NO_EVENT_REFERENCE', or 'INSUFFICIENT_SAMPLE'")


class ReliabilityBinData(BaseModel):
    """Calibration statistics for a single forecast probability bin."""
    bin_lower: float = Field(..., ge=0.0, le=1.0, description="Lower probability bin limit")
    bin_upper: float = Field(..., ge=0.0, le=1.0, description="Upper probability bin limit")
    bin_midpoint: float = Field(..., ge=0.0, le=1.0, description="Nominal center of probability bin")
    mean_forecast_probability: float = Field(..., ge=0.0, le=1.0, description="Empirical mean forecast probability in bin")
    observed_event_frequency: float = Field(..., ge=0.0, le=1.0, description="Observed event occurrence rate in bin (o / N_bin)")
    sample_count: int = Field(..., ge=0, description="Number of predictions falling in this bin")


class ProbabilisticCalibrationReport(BaseModel):
    """Reliability, resolution, and calibration scores for a probability product."""
    threshold_mm: float = Field(..., description="Evaluated exceedance threshold (e.g. 64.5 mm)")
    brier_score: float = Field(..., ge=0.0, le=1.0, description="Brier Score: mean((p - o)^2)")
    brier_skill_score: Optional[float] = Field(None, description="BSS relative to explicit reference forecast")
    reference_forecast_name: str = Field("SAMPLE_CLIMATOLOGY", description="Reference forecast for BSS")
    expected_calibration_error: float = Field(..., ge=0.0, le=1.0, description="Expected Calibration Error (ECE)")
    max_calibration_error: float = Field(..., ge=0.0, le=1.0, description="Maximum Calibration Error (MCE)")
    
    # Sharpness distribution (fraction of predictions in probability brackets)
    sharpness_near_zero_pct: float = Field(..., description="% of predictions with P < 0.10")
    sharpness_mid_range_pct: float = Field(..., description="% of predictions with 0.10 <= P <= 0.80")
    sharpness_near_one_pct: float = Field(..., description="% of predictions with P > 0.80")
    
    reliability_bins: List[ReliabilityBinData] = Field(default_factory=list, description="10-bin reliability diagram data")
    status: str = Field("VALID", description="Calibration evaluation status")


class UncertaintyIntervalReport(BaseModel):
    """Empirical reliability evaluation for forecast quantiles (P10, P50, P90)."""
    nominal_coverage_pct: float = Field(80.0, description="Nominal interval coverage: 80% for [P10, P90]")
    empirical_coverage_pct: float = Field(..., description="Observed fraction of ground-truth observations within [P10, P90]")
    mean_interval_width_mm: float = Field(..., description="Mean interval width (P90 - P10) in mm")
    normalized_interval_width: float = Field(..., description="Mean interval width divided by mean observation")
    quantile_crossing_violations: int = Field(0, description="Count of invalid ordering violations (P10 > P50 or P50 > P90)")
    underprediction_rate_pct: float = Field(..., description="% of observations exceeding P90 (upper misses)")
    overprediction_rate_pct: float = Field(..., description="% of observations falling below P10 (lower misses)")
    status: str = Field("VALID", description="Uncertainty verification status")


class RegimeStratifiedEntry(BaseModel):
    """Verification score record stratified by a specific synoptic weather regime."""
    regime_name: str = Field(..., description="Weather regime identifier (e.g. 'OROGRAPHIC_RAINFALL')")
    is_multi_label: bool = Field(False, description="Whether this represents a multi-label intersection subset")
    sample_count: int = Field(..., ge=0, description="Sample count in regime subset")
    observed_event_count: int = Field(..., ge=0, description="Observed events >= threshold in regime subset")
    continuous: ContinuousVerificationMetrics = Field(..., description="Continuous rainfall error in regime")
    categorical: CategoricalContingencyMetrics = Field(..., description="Threshold skill scores in regime")
    probabilistic: Optional[ProbabilisticCalibrationReport] = Field(None, description="Calibration in regime")
    status: str = Field("VALID", description="'VALID' or 'INSUFFICIENT_SAMPLE'")


class SpatialNeighborhoodScaleReport(BaseModel):
    """FSS and physical geometry audit for a single spatial neighborhood radius."""
    scale_label: str = Field(..., description="Scale label (e.g. '25km', '50km', '100km')")
    nominal_radius_km: float = Field(..., description="Target physical scale in kilometers")
    window_size_cells: int = Field(..., description="Kernel window dimension in grid cells (W x W)")
    actual_meridional_span_km: float = Field(..., description="Physical North-South span of window (km)")
    actual_zonal_span_km_mean: float = Field(..., description="Mean physical East-West span of window across India domain (km)")
    actual_area_footprint_km2: float = Field(..., description="Physical spatial area envelope of neighborhood window (km²)")
    fss_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Fractions Skill Score at this scale")
    status: str = Field("VALID", description="FSS computation status")


class SpatialFieldVerificationReport(BaseModel):
    """2D spatial grid verification diagnostics."""
    grid_name: str = Field("Canonical_0.25deg_WGS84", description="Evaluated grid layout")
    pattern_correlation_2d: float = Field(..., ge=-1.0, le=1.0, description="2D Pearson pattern correlation")
    gradient_rmse_mm: float = Field(..., description="Spatial gradient vector RMSE (mm/cell)")
    laplacian_variance_diff: float = Field(..., description="Difference in 2D Laplacian field roughness")
    scales: List[SpatialNeighborhoodScaleReport] = Field(default_factory=list, description="Multi-scale FSS reports")


class ModelTradeOffEntry(BaseModel):
    """Single model trade-off entry across continuous, categorical, spatial, and probabilistic axes."""
    model_id: str = Field(..., description="Model identifier (e.g. 'REGIME_AWARE_ML')")
    model_name: str = Field(..., description="Human-readable model name")
    is_directly_comparable: bool = Field(True, description="Strict rule: Fair comparison on identical test population")
    
    # Continuous Error
    rmse_mm: float = Field(..., description="Root Mean Square Error (mm)")
    mae_mm: float = Field(..., description="Mean Absolute Error (mm)")
    mean_bias_mm: float = Field(..., description="Mean Bias (mm)")
    
    # Categorical Skill at Heavy Rain (>= 64.5 mm)
    csi_64_5: Optional[float] = Field(None, description="CSI at 64.5 mm")
    ets_64_5: Optional[float] = Field(None, description="ETS at 64.5 mm")
    pod_64_5: Optional[float] = Field(None, description="POD at 64.5 mm")
    far_64_5: Optional[float] = Field(None, description="FAR at 64.5 mm")
    
    # Categorical Skill at Very Heavy (>= 115.6 mm) & Extreme (>= 204.5 mm)
    csi_115_6: Optional[float] = Field(None, description="CSI at 115.6 mm")
    csi_204_5: Optional[float] = Field(None, description="CSI at 204.5 mm")
    
    # Spatial FSS
    fss_25km: Optional[float] = Field(None, description="FSS at 25km")
    fss_50km: Optional[float] = Field(None, description="FSS at 50km")
    fss_100km: Optional[float] = Field(None, description="FSS at 100km")
    pattern_correlation: Optional[float] = Field(None, description="2D Pattern Correlation")
    
    # Probabilistic Calibration
    brier_score_64_5: Optional[float] = Field(None, description="Brier score at 64.5 mm")
    ece_64_5: Optional[float] = Field(None, description="Expected Calibration Error at 64.5 mm")
    
    # Uncertainty
    uncertainty_coverage_80pct: Optional[float] = Field(None, description="Empirical coverage of nominal 80% interval (%)")


class TemporalRegimeVerificationReport(BaseModel):
    """Verification of Phase 12 temporal regime transition and projection engine."""
    horizon_days: int = Field(..., description="Forecast horizon lead time (Days 1 to 10)")
    top1_accuracy_pct: float = Field(..., description="Top-1 regime prediction accuracy (%)")
    top2_accuracy_pct: float = Field(..., description="Top-2 regime prediction accuracy (%)")
    brier_score_multiclass: float = Field(..., description="Multi-class Brier score for regime probability distribution")
    log_loss: float = Field(..., description="Cross-entropy / Log Loss for regime transition matrix")
    calibration_error: float = Field(..., description="Regime probability calibration error")
    sample_count: int = Field(..., description="Evaluated temporal transition instances")


class CaseStudyVerificationEntry(BaseModel):
    """Verification summary for a historical benchmark case study."""
    event_id: str = Field(..., description="Case study identifier (e.g. 'KERALA_2018')")
    event_name: str = Field(..., description="Event title")
    date_range: str = Field(..., description="Historical date span")
    observation_available: bool = Field(True, description="Observational grid availability")
    nwp_forecast_available: bool = Field(True, description="NWP baseline availability")
    spatial_grid_available: bool = Field(True, description="2D Spatial grid availability")
    probability_available: bool = Field(True, description="Probability field availability")
    rmse_raw_nwp_mm: float = Field(..., description="Raw NWP RMSE during event")
    rmse_corrected_mm: float = Field(..., description="Post-processed RMSE during event")
    peak_observed_mm: float = Field(..., description="Peak observed 24h rainfall")
    peak_forecast_mm: float = Field(..., description="Peak post-processed 24h rainfall")
    csi_64_5: float = Field(..., description="Critical Success Index during event")
    provenance_status: str = Field("HISTORICAL_REAL_DATA_EVALUATION", description="Provenance status")


class AdvancedVerificationSummary(BaseModel):
    """Complete comprehensive verification response for Phase 15."""
    evaluation_id: str = Field(..., description="Unique evaluation execution identifier")
    namespace: EvaluationNamespace = Field(
        EvaluationNamespace.ADVANCED_VERIFICATION_V1, description="Provenance evaluation namespace"
    )
    test_period: str = Field("JJAS 2022–2023 (Held-Out Test Partition)", description="Chronological test period")
    training_period: str = Field("JJAS 2010–2019", description="Training period")
    validation_period: str = Field("JJAS 2020–2021", description="Validation tuning period")
    total_test_samples: int = Field(..., description="Total test set sample instances")
    total_heavy_rain_events: int = Field(..., description="Total observed heavy rain events >= 64.5 mm")
    
    # Multi-model trade-off matrix
    model_trade_offs: List[ModelTradeOffEntry] = Field(..., description="Comprehensive model trade-offs")
    
    # Stratified analyses
    regime_breakdown: List[RegimeStratifiedEntry] = Field(..., description="Regime-conditional verification scores")
    temporal_regime_verification: List[TemporalRegimeVerificationReport] = Field(..., description="Day 1-10 regime projection scores")
    probabilistic_calibration: List[ProbabilisticCalibrationReport] = Field(..., description="Multi-threshold calibration reports")
    uncertainty_verification: UncertaintyIntervalReport = Field(..., description="Quantile interval coverage metrics")
    spatial_diagnostics: SpatialFieldVerificationReport = Field(..., description="2D spatial field & FSS verification")
    case_studies: List[CaseStudyVerificationEntry] = Field(..., description="Historical extreme event evaluations")
    
    # Provenance & Audit Governance
    configuration_hash: str = Field(..., description="SHA-256 hash of verification parameters")
    leakage_audit_status: str = Field("PASSED_ZERO_LEAKAGE", description="Temporal and spatial leakage audit status")
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    disclaimer: str = Field(
        "Verification benchmarks are conducted strictly on independent held-out data. "
        "No universal model ranking is declared; metric-specific trade-offs are reported.",
        description="Scientific governance disclaimer",
    )
