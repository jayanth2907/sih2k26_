"""
Abstract Base Classes and Data Contracts for Post-Processing Models (PS26080).
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
import numpy as np


class PostProcessingInput(BaseModel):
    """Standardized input payload for post-processing models."""
    raw_nwp_rainfall: float = Field(..., ge=0.0, description="Raw NWP 24-hour rainfall forecast (mm)")
    lead_time_hours: int = Field(default=24, ge=0, description="Forecast lead time in hours")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    month: int = Field(default=7, ge=1, le=12)
    day_of_year: int = Field(default=200, ge=1, le=366)

    # Ensemble features
    ensemble_mean: Optional[float] = None
    ensemble_std: Optional[float] = None
    ensemble_p10: Optional[float] = None
    ensemble_p90: Optional[float] = None

    # Multi-level thermodynamic & kinematic features
    wind_speed_850: float = Field(default=12.0, ge=0.0)
    wind_direction_850: float = Field(default=245.0, ge=0.0, le=360.0)
    wind_speed_700: float = Field(default=9.0, ge=0.0)
    wind_direction_700: float = Field(default=250.0, ge=0.0, le=360.0)
    relative_humidity_850: float = Field(default=80.0, ge=0.0, le=100.0)
    relative_humidity_700: float = Field(default=70.0, ge=0.0, le=100.0)
    specific_humidity_850: float = Field(default=14.0, ge=0.0)
    cape_j_kg: float = Field(default=1500.0, ge=0.0)
    moisture_transport_proxy: float = Field(default=180.0, ge=0.0)
    vertical_wind_shear: float = Field(default=8.0, ge=0.0)
    geopotential_500: float = Field(default=5850.0)
    vertical_velocity: float = Field(default=-0.3)
    mslp: float = Field(default=1008.0)

    # Geographic & Topographic features
    elevation: float = Field(default=150.0)
    slope: float = Field(default=1.5, ge=0.0)
    aspect: float = Field(default=270.0, ge=0.0, le=360.0)
    terrain_roughness: float = Field(default=10.0, ge=0.0)
    distance_to_coast: float = Field(default=80.0, ge=0.0)
    orographic_lift_index: float = Field(default=0.1, ge=0.0)
    coastal_moisture_indicator: float = Field(default=0.2, ge=0.0)

    # Regime Probabilities (from Phase 2 Regime Engine)
    regime_probabilities: Dict[str, float] = Field(
        default_factory=lambda: {
            "ACTIVE_MONSOON": 0.50,
            "BREAK_MONSOON": 0.05,
            "MONSOON_LOW_LPS": 0.15,
            "COASTAL_CONVERGENCE": 0.20,
            "OROGRAPHIC_RAINFALL": 0.25,
            "WESTERN_DISTURBANCE": 0.02,
            "NEUTRAL": 0.10,
        }
    )
    primary_regime: str = Field(default="ACTIVE_MONSOON")
    regime_confidence: float = Field(default=0.85, ge=0.0, le=1.0)

    # Provenance metadata
    data_source: str = Field(default="NCMRWF_NCUM")
    is_demo: bool = Field(default=False)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PostProcessingOutput(BaseModel):
    """Standardized output from any post-processing model."""
    model_id: str = Field(..., description="Identifier of model (raw_nwp, quantile_mapping, global_ml, regime_aware_ml)")
    model_name: str = Field(..., description="Human-readable model name")
    raw_rainfall_24h_mm: float = Field(..., ge=0.0)
    corrected_rainfall_24h_mm: float = Field(..., ge=0.0)
    predicted_bias_delta_mm: float = Field(..., description="predicted_error = corrected - raw")
    
    # Uncertainty distribution
    rainfall_p10_mm: float = Field(..., ge=0.0)
    rainfall_p50_mm: float = Field(..., ge=0.0)
    rainfall_p90_mm: float = Field(..., ge=0.0)
    uncertainty_width_mm: float = Field(..., ge=0.0, description="P90 - P10")

    # Heavy rainfall probabilities
    heavy_rain_prob_ge_64_5mm: float = Field(..., ge=0.0, le=1.0)
    very_heavy_rain_prob_ge_115_6mm: float = Field(..., ge=0.0, le=1.0)
    extreme_rain_prob_ge_204_5mm: float = Field(..., ge=0.0, le=1.0)
    
    # Hourly series breakdown if synthesized
    hourly_series_mm: List[float] = Field(default_factory=list)
    
    # Metadata & Attribution
    primary_regime: str
    regime_confidence: float
    data_source: str
    is_demo: bool
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BasePostProcessingModel(ABC):
    """
    Abstract Base Class for all SIH26080 Post-Processing Models.
    Enforces residual error formulation: error = observed - raw_nwp.
    """

    def __init__(self, model_id: str, model_name: str, version: str = "v1.0"):
        self.model_id = model_id
        self.model_name = model_name
        self.version = version
        self.is_fitted = False
        self.training_period: Optional[str] = None
        self.metrics: Dict[str, float] = {}

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> "BasePostProcessingModel":
        """
        Fit model on residual errors: y = observed_rainfall - raw_nwp_rainfall.
        """
        pass

    @abstractmethod
    def predict_error(self, X: np.ndarray) -> np.ndarray:
        """
        Predict residual error: delta = f(X).
        """
        pass

    def predict(self, sample: PostProcessingInput) -> PostProcessingOutput:
        """
        Produce standardized PostProcessingOutput from PostProcessingInput.
        """
        pass
