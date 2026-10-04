"""
Model Feature Input Contract Validator for PS26080 Phase 16.
Validates required, optional, derived, and unavailable meteorological/geographic features
before machine learning or spatial model inference, preventing silent zero-filling.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from backend.app.data.schemas.meteorology import CanonicalMeteorologicalRecord

logger = logging.getLogger("rainfall_backend.data.feature_validator")


class FeatureClassification(str, Enum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"
    DERIVED = "DERIVED"
    UNAVAILABLE = "UNAVAILABLE"
    STATIC = "STATIC"
    VERIFICATION_ONLY = "VERIFICATION_ONLY"


class FeatureValidationStatus(str, Enum):
    VALID = "VALID"
    MODEL_INPUT_INCOMPLETE = "MODEL_INPUT_INCOMPLETE"
    VALID_WITH_FALLBACK = "VALID_WITH_FALLBACK"


class ModelInputValidationResult(BaseModel):
    """Diagnostic outcome of operational model input feature contract validation."""
    status: FeatureValidationStatus = Field(..., description="Validation outcome status")
    is_inference_ready: bool = Field(..., description="Whether model inference can proceed safely")
    source: str = Field(..., description="NWP or meteorological data source identifier")
    forecast_time: str = Field(..., description="Target valid time or initialization time")
    required_features_present: List[str] = Field(default_factory=list)
    missing_features: List[str] = Field(default_factory=list)
    optional_features_present: List[str] = Field(default_factory=list)
    optional_features_missing: List[str] = Field(default_factory=list)
    derived_features_available: List[str] = Field(default_factory=list)
    unavailable_features: List[str] = Field(default_factory=list)
    error_message: Optional[str] = Field(None, description="Diagnostic error explanation")
    validated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ModelFeatureValidator:
    """
    Validates model feature input contracts across NCUM, NEPS, GFS fallback,
    and synthetic demo sources according to strict governance rules.
    """

    # Atmospheric & Geographic contract specifications
    CONTRACT_SPECIFICATION: Dict[str, FeatureClassification] = {
        # Core NWP Required Predictors
        "rainfall": FeatureClassification.REQUIRED,
        "u850": FeatureClassification.REQUIRED,
        "v850": FeatureClassification.REQUIRED,
        "temperature_850": FeatureClassification.REQUIRED,
        "relative_humidity_850": FeatureClassification.REQUIRED,
        "mslp": FeatureClassification.REQUIRED,
        "latitude": FeatureClassification.REQUIRED,
        "longitude": FeatureClassification.REQUIRED,
        "lead_time_hours": FeatureClassification.REQUIRED,

        # Upper air optional predictors
        "u700": FeatureClassification.OPTIONAL,
        "v700": FeatureClassification.OPTIONAL,
        "u500": FeatureClassification.OPTIONAL,
        "v500": FeatureClassification.OPTIONAL,
        "temperature_700": FeatureClassification.OPTIONAL,
        "temperature_500": FeatureClassification.OPTIONAL,
        "relative_humidity_700": FeatureClassification.OPTIONAL,
        "relative_humidity_500": FeatureClassification.OPTIONAL,
        "vertical_velocity": FeatureClassification.OPTIONAL,
        "cape_j_kg": FeatureClassification.OPTIONAL,
        "surface_pressure": FeatureClassification.OPTIONAL,

        # Static Terrain Predictors
        "elevation": FeatureClassification.STATIC,
        "slope": FeatureClassification.STATIC,
        "aspect": FeatureClassification.STATIC,
        "distance_to_coast": FeatureClassification.STATIC,

        # Derived Kinematic / Thermodynamic Proxies
        "wind_speed_850": FeatureClassification.DERIVED,
        "wind_direction_850": FeatureClassification.DERIVED,
        "vertical_wind_shear": FeatureClassification.DERIVED,
        "moisture_transport_proxy": FeatureClassification.DERIVED,
        "orographic_lift_index": FeatureClassification.DERIVED,
        "coastal_moisture_indicator": FeatureClassification.DERIVED,
        "pressure_gradient": FeatureClassification.DERIVED,

        # Source-specific items
        "ensemble_spread": FeatureClassification.OPTIONAL,  # NEPS specific
        "olr": FeatureClassification.OPTIONAL,
        "imd_gridded_obs": FeatureClassification.VERIFICATION_ONLY,
    }

    REQUIRED_METEOROLOGICAL_FIELDS: Set[str] = {
        "rainfall",
        "u850",
        "v850",
        "temperature_850",
        "relative_humidity_850",
        "mslp",
    }

    @classmethod
    def validate_record(
        cls,
        record: CanonicalMeteorologicalRecord,
        strict_required: bool = True,
    ) -> ModelInputValidationResult:
        """
        Validate a CanonicalMeteorologicalRecord against the operational model input contract.
        If mandatory features are missing (None), returns MODEL_INPUT_INCOMPLETE.
        """
        source = record.data_source or "UNKNOWN_SOURCE"
        forecast_time = record.timestamp or datetime.now(timezone.utc).isoformat()

        req_present: List[str] = []
        req_missing: List[str] = []
        opt_present: List[str] = []
        opt_missing: List[str] = []
        derived_avail: List[str] = []
        unavail: List[str] = []

        # Check required fields
        for field_name in cls.REQUIRED_METEOROLOGICAL_FIELDS:
            val = getattr(record, field_name, None)
            # Allow mslp or surface_pressure to satisfy surface pressure requirement
            if field_name == "mslp" and val is None and getattr(record, "surface_pressure", None) is not None:
                val = getattr(record, "surface_pressure")
            
            if val is not None:
                req_present.append(field_name)
            else:
                req_missing.append(field_name)

        # Check optional fields
        optional_fields = [
            "u700", "v700", "u500", "v500", "temperature_700", "temperature_500",
            "relative_humidity_700", "relative_humidity_500", "vertical_velocity",
            "cape_j_kg", "surface_pressure", "elevation", "slope", "aspect", "distance_to_coast"
        ]
        for field_name in optional_fields:
            val = getattr(record, field_name, None)
            if val is not None:
                opt_present.append(field_name)
            else:
                opt_missing.append(field_name)

        # Check ensemble spread capability
        ens_spread = getattr(record, "ensemble_spread", None)
        ens_std = getattr(record, "ensemble_std", None)
        if ens_spread is not None or ens_std is not None:
            opt_present.append("ensemble_spread")
        else:
            unavail.append("ensemble_spread")

        # Derived features check
        if record.u850 is not None and record.v850 is not None:
            derived_avail.extend(["wind_speed_850", "wind_direction_850", "moisture_transport_proxy"])
        if record.u850 is not None and record.v850 is not None and record.u500 is not None and record.v500 is not None:
            derived_avail.append("vertical_wind_shear")
        else:
            unavail.append("vertical_wind_shear")

        if record.slope is not None and record.elevation is not None:
            derived_avail.append("orographic_lift_index")
        else:
            unavail.append("orographic_lift_index")

        if strict_required and len(req_missing) > 0:
            msg = f"Model input feature contract violation: missing mandatory fields {req_missing} for source '{source}'."
            logger.warning(msg)
            return ModelInputValidationResult(
                status=FeatureValidationStatus.MODEL_INPUT_INCOMPLETE,
                is_inference_ready=False,
                source=source,
                forecast_time=forecast_time,
                required_features_present=req_present,
                missing_features=req_missing,
                optional_features_present=opt_present,
                optional_features_missing=opt_missing,
                derived_features_available=derived_avail,
                unavailable_features=unavail,
                error_message=msg,
            )

        return ModelInputValidationResult(
            status=FeatureValidationStatus.VALID,
            is_inference_ready=True,
            source=source,
            forecast_time=forecast_time,
            required_features_present=req_present,
            missing_features=[],
            optional_features_present=opt_present,
            optional_features_missing=opt_missing,
            derived_features_available=derived_avail,
            unavailable_features=unavail,
            error_message=None,
        )
