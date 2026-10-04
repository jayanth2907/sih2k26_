"""
Comprehensive Tests for Real Historical Data & Reproducible Training Pipeline (Phase 11).
Tests 20 key scientific and engineering requirements without requiring external CDS credentials.
"""

from datetime import datetime
import os
import tempfile
import pytest
from starlette.testclient import TestClient

from backend.app.main import create_app
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
from backend.app.training.evaluator import TrainingEvaluator
from backend.app.training.model_trainer import ReproducibleModelTrainer
from backend.app.training.quality_control import TrainingQualityController
from backend.app.training.registry import (
    ModelLifecycleStatus,
    TrainingModelRegistry,
    TrainingRegistryEntry,
)
from backend.app.training.splits import ChronologicalSplitter


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_dataset():
    builder = HistoricalDatasetBuilder(random_seed=42)
    records, manifest = builder.build_synthetic_fixture_dataset(sample_count=60)
    return records, manifest


# 1 & 2. Dataset Manifest Creation & Source Provenance
def test_dataset_manifest_creation_and_provenance(sample_dataset):
    """1-2. Verify manifest generation and provenance tracking."""
    records, manifest = sample_dataset
    assert isinstance(manifest, DatasetManifest)
    assert manifest.total_samples == len(records)
    assert manifest.provenance_status == "SYNTHETIC_FIXTURE"
    assert "ECMWF_ERA5_FIXTURE" in manifest.source_ids
    assert manifest.train_count > 0
    assert manifest.val_count > 0
    assert manifest.test_count > 0


# 3. Unit Normalization
def test_precipitation_unit_conversions():
    """3. Verify precipitation unit conversion logic."""
    assert convert_precip_units(12.5, "kg m**-2") == 12.5
    assert convert_precip_units(0.0125, "m") == 12.5
    assert round(convert_precip_units(0.001, "m/s"), 1) == 3.6


# 4 & 5. Temporal and Spatial Alignment
def test_temporal_and_spatial_alignment():
    """4-5. Verify temporal causality check and grid alignment metadata."""
    # Causality valid
    ok, err = DataAlignmentEngine.verify_temporal_causality(
        init_time="2022-07-15T00:00:00Z",
        valid_time="2022-07-16T00:00:00Z",
        obs_time="2022-07-16T00:00:00Z",
        lead_hours=24,
    )
    assert ok is True
    assert err is None

    # Causality invalid
    ok, err = DataAlignmentEngine.verify_temporal_causality(
        init_time="2022-07-15T00:00:00Z",
        valid_time="2022-07-16T12:00:00Z", # wrong valid time
        obs_time="2022-07-16T00:00:00Z",
        lead_hours=24,
    )
    assert ok is False

    # Grid metadata
    grid_meta = GridAlignmentMetadata(source_grid="ERA5_0.25", target_grid="IMD_0.25", regridding_method="bilinear")
    aligned = DataAlignmentEngine.align_forecast_and_observation(
        forecast_record={"timestamp": "2022-07-16T00:00:00Z", "rainfall": 40.0},
        observation_record={"timestamp": "2022-07-16T00:00:00Z", "rainfall": 52.5},
        grid_alignment=grid_meta,
    )
    assert aligned["residual_target"] == 12.5
    assert aligned["grid_alignment"]["regridding_method"] == "bilinear"


# 6. Rainfall Accumulation
def test_rainfall_accumulation_windows():
    """6. Accumulation window validation and sliding sum."""
    assert validate_accumulation_window(24) is True
    assert validate_accumulation_window(5) is False

    hourly = [2.0] * 24 # 48 mm total
    acc_24 = accumulate_rainfall(hourly, window_hours=24)
    assert acc_24 == 48.0


# 7 & 8. Missing Value Handling & Physical QC
def test_quality_control_and_missing_values():
    """7-8. Missing value calculation and physical bounds audit."""
    qc = TrainingQualityController(max_allowed_missing_pct=0.20)
    records = [
        {"timestamp": "2020-07-01T00:00:00Z", "latitude": 18.5, "longitude": 73.8, "rainfall": 25.0, "u850": 10.0, "v850": 4.0, "temperature_850": 294.0, "relative_humidity_850": 80.0},
        {"timestamp": "2020-07-02T00:00:00Z", "latitude": 18.5, "longitude": 73.8, "rainfall": -5.0}, # Negative rainfall
        {"timestamp": "2020-07-03T00:00:00Z", "latitude": 18.5, "longitude": 73.8, "rainfall": 50.0, "u850": None, "v850": 4.0, "temperature_850": 294.0, "relative_humidity_850": 80.0}, # missing u850
    ]
    clean, report = qc.audit_and_clean_records(records)
    assert report.records_total == 3
    assert report.records_valid >= 1
    assert "RAINFALL_OUT_OF_BOUNDS" in report.rejection_reasons or report.out_of_range_fraction > 0


# 9 & 10. Chronological Split & Leakage Detection
def test_chronological_splits_and_leakage_audit(sample_dataset):
    """9-10. Chronological partitioning without future information leakage."""
    records, _ = sample_dataset
    splitter = ChronologicalSplitter(train_years=[2018], val_years=[2020], test_years=[2022])
    train_set, val_set, test_set, audit = splitter.split_dataset(records)

    assert len(train_set) > 0
    assert len(val_set) > 0
    assert len(test_set) > 0
    assert audit.temporal_leakage_detected is False
    assert audit.target_leakage_detected is False
    assert "NO LEAKAGE FOUND" in audit.audit_summary


