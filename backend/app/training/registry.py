"""
Model Registry for Retrained & Experimental Meteorological Models (PS26080).
Manages lifecycle governance (EXPERIMENTAL -> VALIDATED -> FROZEN -> DEPRECATED)
and strictly prevents automated replacement of production dashboard models.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("rainfall_backend.training.registry")


class ModelLifecycleStatus(str, Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    VALIDATED = "VALIDATED"
    FROZEN = "FROZEN"
    DEPRECATED = "DEPRECATED"


class TrainingRegistryEntry(BaseModel):
    """Metadata record for an artifact in the model registry."""
    model_id: str = Field(..., description="Unique model identifier")
    model_type: str = Field(..., description="Model architecture type")
    version: str = Field(..., description="Version string")
    dataset_id: str = Field(..., description="Training dataset identifier")
    feature_version: str = Field("MeteorologicalFeatureSchema_v2.1", description="Feature schema version")
    training_period: str = Field(..., description="Historical training period")
    validation_period: str = Field(..., description="Validation tuning period")
    test_period: str = Field(..., description="Held-out evaluation period")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Held-out verification metrics")
    artifact_path: str = Field(..., description="Filesystem directory where artifact is stored")
    provenance_status: str = Field(..., description="'REAL', 'DERIVED_FROM_REAL', 'SYNTHETIC_FIXTURE'")
    status: ModelLifecycleStatus = Field(ModelLifecycleStatus.EXPERIMENTAL, description="Lifecycle governance state")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active_dashboard_model: bool = Field(False, description="Whether this model powers the live dashboard")


class TrainingModelRegistry:
    """
    Registry tracking experimental, candidate, and validated model artifacts.
    """

    _REGISTRY: Dict[str, TrainingRegistryEntry] = {
        "SPATIAL_RESIDUAL_BASELINE_V1:SpatialBaseline_v1.0": TrainingRegistryEntry(
            model_id="SPATIAL_RESIDUAL_BASELINE_V1",
            model_type="Neighborhood_Augmented_Spatial_Residual_Regressor",
            version="SpatialBaseline_v1.0",
            dataset_id="IMD_ERA5_JJAS_2010_2023_0.25deg",
            feature_version="SpatialMeteorologicalSchema_v1.0",
            training_period="2010–2019 JJAS",
            validation_period="2020–2021 JJAS",
            test_period="2022–2023 JJAS",
            metrics={"rmse_mm": 13.8, "csi_64_5": 0.69, "ets_64_5": 0.62, "fss_50km": 0.76},
            artifact_path="backend/app/postprocessing/saved_models/spatial_baseline_v1",
            provenance_status="DERIVED_FROM_REAL",
            status=ModelLifecycleStatus.EXPERIMENTAL,
            is_active_dashboard_model=False,
        ),
        "SPATIAL_REGIME_AWARE_V1:SpatialRegimeConv_v1.0": TrainingRegistryEntry(
            model_id="SPATIAL_REGIME_AWARE_V1",
            model_type="Compact_Convolutional_Spatial_Regime_UNet",
            version="SpatialRegimeConv_v1.0",
            dataset_id="IMD_ERA5_JJAS_2010_2023_0.25deg",
            feature_version="SpatialMeteorologicalSchema_v1.0",
            training_period="2010–2019 JJAS",
            validation_period="2020–2021 JJAS",
            test_period="2022–2023 JJAS",
            metrics={"rmse_mm": 9.8, "csi_64_5": 0.83, "ets_64_5": 0.77, "fss_50km": 0.91},
            artifact_path="backend/app/postprocessing/saved_models/spatial_regime_aware_v1",
            provenance_status="DERIVED_FROM_REAL",
            status=ModelLifecycleStatus.EXPERIMENTAL,
            is_active_dashboard_model=False,
        ),
        "SPATIAL_REGIME_TEMPORAL_V1:SpatialRegimeTemporal_v1.0": TrainingRegistryEntry(
            model_id="SPATIAL_REGIME_TEMPORAL_V1",
            model_type="Temporal_Context_Spatial_Regime_Processor",
            version="SpatialRegimeTemporal_v1.0",
            dataset_id="IMD_ERA5_JJAS_2010_2023_0.25deg",
            feature_version="SpatialMeteorologicalSchema_v1.0",
            training_period="2010–2019 JJAS",
            validation_period="2020–2021 JJAS",
            test_period="2022–2023 JJAS",
            metrics={"rmse_mm": 9.4, "csi_64_5": 0.85, "ets_64_5": 0.79, "fss_50km": 0.93},
            artifact_path="backend/app/postprocessing/saved_models/spatial_regime_temporal_v1",
            provenance_status="DERIVED_FROM_REAL",
            status=ModelLifecycleStatus.EXPERIMENTAL,
            is_active_dashboard_model=False,
        ),
    }

    @classmethod
    def register_artifact(
        cls,
        entry: TrainingRegistryEntry,
    ) -> None:
        """
        Register a new model artifact. Default state is strictly EXPERIMENTAL.
        """
        key = f"{entry.model_id}:{entry.version}"
        # Ensure new models do not automatically replace production dashboard models
        entry.is_active_dashboard_model = False
        cls._REGISTRY[key] = entry
        logger.info("Registered model artifact '%s' with status=%s", key, entry.status)

    @classmethod
    def get_all_entries(cls) -> List[TrainingRegistryEntry]:
        """Return all registered model artifacts."""
        return list(cls._REGISTRY.values())

    @classmethod
    def get_entry(cls, model_id: str, version: str) -> Optional[TrainingRegistryEntry]:
        """Lookup model artifact by model_id and version."""
        key = f"{model_id}:{version}"
        return cls._REGISTRY.get(key)

