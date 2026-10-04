"""
Temporal Regime Intelligence Schemas for PS26080 (MoES / NCMRWF).
Defines formal regime state vectors, sequences, transition matrices,
persistence profiles, and Day 1–10 temporal projection schemas.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.app.schemas.regime import AtmosphericDriver, SynopticFeatures, WeatherRegimeType


class RegimeForecastMode(str, Enum):
    FORECAST_CONDITIONED = "FORECAST_CONDITIONED"
    TRANSITION_BASED_PROJECTION = "TRANSITION_BASED_PROJECTION"
    DEMO_FIXTURE = "DEMO_FIXTURE"


class RegimeFeatureSnapshot(BaseModel):
    """Atmospheric feature predictor vector at a single forecast/analysis step."""
    timestamp: str = Field(..., description="Snapshot valid timestamp (ISO-8601 UTC)")
    lead_time_hours: int = Field(default=0, ge=0, description="Forecast lead time in hours")
    llj_speed_kts: float = Field(..., ge=0.0, description="850 hPa Low-Level Jet speed in knots")
    llj_direction_deg: float = Field(..., ge=0.0, le=360.0, description="850 hPa LLJ direction in degrees")
    rh850: float = Field(..., ge=0.0, le=100.0, description="Relative humidity at 850 hPa (%)")
    rh700: float = Field(..., ge=0.0, le=100.0, description="Relative humidity at 700 hPa (%)")
    rh500: float = Field(..., ge=0.0, le=100.0, description="Relative humidity at 500 hPa (%)")
    olr_w_m2: float = Field(215.0, description="Outgoing Longwave Radiation convective proxy (W/m²)")
    cape_j_kg: float = Field(1500.0, ge=0.0, description="Convective Available Potential Energy (J/kg)")
    vorticity_850: float = Field(2.5e-5, description="850 hPa relative vorticity (s⁻¹)")
    mslp_hpa: float = Field(1008.0, description="Mean Sea Level Pressure (hPa)")
    vertical_velocity_pa_s: float = Field(-0.35, description="Omega vertical pressure velocity (Pa/s)")
    ivt_kg_m_s: float = Field(220.0, description="Integrated Vapor Transport proxy (kg/(m·s))")
    orographic_lift_index: float = Field(0.0, ge=0.0, description="Orographic lift index")
    coastal_convergence_index: float = Field(0.0, ge=0.0, description="Coastal convergence indicator")
    shear_850_500_ms: float = Field(15.0, ge=0.0, description="Bulk vertical wind shear magnitude (m/s)")
    regime_probabilities: Dict[str, float] = Field(default_factory=dict, description="Diagnosed regime probabilities")


class RegimeState(BaseModel):
    """Formal weather regime state vector at time t."""
    timestamp: str = Field(..., description="Timestamp ISO-8601 UTC")
    valid_time: str = Field(..., description="Valid time ISO-8601 UTC")
    primary_regime: WeatherRegimeType = Field(..., description="Dominant synoptic regime")
    regime_labels: List[WeatherRegimeType] = Field(default_factory=list, description="Multi-label active regimes")
    regime_probabilities: Dict[str, float] = Field(..., description="Complete multi-label probability distribution")
    classification_confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    transition_confidence: float = Field(0.80, ge=0.0, le=1.0, description="Markov transition confidence")
    persistence_probability: float = Field(..., ge=0.0, le=1.0, description="Probability of persisting in current regime at t+1")
    synoptic_features: SynopticFeatures = Field(..., description="Diagnosed synoptic indices")
    regime_source: str = Field("SASM_RegimeEngine_v2.1", description="Originating classifier architecture")


class RegimeSequenceStep(BaseModel):
    """Single chronological step in a temporal regime trajectory."""
    step_index: int = Field(..., ge=0, description="Time index (e.g. t0, t1, t2)")
    timestamp: str = Field(..., description="Step timestamp")
    primary_regime: WeatherRegimeType = Field(..., description="Primary regime at step")
    secondary_regimes: List[WeatherRegimeType] = Field(default_factory=list, description="Co-occurring regimes")
    probabilities: Dict[str, float] = Field(..., description="Probability distribution")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")


class RegimeSequence(BaseModel):
    """Temporal trajectory of weather regime states over a forecast or historical window."""
    sequence_id: str = Field(..., description="Unique sequence identifier")
    start_time: str = Field(..., description="Sequence start time")
    end_time: str = Field(..., description="Sequence end time")
    total_steps: int = Field(..., ge=1, description="Number of sequential time steps")
    steps: List[RegimeSequenceStep] = Field(..., description="Ordered regime sequence steps")
    dominant_trajectory_summary: str = Field(..., description="Narrative summary of regime evolution")


class RegimeTransitionEntry(BaseModel):
    """Single transition probability P(R_next = j | R_curr = i)."""
    from_regime: WeatherRegimeType
    to_regime: WeatherRegimeType
    transition_probability: float = Field(..., ge=0.0, le=1.0)
    raw_count: int = Field(..., ge=0)


class RegimeTransitionMatrix(BaseModel):
    """Complete empirical Markov regime transition matrix with provenance metadata."""
    matrix_version: str = Field("Markov_SASM_v2.0", description="Transition matrix model version")
    training_period: str = Field("2010–2019 JJAS (10-Year Historical Reanalysis)", description="Training split")
    smoothing_method: str = Field("Laplace Smoothing (alpha=1.0)", description="Smoothing algorithm")
    sample_count: int = Field(..., description="Total training transition pairs analyzed")
    regimes: List[str] = Field(..., description="Ordered regime state space")
    transition_probabilities: Dict[str, Dict[str, float]] = Field(
        ..., description="Nested probability matrix: P[from_regime][to_regime]"
    )
    dataset_id: str = Field("ERA5_JJAS_2010_2023_025DEG", description="Training dataset identifier")
    config_hash: str = Field(..., description="SHA-256 configuration hash")


class RegimeDurationStats(BaseModel):
    """Empirical duration statistics for a specific weather regime."""
    regime: WeatherRegimeType
    persistence_probability: float = Field(..., ge=0.0, le=1.0, description="P(R_t+1 = R_t | R_t)")
    mean_duration_days: float = Field(..., ge=0.0, description="Empirical mean duration in days")
    median_duration_days: float = Field(..., ge=0.0, description="Empirical median duration in days")
    sample_count: int = Field(..., ge=0, description="Historical occurrence episodes analyzed")


class RegimePersistenceReport(BaseModel):
    """Comprehensive regime persistence and duration report across all 7 SASM regimes."""
    report_title: str = "South Asian Summer Monsoon Regime Persistence & Duration Profile"
    training_period: str = "2010–2019 JJAS"
    regimes: Dict[str, RegimeDurationStats]
    methodology_note: str = "Persistence probabilities and durations estimated from the Phase 12 training dataset."


class DayProjectionStep(BaseModel):
    """Single day in a Day 1–10 regime forecast projection."""
    day: int = Field(..., ge=1, le=10, description="Forecast horizon day (1 to 10)")
    valid_date: str = Field(..., description="Valid date (YYYY-MM-DD)")
    primary_regime: WeatherRegimeType = Field(..., description="Projected dominant regime")
    probabilities: Dict[str, float] = Field(..., description="Projected probability distribution summing to 1.0")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Horizon-dependent projection confidence")


class Day10RegimeForecastResponse(BaseModel):
    """Complete 10-day temporal regime forecast response."""
    initialization_time: str = Field(..., description="Forecast cycle initialization UTC")
    mode: RegimeForecastMode = Field(..., description="Projection mode")
    current_regime: WeatherRegimeType = Field(..., description="Current primary regime")
    current_probabilities: Dict[str, float] = Field(..., description="Current probability vector")
    daily_projections: List[DayProjectionStep] = Field(..., description="Day 1 to Day 10 sequential projections")
    provenance: Dict[str, Any] = Field(..., description="Originating model and data provenance")
    disclaimer: str = (
        "Day 1–10 regime projections represent Markov probability propagation and/or forecast-conditioned synoptics. "
        "This is an AI post-processing decision support tool, not an official IMD extended-range outlook."
    )


class RegimeTransitionExplanation(BaseModel):
    """Physical explainability breakdown for a regime transition."""
    current_regime: WeatherRegimeType
    next_regime: WeatherRegimeType
    transition_probability: float = Field(..., ge=0.0, le=1.0)
    primary_drivers: List[str] = Field(..., description="Dominant physical mechanisms driving transition")
    feature_deltas: Dict[str, float] = Field(default_factory=dict, description="Quantified feature shifts (t+1 minus t)")
    meteorological_narrative: str = Field(..., description="Physical synoptic explanation")
