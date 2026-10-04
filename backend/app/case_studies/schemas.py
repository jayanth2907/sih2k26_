"""
Schemas for Historical Extreme-Event Case Studies (Phase 9 - MoES / NCMRWF PS26080).
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CaseStudyStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    PARTIALLY_AVAILABLE = "PARTIALLY_AVAILABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class TrainingOverlapStatus(str, Enum):
    TRUE = "TRUE"  # Part of 2018–2022 historical training split
    FALSE = "FALSE"  # Completely external or validation/test split
    UNKNOWN = "UNKNOWN"


class EventWindow(BaseModel):
    """Temporal extent of the historical extreme event."""
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    peak_date: str = Field(..., description="Peak precipitation date (YYYY-MM-DD)")
    duration_hours: int = Field(..., description="Event duration in hours")
    description: str = Field(..., description="Brief meteorological synopsis")


class SpatialDomain(BaseModel):
    """Geographical region and representative coordinates."""
    region_name: str = Field(..., description="Affected geographical region / district")
    state_name: str = Field(..., description="State or Union Territory")
    latitude: float = Field(..., description="Representative centroid latitude")
    longitude: float = Field(..., description="Representative centroid longitude")
    elevation_m: Optional[float] = Field(None, description="Elevation above sea level in meters")


class ObservationRecord(BaseModel):
    """Historical observational ground truth measurements."""
    peak_24h_mm: Optional[float] = Field(None, description="Observed peak 24-hour rainfall in mm (None if unavailable)")
    station_name: str = Field(..., description="Observing ground station or gridded cell")
    source_agency: str = Field(..., description="Observational authority (e.g. 'IMD High-Density Rain Gauge Network')")
    is_available: bool = Field(True, description="Whether actual ground truth measurements exist in record")


class ForecastComparison(BaseModel):
    """Four-model forecast evaluation across baseline and AI post-processors."""
    is_forecast_available: bool = Field(..., description="Whether historical NWP forecast fields are available")
    raw_nwp_mm: Optional[float] = Field(None, description="Raw uncalibrated NWP accumulated 24h precipitation in mm")
    eqm_mm: Optional[float] = Field(None, description="Empirical Quantile Mapping calibrated precipitation in mm")
    global_ml_mm: Optional[float] = Field(None, description="Global ML post-processing precipitation in mm")
    regime_aware_ml_mm: Optional[float] = Field(None, description="Regime-Aware AI calibrated precipitation in mm")
    bias_correction_delta_mm: Optional[float] = Field(None, description="Correction delta (Regime-Aware - Raw NWP) in mm")
    raw_nwp_error_mm: Optional[float] = Field(None, description="Raw NWP error (forecast - observation) in mm")
    regime_aware_error_mm: Optional[float] = Field(None, description="Regime-Aware error (forecast - observation) in mm")
    error_reduction_pct: Optional[float] = Field(None, description="Absolute error reduction percentage")


class UncertaintyRecord(BaseModel):
    """Calibrated uncertainty quantiles and spread."""
    is_available: bool = Field(True, description="Whether uncertainty quantiles are computed")
    p10_mm: Optional[float] = Field(None, description="Lower forecast quantile (10th percentile) in mm")
    p50_mm: Optional[float] = Field(None, description="Median calibrated forecast (50th percentile) in mm")
    p90_mm: Optional[float] = Field(None, description="Upper forecast quantile (90th percentile) in mm")
    ensemble_spread_mm: Optional[float] = Field(None, description="Derived ensemble spread / standard deviation in mm")


class ExceedanceProbabilities(BaseModel):
    """Calibrated heavy rainfall exceedance probabilities."""
    is_available: bool = Field(True, description="Whether exceedance probabilities are computed")
    heavy_ge_64_5mm: Optional[float] = Field(None, description="Probability of heavy rain >= 64.5 mm [0, 1]")
    very_heavy_ge_115_6mm: Optional[float] = Field(None, description="Probability of very heavy rain >= 115.6 mm [0, 1]")
    extreme_ge_204_5mm: Optional[float] = Field(None, description="Probability of extremely heavy rain >= 204.5 mm [0, 1]")


class RegimeRecord(BaseModel):
    """Historical synoptic weather regime classification."""
    is_available: bool = Field(True, description="Whether historical regime classification is available")
    primary_regime: Optional[str] = Field(None, description="Dominant diagnosed regime key (e.g. 'OROGRAPHIC_RAINFALL')")
    confidence: Optional[float] = Field(None, description="Regime classification confidence [0, 1]")
    posterior_probabilities: Optional[Dict[str, float]] = Field(default_factory=dict, description="Soft multi-regime posterior distribution")


class SpatialVerificationFss(BaseModel):
    """Event-level Fractions Skill Score (FSS) at multiple spatial scales."""
    is_available: bool = Field(False, description="Whether 2D spatial grids exist for multi-scale FSS calculation")
    fss_25km: Optional[float] = Field(None, description="FSS at 25km neighborhood diameter")
    fss_50km: Optional[float] = Field(None, description="FSS at 50km neighborhood diameter")
    fss_100km: Optional[float] = Field(None, description="FSS at 100km neighborhood diameter")
    threshold_mm: float = Field(default=64.5, description="Physical threshold applied (64.5 mm / 24h)")
    status_message: str = Field(default="MULTI-SCALE FSS NOT AVAILABLE — 2D HISTORICAL GRID NOT PRESENT", description="Factual availability message")


class CaseStudyProvenance(BaseModel):
    """Scientific metadata and data provenance audit trail."""
    evaluation_role: str = Field(default="HISTORICAL CASE STUDY (SUPPLEMENTARY)", description="Evaluation purpose")
    training_overlap: TrainingOverlapStatus = Field(..., description="Whether event overlaps with model training data")
    benchmark_membership: str = Field(default="NOT PART OF PRIMARY 2024–2025 BENCHMARK", description="Explicit benchmark isolation statement")
    is_official_imd_warning: bool = Field(default=False, description="Strictly False: Retrospective case study, not an official warning")
    disclaimer: str = Field(
        default="Historical event analysis for scientific model verification. Not an official IMD warning or forecast.",
        description="Mandatory scientific disclaimer",
    )


class CaseStudySummary(BaseModel):
    """Lightweight summary card for catalog listing."""
    case_id: str = Field(..., description="Unique case study identifier (e.g. 'KERALA_2018')")
    title: str = Field(..., description="Human-readable case title")
    subtitle: str = Field(..., description="Event category / impact subtitle")
    event_year: int = Field(..., description="Calendar year of the event")
    status: CaseStudyStatus = Field(..., description="Data availability status")
    spatial_domain: SpatialDomain = Field(..., description="Geographical domain")
    peak_observation_mm: Optional[float] = Field(None, description="Peak recorded 24h rainfall in mm")
    training_overlap: TrainingOverlapStatus = Field(..., description="Training split overlap status")
    primary_regime: Optional[str] = Field(None, description="Dominant meteorological regime")


class CaseStudyDetail(BaseModel):
    """Complete case-study profile for detailed view."""
    case_id: str = Field(..., description="Unique case study identifier")
    title: str = Field(..., description="Human-readable case title")
    subtitle: str = Field(..., description="Event category subtitle")
    status: CaseStudyStatus = Field(..., description="Data completeness status")
    event_window: EventWindow = Field(..., description="Event date window")
    spatial_domain: SpatialDomain = Field(..., description="Spatial domain")
    observation: ObservationRecord = Field(..., description="Observational ground truth")
    forecast_comparison: ForecastComparison = Field(..., description="4-product forecast comparison")
    uncertainty: UncertaintyRecord = Field(..., description="Calibrated uncertainty quantiles")
    exceedance_probabilities: ExceedanceProbabilities = Field(..., description="Calibrated exceedance probabilities")
    regime: RegimeRecord = Field(..., description="Diagnosed synoptic regime")
    spatial_fss: SpatialVerificationFss = Field(..., description="Spatial Fractions Skill Score")
    provenance: CaseStudyProvenance = Field(..., description="Scientific provenance and leakage disclosure")
    synoptic_summary: str = Field(..., description="Meteorological analysis of the event")
    why_corrected_summary: str = Field(..., description="Physical explanation of NWP systematic error and AI correction")