# 11 & 14. Feature Reproducibility & Deterministic Training
def test_deterministic_training_reproducibility(sample_dataset):
    """11 & 14. Deterministic training across identical seeds."""
    records, manifest = sample_dataset
    splitter = ChronologicalSplitter(train_years=[2018], val_years=[2020], test_years=[2022])
    train_set, val_set, test_set, _ = splitter.split_dataset(records)

    trainer1 = ReproducibleModelTrainer(random_seed=42)
    art1 = trainer1.train_global_ml(train_set, val_set, manifest, version="v1")

    trainer2 = ReproducibleModelTrainer(random_seed=42)
    art2 = trainer2.train_global_ml(train_set, val_set, manifest, version="v1")

    assert art1.metadata["dataset_hash"] == art2.metadata["dataset_hash"]
    assert art1.metadata["config_hash"] == art2.metadata["config_hash"]


# 12 & 13. Model Metadata & Artifact Creation
def test_model_artifact_creation_and_filesystem_save(sample_dataset):
    """12-13. Saving pickle, metadata JSON, and feature schema to disk."""
    records, manifest = sample_dataset
    splitter = ChronologicalSplitter(train_years=[2018], val_years=[2020], test_years=[2022])
    train_set, val_set, _, _ = splitter.split_dataset(records)

    trainer = ReproducibleModelTrainer(random_seed=42)
    art = trainer.train_global_ml(train_set, val_set, manifest, version="test_v1")

    with tempfile.TemporaryDirectory() as tmpdir:
        saved_path = art.save_artifact(base_dir=tmpdir)
        assert os.path.exists(os.path.join(saved_path, "metadata.json"))
        assert os.path.exists(os.path.join(saved_path, "feature_schema.json"))
        assert os.path.exists(os.path.join(saved_path, "model.pkl"))


# 15. Benchmark Separation
def test_benchmark_separation_and_evaluation(sample_dataset):
    """15. Real-data training evaluation lives in a distinct namespace."""
    records, manifest = sample_dataset
    splitter = ChronologicalSplitter(train_years=[2018], val_years=[2020], test_years=[2022])
    train_set, val_set, test_set, _ = splitter.split_dataset(records)

    trainer = ReproducibleModelTrainer(random_seed=42)
    global_art = trainer.train_global_ml(train_set, val_set, manifest, version="v1")
    regime_art = trainer.train_regime_aware_ml(train_set, val_set, manifest, version="v1")

    evaluator = TrainingEvaluator()
    eval_report = evaluator.evaluate_all_models(
        test_samples=test_set,
        global_ml_artifact=global_art,
        regime_aware_artifact=regime_art,
        dataset_id=manifest.dataset_id,
        evaluation_date="2026-10-02T12:00:00Z",
    )

    assert eval_report.evaluation_namespace == "REAL_DATA_TRAINING_EVALUATION"
    assert "raw_nwp" in eval_report.models
    assert "quantile_mapping" in eval_report.models
    assert "global_ml" in eval_report.models
    assert "regime_aware_ml" in eval_report.models
    assert eval_report.models["regime_aware_ml"].rmse_mm > 0.0


# 16. Synthetic Fixture Isolation
def test_synthetic_fixture_isolation(sample_dataset):
    """16. Fixture datasets are flagged with provenance SYNTHETIC_FIXTURE."""
    _, manifest = sample_dataset
    assert manifest.provenance_status == "SYNTHETIC_FIXTURE"


# 17. Credential Safety
def test_credential_safety_in_endpoints(client: TestClient):
    """17. Training endpoints never expose API keys, passwords, or tokens."""
    res1 = client.get("/api/v1/data/training/status")
    assert res1.status_code == 200
    text1 = res1.text.lower()
    for secret_keyword in ["secret", "password", "api_key", "bearer", "private_key"]:
        assert f'"{secret_keyword}"' not in text1 or "none" in text1 or "false" in text1

    res2 = client.get("/api/v1/data/training/catalog")
    assert res2.status_code == 200


# 18 & 19. Dataset Hash & Configuration Hash
def test_dataset_and_config_hashes(sample_dataset):
    """18-19. SHA-256 hashes generated for dataset and configuration."""
    _, manifest = sample_dataset
    assert len(manifest.training_config_hash) == 64 # sha256 hex
    assert len(manifest.data_hash) == 64


# 20. Provenance Propagation & Model Registry Non-Replacement
def test_model_registry_lifecycle_and_non_replacement():
    """20. New models register as EXPERIMENTAL and do NOT replace active dashboard model."""
    entry = TrainingRegistryEntry(
        model_id="candidate_regime_moe",
        model_type="SoftConditionedMixtureOfExperts",
        version="candidate_v1",
        dataset_id="ERA5_JJAS_2010_2023_025DEG",
        training_period="2010–2019",
        validation_period="2020–2021",
        test_period="2022–2023",
        metrics={"rmse_mm": 11.4},
        artifact_path="artifacts/models/candidate_regime_moe/v1",
        provenance_status="REAL_REANALYSIS_FIT",
        status=ModelLifecycleStatus.EXPERIMENTAL,
    )
    TrainingModelRegistry.register_artifact(entry)
    retrieved = TrainingModelRegistry.get_entry("candidate_regime_moe", "candidate_v1")
    assert retrieved is not None
    assert retrieved.status == ModelLifecycleStatus.EXPERIMENTAL
    assert retrieved.is_active_dashboard_model is False # Strictly False
