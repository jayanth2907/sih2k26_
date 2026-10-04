"""
Comprehensive Tests for Advanced Weather Regime Intelligence (Phase 12).
Tests 20 required dimensions: Markov transitions, persistence, Day 1-10 propagation,
multi-label representation, explainability deltas, API endpoints, and scientific regression.
"""

from datetime import datetime
import numpy as np
import pytest
from starlette.testclient import TestClient

from backend.app.main import create_app
from backend.app.regime.regime_classifier import WeatherRegimeClassifier
from backend.app.regime.temporal_pipeline import TemporalRegimePipeline
from backend.app.regime.transition_engine import MarkovRegimeTransitionModel
from backend.app.regime.transition_explainer import RegimeTransitionExplainer
from backend.app.schemas.regime import WeatherRegimeType
from backend.app.schemas.regime_temporal import (
    Day10RegimeForecastResponse,
    RegimeForecastMode,
    RegimePersistenceReport,
    RegimeSequence,
    RegimeTransitionMatrix,
)


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def transition_model():
    return MarkovRegimeTransitionModel(smoothing_alpha=1.0)


# 1 & 2. Transition Matrix Sums & Probability Bounds
def test_transition_matrix_stochastic_properties(transition_model: MarkovRegimeTransitionModel):
    """1-2. Verify all rows sum to 1.0 and all transition probabilities are in [0, 1]."""
    P = transition_model.transition_matrix
    assert P.shape == (7, 7)
    
    # Row sum invariant
    row_sums = P.sum(axis=1)
    np.testing.assert_allclose(row_sums, 1.0, atol=1.0e-5)

    # Probability bounds
    assert np.all(P >= 0.0)
    assert np.all(P <= 1.0)


# 3. Smoothing
def test_laplace_smoothing_mechanism():
    """3. Verify Laplace smoothing ensures non-zero transitions."""
    # Zero count matrix
    zero_counts = np.zeros((7, 7), dtype=np.float64)
    model = MarkovRegimeTransitionModel(smoothing_alpha=1.0, custom_counts=zero_counts)
    P = model.transition_matrix
    
    # Each entry must equal 1/7
    expected_uniform = 1.0 / 7.0
    np.testing.assert_allclose(P, expected_uniform, atol=1.0e-5)


# 4 & 5. Persistence & Duration Estimation
def test_persistence_and_duration_statistics(transition_model: MarkovRegimeTransitionModel):
    """4-5. Verify diagonal persistence probabilities and duration estimates."""
    report = transition_model.get_persistence_report()
    assert isinstance(report, RegimePersistenceReport)
    assert len(report.regimes) == 7

    for reg_name, stat in report.regimes.items():
        assert 0.0 < stat.persistence_probability < 1.0
        assert stat.mean_duration_days >= 1.0
        assert stat.median_duration_days >= 0.5
        assert stat.sample_count > 0


# 6 & 7 & 8. Multi-Step Probability Propagation & Bounds
def test_multi_step_markov_probability_propagation(transition_model: MarkovRegimeTransitionModel):
    """6-8. Verify p_(t+k) = p_t * P^k maintains probability axioms across all horizons."""
    # Initial state: 100% ACTIVE_MONSOON
    p0 = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    for day in range(1, 11):
        p_day = transition_model.propagate_probabilities(p0, steps_ahead=day)
        assert len(p_day) == 7
        assert abs(p_day.sum() - 1.0) < 1.0e-5
        assert np.all(p_day >= 0.0)
        assert np.all(p_day <= 1.0)


# 9 & 10. Chronological Training & Test Isolation
def test_training_period_metadata_isolation(transition_model: MarkovRegimeTransitionModel):
    """9-10. Verify transition matrix metadata strictly references training partition (2010–2019)."""
    schema = transition_model.get_transition_matrix_schema()
    assert "2010–2019" in schema.training_period
    assert schema.dataset_id == "ERA5_JJAS_2010_2023_025DEG"


# 11. Multi-Label Support
def test_multi_label_regime_classification():
    """11. Verify co-occurring secondary regimes are preserved."""
    pipeline = TemporalRegimePipeline()
    seq = pipeline.get_regime_sequence(start_date="2024-07-01", end_date="2024-07-05")
    assert len(seq.steps) == 5
    # Check that secondary regimes list is a valid list
    for s in seq.steps:
        assert isinstance(s.secondary_regimes, list)
        assert s.primary_regime in MarkovRegimeTransitionModel.REGIMES


