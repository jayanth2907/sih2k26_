"""
Unit & Integration Tests for PS26080 Post-Processing Models & API Endpoints.
Tests:
- Empirical Quantile Mapping Model (fitting, CDF mapping, extreme extrapolation)
- Global ML Correction Model
- Regime-Aware ML Correction Model (soft mixture of experts conditioning)
- Model Comparison Engine
- Model Registry catalogue
- REST API endpoints (/models, /correct, /compare, /verification)
"""

import numpy as np
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.postprocessing.base import PostProcessingInput
from backend.app.postprocessing.comparison import ModelComparisonEngine
from backend.app.postprocessing.datasets import DatasetGenerator
from backend.app.postprocessing.global_ml import GlobalMLCorrectionModel
from backend.app.postprocessing.model_registry import PostProcessingModelRegistry
from backend.app.postprocessing.quantile_mapping import EmpiricalQuantileMappingModel
from backend.app.postprocessing.regime_aware_ml import RegimeAwareMLCorrectionModel


@pytest.fixture
def test_dataset():
    """Generate small train dataset for fast unit test fitting."""
    return DatasetGenerator.generate_synthetic_dataset(split="train", seed=42)


@pytest.fixture
def sample_input():
    """Standard PostProcessingInput sample fixture."""
    return PostProcessingInput(
        raw_nwp_rainfall=55.0,
        lead_time_hours=24,
        latitude=17.92,
        longitude=73.65,
        month=7,
        day_of_year=205,
        wind_speed_850=18.5,
        wind_direction_850=255.0,
        elevation=1353.0,
        slope=8.4,
        distance_to_coast=55.0,
        orographic_lift_index=1.36,
        primary_regime="OROGRAPHIC_RAINFALL",
        regime_confidence=0.88,
        regime_probabilities={
            "ACTIVE_MONSOON": 0.45,
            "BREAK_MONSOON": 0.02,
            "MONSOON_LOW_LPS": 0.10,
            "COASTAL_CONVERGENCE": 0.25,
            "OROGRAPHIC_RAINFALL": 0.85,
            "WESTERN_DISTURBANCE": 0.02,
            "NEUTRAL": 0.05,
        },
        is_demo=True,
    )


def test_empirical_quantile_mapping_fitting_and_predict(test_dataset, sample_input):
    """Test EQM non-parametric CDF calibration and extrapolation."""
    eqm = EmpiricalQuantileMappingModel()
    eqm.fit(test_dataset.X, test_dataset.y_residual, raw_nwp=test_dataset.raw_nwp, observed=test_dataset.observed)
    assert eqm.is_fitted is True

    out = eqm.predict(sample_input)
    assert out.model_id == "quantile_mapping"
    assert out.corrected_rainfall_24h_mm >= 0.0
    assert out.rainfall_p10_mm <= out.rainfall_p50_mm <= out.rainfall_p90_mm

    # Dry-day test
    assert eqm.predict_corrected_scalar(0.0) == 0.0
    assert eqm.predict_corrected_scalar(0.05) == 0.0

    # Extreme extrapolation test
    extreme_val = 400.0
    corr_extreme = eqm.predict_corrected_scalar(extreme_val)
    assert corr_extreme > 0.0


def test_global_ml_model_fitting_and_predict(test_dataset, sample_input):
    """Test Global ML HistGradientBoosting model fitting and inference."""
    model = GlobalMLCorrectionModel()
    model.fit(test_dataset.X, test_dataset.y_residual)
    assert model.is_fitted is True

    out = model.predict(sample_input)
    assert out.model_id == "global_ml"
    assert out.corrected_rainfall_24h_mm >= 0.0
    assert out.rainfall_p10_mm <= out.rainfall_p50_mm <= out.rainfall_p90_mm


def test_regime_aware_ml_soft_conditioning(test_dataset, sample_input):
    """Test Regime-Aware ML soft-conditioning and mixture of experts."""
    model = RegimeAwareMLCorrectionModel()
    model.fit(test_dataset.X, test_dataset.y_residual, regimes=test_dataset.regimes)
    assert model.is_fitted is True

    out = model.predict(sample_input)
    assert out.model_id == "regime_aware_ml"
    assert out.corrected_rainfall_24h_mm >= 0.0
    assert out.rainfall_p10_mm <= out.rainfall_p50_mm <= out.rainfall_p90_mm
    assert out.heavy_rain_prob_ge_64_5mm >= out.very_heavy_rain_prob_ge_115_6mm >= out.extreme_rain_prob_ge_204_5mm


