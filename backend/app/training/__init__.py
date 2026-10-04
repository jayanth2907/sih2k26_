"""
Real Historical Data and Reproducible Training Pipeline for PS26080.
"""

from backend.app.training.alignment import (
    DataAlignmentEngine,
    GridAlignmentMetadata,
    accumulate_rainfall,
    convert_precip_units,
    validate_accumulation_window,
)
from backend.app.training.dataset_builder import (
    DatasetManifest,
    HistoricalDatasetBuilder,
)
from backend.app.training.evaluator import (
    ModelEvaluationMetrics,
    RealDataTrainingEvaluation,
    TrainingEvaluator,
)
from backend.app.training.model_trainer import (
    ReproducibleModelTrainer,
    TrainedModelArtifact,
)
from backend.app.training.quality_control import (
    DatasetQCReport,
    TrainingQualityController,
)
from backend.app.training.registry import (
    ModelLifecycleStatus,
    TrainingModelRegistry,
    TrainingRegistryEntry,
)
from backend.app.training.splits import (
    ChronologicalSplitter,
    LeakageAuditReport,
)

__all__ = [
    "convert_precip_units",
    "validate_accumulation_window",
    "accumulate_rainfall",
    "GridAlignmentMetadata",
    "DataAlignmentEngine",
    "DatasetQCReport",
    "TrainingQualityController",
    "LeakageAuditReport",
    "ChronologicalSplitter",
    "DatasetManifest",
    "HistoricalDatasetBuilder",
    "TrainedModelArtifact",
    "ReproducibleModelTrainer",
    "ModelEvaluationMetrics",
    "RealDataTrainingEvaluation",
    "TrainingEvaluator",
    "ModelLifecycleStatus",
    "TrainingRegistryEntry",
    "TrainingModelRegistry",
]
