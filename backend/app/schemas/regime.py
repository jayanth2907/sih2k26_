"""Weather Regime schemas for PS26080 (MoES / NCMRWF)."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WeatherRegimeType(str, Enum):
    """South Asian Summer Monsoon Synoptic & Mesoscale Weather Regimes."""
    ACTIVE_MONSOON = "ACTIVE_MONSOON"
    BREAK_MONSOON = "BREAK_MONSOON"
    MONSOON_LOW_LPS = "MONSOON_LOW_LPS"
    COASTAL_CONVERGENCE = "COASTAL_CONVERGENCE"
    OROGRAPHIC_RAINFALL = "OROGRAPHIC_RAINFALL"
    WESTERN_DISTURBANCE = "WESTERN_DISTURBANCE"
    NEUTRAL = "NEUTRAL"


class SynopticFeatures(BaseModel):
    """Synoptic meteorological parameters diagnosed for regime classification."""
    monsoon_trough_position: str = Field("NORMAL", description="Monsoon trough axis position (e.g. SOUTH_OF_NORMAL, NORMAL, FOOTHILLS)")
    trough_position: str = Field("normal", description="Normalized trough position identifier")
    monsoon_trough_lat: float = Field(24.5, description="Diagnosed monsoon trough latitude (°N)")
    low_level_jet_speed_kts: float = Field(22.0, ge=0.0, description="850 hPa Arabian Sea Low-Level Jet speed in knots")
    low_level_jet_direction_deg: float = Field(245.0, ge=0.0, le=360.0, description="850 hPa LLJ wind direction in degrees")
    offshore_trough_active: bool = Field(False, description="Whether West Coast offshore trough signature is active")
    olr_w_m2: float = Field(215.0, description="Outgoing Longwave Radiation proxy (W/m²)")
    olr_anomaly_w_m2: float = Field(-15.0, description="Outgoing Longwave Radiation anomaly (W/m²), negative = deep convection")
    mid_tropospheric_vorticity_1e5_s: float = Field(2.5, description="Mid-tropospheric (850-700 hPa) relative vorticity (10⁻⁵ s⁻¹)")
    vorticity_850hpa_s1: float = Field(2.5e-5, description="850 hPa relative vorticity (s⁻¹)")
    surface_pressure_anomaly_hpa: float = Field(-2.5, description="MSLP anomaly from standard atmosphere (hPa)")
    cape_j_kg: float = Field(1200.0, description="Convective Available Potential Energy (J/kg)")
    integrated_vapor_transport_kg_m_s: float = Field(180.0, description="Integrated Vapor Transport proxy (kg/(m·s))")
    moisture_flux_convergence_g_kg_s: float = Field(1.8, description="Vertically integrated moisture flux convergence (g/(kg·s))")
    orographic_lift_index: float = Field(0.0, description="Orographic lift index")
    coastal_convergence_index: float = Field(0.0, description="Coastal convergence index")


class AtmosphericDriver(BaseModel):
    """Explainability driver detailing atmospheric feature contribution."""
    feature: str = Field(..., description="Atmospheric feature name (e.g., 850_hPa_wind_speed)")
    value: float = Field(..., description="Actual quantified feature value")
    importance: float = Field(..., ge=0.0, le=1.0, description="Normalized relative importance score [0, 1]")
    description: Optional[str] = Field(None, description="Physical interpretation of driver contribution")


class RegimeResponse(BaseModel):
    """Hierarchical weather regime classification response."""
    primary_regime: WeatherRegimeType = Field(..., description="Dominant primary synoptic weather regime")
    confidence: float = Field(0.85, ge=0.0, le=1.0, description="Classification confidence [0.0, 1.0]")
    primary_confidence: float = Field(0.85, ge=0.0, le=1.0, description="Alias for confidence")
    secondary_regimes: List[WeatherRegimeType] = Field(default_factory=list, description="Co-occurring secondary physical mechanisms")
    probabilities: Dict[str, float] = Field(default_factory=dict, description="Full multi-label regime probability distribution")
    drivers: List[AtmosphericDriver] = Field(default_factory=list, description="Top atmospheric drivers explaining the regime")
    synoptic_features: SynopticFeatures = Field(..., description="Diagnosed synoptic indices and parameters")
    regime_narrative: str = Field(..., description="Physical meteorological explanation of identified regime")
    model_version: str = Field("RegimeClassifier_v2.0_Hybrid", description="Classifier model architecture version")
    data_source: str = Field("NCMRWF_NCUM_REGIME_ENGINE", description="Atmospheric data source for classification")
    is_demo: bool = Field(False, description="Whether this classification uses synthetic/demo data")
    timestamp: str = Field(..., description="Classification ISO timestamp")

