"""
PS26080 AI Post-Processing Package for Monsoon Rainfall Forecasts.
Ministry of Earth Sciences (MoES) / NCMRWF.
"""

from backend.app.postprocessing.base import (
    BasePostProcessingModel,
    PostProcessingInput,
    PostProcessingOutput,
)
from backend.app.postprocessing.comparison import (
    ForecastComparisonSummary,
    ModelComparisonEngine,
)
from backend.app.postprocessing.datasets import (
    DatasetGenerator,
    PostProcessingDataset,
    extract_feature_vector,
)
from backend.app.postprocessing.global_ml import GlobalMLCorrectionModel
from backend.app.postprocessing.heavy_rain import HeavyRainfallCalibrator, RainfallProbabilityPackage
from backend.app.postprocessing.inference import PostProcessingInferenceEngine
from backend.app.postprocessing.metrics import (
    ContingencyTable2x2,
    PostProcessingVerificationEngine,
    VerificationReport,
)
from backend.app.postprocessing.model_registry import (
    ModelRegistryEntry,
    PostProcessingModelRegistry,
)
from backend.app.postprocessing.quantile_mapping import EmpiricalQuantileMappingModel
from backend.app.postprocessing.regime_aware_ml import RegimeAwareMLCorrectionModel
from backend.app.postprocessing.uncertainty import UncertaintyBounds, UncertaintyQuantifier

__all__ = [
    "BasePostProcessingModel",
    "PostProcessingInput",
    "PostProcessingOutput",
    "ForecastComparisonSummary",
    "ModelComparisonEngine",
    "DatasetGenerator",
    "PostProcessingDataset",
    "extract_feature_vector",
    "GlobalMLCorrectionModel",
    "HeavyRainfallCalibrator",
    "RainfallProbabilityPackage",
    "PostProcessingInferenceEngine",
    "ContingencyTable2x2",
    "PostProcessingVerificationEngine",
    "VerificationReport",
    "ModelRegistryEntry",
    "PostProcessingModelRegistry",
    "EmpiricalQuantileMappingModel",
    "RegimeAwareMLCorrectionModel",
    "UncertaintyBounds",
    "UncertaintyQuantifier",
]
