"""
Canonical Meteorological Data Models and Schemas for PS26080 (MoES / NCMRWF).
Defines standardized data records across NWP, Reanalysis, Observational, and Geographic domains.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class CanonicalMeteorologicalRecord(BaseModel):
    """
    Canonical standardized meteorological observation/forecast record across all sources.
    Every provider (NCUM, NEPS, ERA5, GFS, IMD, IMERG) maps to this canonical structure.
    """
    # 1. Temporal Identifiers
    timestamp: str = Field(..., description="Forecast valid time or observation time (ISO 8601 UTC)")
    forecast_initialization: Optional[str] = Field(None, description="Forecast cycle initialization timestamp (ISO 8601 UTC)")
    lead_time_hours: int = Field(default=0, ge=0, description="Forecast lead time in hours (0 for observations)")

    # 2. Spatial Coordinates
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 Longitude in decimal degrees")

    # 3. Precipitation & Ensemble Statistics
    rainfall: float = Field(..., ge=0.0, description="Point rainfall rate or accumulation (mm)")
    ensemble_mean: Optional[float] = Field(None, ge=0.0, description="Ensemble mean rainfall (mm)")
    ensemble_std: Optional[float] = Field(None, ge=0.0, description="Ensemble standard deviation (mm)")
    ensemble_min: Optional[float] = Field(None, ge=0.0, description="Ensemble minimum rainfall (mm)")
    ensemble_max: Optional[float] = Field(None, ge=0.0, description="Ensemble maximum rainfall (mm)")
    ensemble_p10: Optional[float] = Field(None, ge=0.0, description="Ensemble 10th percentile rainfall (mm)")
    ensemble_p90: Optional[float] = Field(None, ge=0.0, description="Ensemble 90th percentile rainfall (mm)")

    # 4. Multi-Level Atmospheric Thermodynamic Fields (850, 700, 500 hPa)
    temperature_850: Optional[float] = Field(None, description="Temperature at 850 hPa (Kelvin or Celsius)")
    temperature_700: Optional[float] = Field(None, description="Temperature at 700 hPa (Kelvin or Celsius)")
    temperature_500: Optional[float] = Field(None, description="Temperature at 500 hPa (Kelvin or Celsius)")

    relative_humidity_850: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative humidity at 850 hPa (%)")
    relative_humidity_700: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative humidity at 700 hPa (%)")
    relative_humidity_500: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative humidity at 500 hPa (%)")

    # 5. Multi-Level Dynamic Wind Components (m/s)
    u850: Optional[float] = Field(None, description="Zonal wind u at 850 hPa (m/s, positive eastward)")
    v850: Optional[float] = Field(None, description="Meridional wind v at 850 hPa (m/s, positive northward)")
    u700: Optional[float] = Field(None, description="Zonal wind u at 700 hPa (m/s)")
    v700: Optional[float] = Field(None, description="Meridional wind v at 700 hPa (m/s)")
    u500: Optional[float] = Field(None, description="Zonal wind u at 500 hPa (m/s)")
    v500: Optional[float] = Field(None, description="Meridional wind v at 500 hPa (m/s)")

    # 6. Geopotential Height & Vertical Velocity
    geopotential_850: Optional[float] = Field(None, description="Geopotential height at 850 hPa (gpm or m^2/s^2)")
    geopotential_500: Optional[float] = Field(None, description="Geopotential height at 500 hPa (gpm or m^2/s^2)")
    vertical_velocity: Optional[float] = Field(None, description="Vertical pressure velocity omega at 700/500 hPa (Pa/s)")

    # 7. Surface Variables
    surface_pressure: Optional[float] = Field(None, description="Surface pressure (hPa or Pa)")
    mslp: Optional[float] = Field(None, description="Mean Sea Level Pressure (hPa)")
    cape_j_kg: Optional[float] = Field(None, ge=0.0, description="Convective Available Potential Energy (J/kg)")

    # 8. Static Geographic & Topographic Predictors
    elevation: Optional[float] = Field(None, description="Terrain elevation above MSL (meters)")
    slope: Optional[float] = Field(None, ge=0.0, le=90.0, description="Terrain slope angle (degrees)")
    aspect: Optional[float] = Field(None, ge=0.0, le=360.0, description="Terrain aspect facing direction (degrees)")
    terrain_roughness: Optional[float] = Field(None, ge=0.0, description="Terrain roughness index (m)")
    distance_to_coast: Optional[float] = Field(None, ge=0.0, description="Orthodromic distance to nearest coastline (km)")

    # 9. Verification Ground Truth Observation
    observed_rainfall: Optional[float] = Field(None, ge=0.0, description="Collocated gauge/IMD observed rainfall (mm)")

    # 10. Data Provenance & Reliability Metadata
    data_source: str = Field(..., description="Originating provider (e.g., 'NCMRWF_NCUM', 'ERA5', 'GFS_FALLBACK', 'IMD_GRIDDED')")
    data_quality: str = Field(default="RAW", description="Quality flag: 'QC_PASSED', 'IMPUTED', 'RAW', 'FLAGGED'")
    is_demo: bool = Field(default=False, description="Explicit boolean flag: True if record is demo/synthetic fallback")

    @field_validator("longitude")
    @classmethod
    def normalize_longitude(cls, v: float) -> float:
        """Standardize longitudes to [-180, 180] domain."""
        while v > 180.0:
            v -= 360.0
        while v < -180.0:
            v += 360.0
        return round(v, 6)


class QualityControlLog(BaseModel):
    """Log entry recording automatic corrections or flags during ingestion."""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    field_name: str
    original_value: Any
    corrected_value: Any
    rule_applied: str
    action_taken: str = Field(..., description="'CORRECTED', 'CAPPED', 'FLAGGED', 'REJECTED'")


class MeteorologicalFeatureSet(BaseModel):
    """Derived physical atmospheric and geographic features for regime classification & AI models."""
    # Derived Wind Metrics
    wind_speed_850: float = Field(..., ge=0.0, description="850 hPa wind speed (m/s)")
    wind_direction_850: float = Field(..., ge=0.0, le=360.0, description="850 hPa meteorological wind direction (deg)")
    wind_speed_700: float = Field(..., ge=0.0, description="700 hPa wind speed (m/s)")
    wind_direction_700: float = Field(..., ge=0.0, le=360.0, description="700 hPa meteorological wind direction (deg)")
    vertical_wind_shear: float = Field(..., ge=0.0, description="Magnitude of vector wind shear between 850 and 500 hPa (m/s)")

    # Synoptic Gradients & Moisture Transport
    pressure_gradient: float = Field(..., description="Local spatial or temporal pressure gradient (hPa/deg or hPa/3h)")
    moisture_transport_proxy: float = Field(..., ge=0.0, description="Integrated moisture transport proxy: q * V_850 (g/kg * m/s)")

    # Accumulation Curves
    rainfall_accumulation_6h: float = Field(default=0.0, ge=0.0, description="6-hour accumulated rainfall (mm)")
    rainfall_accumulation_12h: float = Field(default=0.0, ge=0.0, description="12-hour accumulated rainfall (mm)")
    rainfall_accumulation_24h: float = Field(default=0.0, ge=0.0, description="24-hour accumulated rainfall (mm)")

    # Ensemble Disagreement
    ensemble_spread: float = Field(default=0.0, ge=0.0, description="Ensemble spread (P90 - P10 or std deviation)")
    forecast_disagreement: float = Field(default=0.0, ge=0.0, description="Normalized forecast disagreement index [0.0, 1.0]")

    # Geographic & Orographic Indices
    terrain_gradient: float = Field(default=0.0, description="Local elevation gradient magnitude (m/km)")
    orographic_lift_index: float = Field(default=0.0, ge=0.0, description="Orographic lift index: V_normal * slope")
    coastal_moisture_indicator: float = Field(default=0.0, ge=0.0, description="Coastal proximity & onshore moisture convergence index")


class DataSourceStatusResponse(BaseModel):
    """Operational status report for all meteorological adapters in the platform."""
    source_id: str
    name: str
    role: str
    is_live_operational: bool
    is_demo_fallback: bool
    last_ingestion_time: Optional[str]
    sample_record_count: int
    quality_status: str
    error_detail: Optional[str]