def test_model_comparison_engine(test_dataset, sample_input):
    """Test ModelComparisonEngine evaluating all 4 approaches side-by-side."""
    eqm = EmpiricalQuantileMappingModel().fit(test_dataset.X, test_dataset.y_residual, raw_nwp=test_dataset.raw_nwp, observed=test_dataset.observed)
    global_ml = GlobalMLCorrectionModel().fit(test_dataset.X, test_dataset.y_residual)
    regime_ml = RegimeAwareMLCorrectionModel().fit(test_dataset.X, test_dataset.y_residual, regimes=test_dataset.regimes)

    engine = ModelComparisonEngine(eqm_model=eqm, global_ml_model=global_ml, regime_ml_model=regime_ml)
    summary = engine.compare_sample(sample_input)

    assert summary.raw_nwp is not None
    assert summary.quantile_mapping is not None
    assert summary.global_ml is not None
    assert summary.regime_aware_ml is not None
    assert summary.skill_gain_vs_raw_pct > 0.0
    assert summary.skill_gain_vs_global_pct > 0.0


def test_model_registry():
    """Verify PostProcessingModelRegistry entries and query methods."""
    models = PostProcessingModelRegistry.get_all_models()
    assert len(models) >= 4

    ids = {m.model_id for m in models}
    assert {"raw_nwp", "quantile_mapping", "global_ml", "regime_aware_ml"}.issubset(ids)

    regime_entry = PostProcessingModelRegistry.get_model_entry("regime_aware_ml")
    assert regime_entry is not None
    assert regime_entry.feature_schema_version == "MeteorologicalFeatureSchema_v2.0"
    assert regime_entry.regime_schema_version == "SASM_RegimeEngine_v2.0"


def test_api_postprocess_models_endpoint():
    """Test GET /api/v1/postprocess/models."""
    client = TestClient(app)
    response = client.get("/api/v1/postprocess/models")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 4
    model_ids = [m["model_id"] for m in data]
    assert "regime_aware_ml" in model_ids


def test_api_postprocess_correct_endpoint(sample_input):
    """Test POST /api/v1/postprocess/correct."""
    client = TestClient(app)
    payload = sample_input.model_dump()
    response = client.post("/api/v1/postprocess/correct?model_id=regime_aware_ml", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == "regime_aware_ml"
    assert "corrected_rainfall_24h_mm" in data
    assert "heavy_rain_prob_ge_64_5mm" in data
    assert data["corrected_rainfall_24h_mm"] >= 0.0


def test_api_postprocess_compare_endpoint(sample_input):
    """Test POST and GET /api/v1/postprocess/compare."""
    client = TestClient(app)
    
    # POST with sample payload
    payload = sample_input.model_dump()
    resp_post = client.post("/api/v1/postprocess/compare", json=payload)
    assert resp_post.status_code == 200
    data_post = resp_post.json()
    assert "raw_nwp" in data_post
    assert "regime_aware_ml" in data_post

    # GET default comparison
    resp_get = client.get("/api/v1/postprocess/compare?raw_rainfall_mm=65.0")
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert data_get["raw_nwp"]["raw_rainfall_24h_mm"] == 65.0
    assert "regime_aware_ml" in data_get
    assert data_get["regime_aware_ml"]["corrected_rainfall_24h_mm"] > 0.0
    assert data_get["skill_gain_vs_raw_pct"] > 0.0


def test_api_postprocess_verification_endpoint():
    """Test GET /api/v1/postprocess/verification."""
    client = TestClient(app)
    response = client.get("/api/v1/postprocess/verification")
    assert response.status_code == 200
    data = response.json()
    assert "benchmark_metrics" in data
    assert "regime_aware_ml" in data["benchmark_metrics"]
    assert "regime_skill_gain_pct" in data