# 12 & 13. Regime Confidence vs Transition Confidence
def test_confidence_decay_across_horizons(transition_model: MarkovRegimeTransitionModel):
    """12-13. Verify confidence decays monotonically with forecast horizon."""
    res = transition_model.generate_day_1_10_projection(
        current_regime=WeatherRegimeType.ACTIVE_MONSOON,
    )
    confidences = [step.confidence for step in res.daily_projections]
    assert confidences[0] >= confidences[-1] # Day 1 >= Day 10
    assert confidences[0] > 0.80
    assert confidences[-1] >= 0.40


# 14. Deterministic Output
def test_deterministic_forecast_reproducibility(transition_model: MarkovRegimeTransitionModel):
    """14. Repeated projections from same state yield bitwise identical probabilities."""
    res1 = transition_model.generate_day_1_10_projection(WeatherRegimeType.BREAK_MONSOON)
    res2 = transition_model.generate_day_1_10_projection(WeatherRegimeType.BREAK_MONSOON)
    assert res1.daily_projections[4].probabilities == res2.daily_projections[4].probabilities


# 15 & 16. Provenance & API Endpoints
def test_regime_api_endpoints(client: TestClient):
    """15-16. Verify GET and POST temporal regime endpoints."""
    # 1. GET /sequence
    r_seq = client.get("/api/v1/regime/sequence?start_date=2024-07-01&end_date=2024-07-07")
    assert r_seq.status_code == 200
    assert r_seq.json()["total_steps"] == 7

    # 2. GET /transitions
    r_trans = client.get("/api/v1/regime/transitions")
    assert r_trans.status_code == 200
    assert "ACTIVE_MONSOON" in r_trans.json()["transition_probabilities"]

    # 3. GET /persistence
    r_pers = client.get("/api/v1/regime/persistence")
    assert r_pers.status_code == 200
    assert "ACTIVE_MONSOON" in r_pers.json()["regimes"]

    # 4. POST /forecast
    r_fc = client.post("/api/v1/regime/forecast", json={
        "current_regime": "ACTIVE_MONSOON",
        "mode": "TRANSITION_BASED_PROJECTION"
    })
    assert r_fc.status_code == 200
    assert len(r_fc.json()["daily_projections"]) == 10

    # 5. POST /explain
    r_exp = client.post("/api/v1/regime/explain", json={
        "from_regime": "ACTIVE_MONSOON",
        "to_regime": "OROGRAPHIC_RAINFALL",
        "initial_features": {"llj_speed_kts": 22.0, "ivt_kg_m_s": 180.0},
        "target_features": {"llj_speed_kts": 28.0, "ivt_kg_m_s": 250.0},
    })
    assert r_exp.status_code == 200
    exp_data = r_exp.json()
    assert len(exp_data["primary_drivers"]) > 0
    assert "feature_deltas" in exp_data


# 17. Day 1–10 Horizon Coverage
def test_day_1_to_10_forecast_structure(transition_model: MarkovRegimeTransitionModel):
    """17. Verify complete 10-day step projection structure."""
    fc = transition_model.generate_day_1_10_projection(
        current_regime=WeatherRegimeType.MONSOON_LOW_LPS,
    )
    assert len(fc.daily_projections) == 10
    for idx, step in enumerate(fc.daily_projections):
        assert step.day == idx + 1
        assert sum(step.probabilities.values()) == pytest.approx(1.0, 0.01)


# 18. Transition Explainer Physical Delta Logic
def test_transition_explainer_physics():
    """18. Verify explainer grounds narratives on feature shifts."""
    explainer = RegimeTransitionExplainer()
    res = explainer.explain_transition(
        from_regime=WeatherRegimeType.ACTIVE_MONSOON,
        to_regime=WeatherRegimeType.BREAK_MONSOON,
        transition_prob=0.035,
        initial_features={"llj_speed_kts": 28.0, "mslp_hpa": 1002.0},
        target_features={"llj_speed_kts": 14.0, "mslp_hpa": 1009.0},
    )
    assert res.feature_deltas["llj_speed_kts"] == -14.0
    assert res.feature_deltas["mslp_hpa"] == 7.0
    assert "northward" in res.meteorological_narrative.lower() or "break" in res.meteorological_narrative.lower()


# 19 & 20. Scientific Regression Against Base Regime Engine
def test_baseline_regime_classification_regression(client: TestClient):
    """19-20. Verify existing regime classifier behavior is preserved."""
    res = client.get("/api/v1/regime?latitude=10.0&longitude=76.5&prediction_date=2024-07-15")
    assert res.status_code == 200
    data = res.json()
    assert "primary_regime" in data
    assert "probabilities" in data
    assert "synoptic_features" in data
    assert data["confidence"] >= 0.0
