"""
Model Registry for PS26080 Post-Processing Models.
Tracks model architecture metadata, training/validation periods, feature schema versions,
and test verification metrics for governance and auditability.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelRegistryEntry(BaseModel):
    """Metadata record for a registered post-processing model."""
    model_id: str
    model_name: str
    version: str
    architecture: str
    training_period: str = "2018–2022 (Historical Monsoon Seasons JJAS)"
    validation_period: str = "2023 (Monsoon Season JJAS)"
    test_period: str = "2024–2025 (Held-out Prospective Evaluation JJAS)"
    feature_schema_version: str = "MeteorologicalFeatureSchema_v2.0"
    regime_schema_version: str = "SASM_RegimeEngine_v2.0"
    data_sources: List[str] = Field(
        default_factory=lambda: [
            "NCMRWF_NCUM",
            "NCMRWF_NEPS",
            "ECMWF_ERA5",
            "IMD_GRIDDED_RAINFALL",
            "NASA_GPM_IMERG",
            "SRTM_DEM_TOPOGRAPHY",
        ]
    )
    test_metrics: Dict[str, float] = Field(default_factory=dict)
    is_operational_ncmrwf: bool = False
    is_demo: bool = True
    registered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PostProcessingModelRegistry:
    """
    Registry catalogue for PS26080 post-processing models.
    """

    _REGISTRY: Dict[str, ModelRegistryEntry] = {
        "raw_nwp": ModelRegistryEntry(
            model_id="raw_nwp",
            model_name="Raw NWP Forecast Baseline",
            version="NCUM_GFS_Raw_v1.0",
            architecture="Deterministic Numerical Weather Prediction Baseline",
            test_metrics={"rmse_mm": 24.8, "ets": 0.38, "csi": 0.44, "pod": 0.62, "far": 0.38, "fss_50km": 0.52},
            is_operational_ncmrwf=False,
            is_demo=True,
        ),
        "quantile_mapping": ModelRegistryEntry(
            model_id="quantile_mapping",
            model_name="Empirical Quantile Mapping (EQM)",
            version="EQM_v1.0_Empirical",
            architecture="Non-Parametric Cumulative Distribution Function Calibration",
            test_metrics={"rmse_mm": 19.2, "ets": 0.46, "csi": 0.53, "pod": 0.71, "far": 0.32, "fss_50km": 0.61},
            is_operational_ncmrwf=False,
            is_demo=True,
        ),
        "global_ml": ModelRegistryEntry(
            model_id="global_ml",
            model_name="Global ML Post-Processing (Standard Non-Regime)",
            version="GlobalML_v1.0_HistGBM",
            architecture="Stationary Histogram-based Gradient Boosting Regressor",
            test_metrics={"rmse_mm": 15.6, "ets": 0.58, "csi": 0.64, "pod": 0.80, "far": 0.24, "fss_50km": 0.73},
            is_operational_ncmrwf=False,
            is_demo=True,
        ),
        "regime_aware_ml": ModelRegistryEntry(
            model_id="regime_aware_ml",
            model_name="Regime-Aware AI Post-Processing (Target MoES/NCMRWF)",
            version="RegimeML_v2.0_SoftConditionedMoE",
            architecture="Soft-Conditioned Mixture of Experts + Regime Interaction Meta-Regressor",
            test_metrics={"rmse_mm": 10.4, "ets": 0.74, "csi": 0.81, "pod": 0.92, "far": 0.14, "fss_50km": 0.89},
            is_operational_ncmrwf=False,
            is_demo=True,
        ),
    }

    @classmethod
    def get_all_models(cls) -> List[ModelRegistryEntry]:
        """Return all registered models."""
        return list(cls._REGISTRY.values())

    @classmethod
    def get_model_entry(cls, model_id: str) -> Optional[ModelRegistryEntry]:
        """Lookup model entry by identifier."""
        return cls._REGISTRY.get(model_id)

    @classmethod
    def register_model(cls, entry: ModelRegistryEntry) -> None:
        """Register or update model entry."""
        cls._REGISTRY[entry.model_id] = entry
