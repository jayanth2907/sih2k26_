"""
Unit and Integration Tests for Phase 6: Regime-Stratified Verification.

Validates:
1. Verification endpoint returns HTTP 200.
2. Overall held-out benchmark preservation (Raw NWP, EQM, Global ML, Regime-Aware AI).
3. Regime-stratified structure and scorecard completeness across all 7 supported regimes.
4. Non-negative sample counts matching held-out evaluation dataset (N=800).
5. Defensible handling of insufficient / zero sample regimes without fabricated metrics.
6. 64.5mm heavy rainfall threshold consistency.
7. Absence of data leakage (held-out chronological period 2024-2025).
8. Provenance metadata tracking.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.postprocessing.inference import PostProcessingInferenceEngine
from backend.app.schemas.postprocess import VerificationResponse


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


def test_verification_endpoint_status_200(client):
    """Ensure GET /api/v1/postprocess/verification responds with HTTP 200."""
    response = client.get("/api/v1/postprocess/verification")
    assert response.status_code == 200
    data = response.json()
    assert "benchmark_metrics" in data
    assert "regime_stratified" in data
    assert data["threshold_mm"] == 64.5


def test_overall_benchmark_preservation():
    """Verify that overall benchmark metrics are strictly preserved without drift."""
    engine = PostProcessingInferenceEngine.get_instance()
    res: VerificationResponse = engine.get_verification_benchmarks()

    benchmarks = res.benchmark_metrics
    assert "raw_nwp" in benchmarks
    assert "quantile_mapping" in benchmarks
    assert "global_ml" in benchmarks
    assert "regime_aware_ml" in benchmarks

    # Raw NWP
    raw = benchmarks["raw_nwp"]
    assert raw.rmse_mm == pytest.approx(24.83, abs=0.01)
    assert raw.mae_mm == pytest.approx(19.06, abs=0.01)
    assert raw.mean_bias_mm == pytest.approx(-17.08, abs=0.01)
    assert raw.csi == pytest.approx(0.291, abs=0.005)
    assert raw.ets == pytest.approx(0.250, abs=0.005)
    assert raw.fss_50km == pytest.approx(0.502, abs=0.005)

    # EQM
    eqm = benchmarks["quantile_mapping"]
    assert eqm.rmse_mm == pytest.approx(12.29, abs=0.01)
    assert eqm.mae_mm == pytest.approx(9.54, abs=0.01)
    assert eqm.mean_bias_mm == pytest.approx(-0.25, abs=0.01)
    assert eqm.csi == pytest.approx(0.759, abs=0.005)
    assert eqm.ets == pytest.approx(0.715, abs=0.005)
    assert eqm.fss_50km == pytest.approx(0.922, abs=0.005)

    # Global ML
    g_ml = benchmarks["global_ml"]
    assert g_ml.rmse_mm == pytest.approx(5.79, abs=0.01)
    assert g_ml.mae_mm == pytest.approx(3.47, abs=0.01)
    assert g_ml.mean_bias_mm == pytest.approx(0.33, abs=0.01)
    assert g_ml.csi == pytest.approx(0.854, abs=0.005)
    assert g_ml.ets == pytest.approx(0.825, abs=0.005)
    assert g_ml.fss_50km == pytest.approx(0.961, abs=0.005)

    # Regime-Aware AI
    r_ml = benchmarks["regime_aware_ml"]
    assert r_ml.rmse_mm == pytest.approx(5.68, abs=0.01)
    assert r_ml.mae_mm == pytest.approx(3.89, abs=0.01)
    assert r_ml.mean_bias_mm == pytest.approx(-0.12, abs=0.01)
    assert r_ml.csi == pytest.approx(0.869, abs=0.005)
    assert r_ml.ets == pytest.approx(0.843, abs=0.005)
    assert r_ml.fss_50km == pytest.approx(0.957, abs=0.005)


def test_regime_stratified_scorecard_completeness():
    """Verify that all 7 required weather regimes are present in regime_stratified."""
    engine = PostProcessingInferenceEngine.get_instance()
    res: VerificationResponse = engine.get_verification_benchmarks()

    expected_regimes = [
        "ACTIVE_MONSOON",
        "BREAK_MONSOON",
        "MONSOON_LOW_LPS",
        "COASTAL_CONVERGENCE",
        "OROGRAPHIC_RAINFALL",
        "WESTERN_DISTURBANCE",
        "NEUTRAL_TRANSITIONAL",
    ]

    for r_key in expected_regimes:
        assert r_key in res.regime_stratified, f"Regime {r_key} missing from regime_stratified"
        entry = res.regime_stratified[r_key]
        assert entry.regime_name == r_key
        assert entry.sample_count >= 0
        assert entry.heavy_event_count >= 0
        assert entry.fss_available is False  # Spatial FSS is only valid for continuous 2D grids, not sub-regimes


def test_regime_sample_counts_and_sum():
    """Verify exact held-out sample distribution sums to total (N=800)."""
    engine = PostProcessingInferenceEngine.get_instance()
    res: VerificationResponse = engine.get_verification_benchmarks()

    total_samples = sum(entry.sample_count for entry in res.regime_stratified.values())
    assert total_samples == 800
    assert res.sample_count == 800

    # Verify specific held-out counts from dataset generator
    assert res.regime_stratified["COASTAL_CONVERGENCE"].sample_count == 200
    assert res.regime_stratified["OROGRAPHIC_RAINFALL"].sample_count == 200
    assert res.regime_stratified["BREAK_MONSOON"].sample_count == 128
    assert res.regime_stratified["MONSOON_LOW_LPS"].sample_count == 100
    assert res.regime_stratified["WESTERN_DISTURBANCE"].sample_count == 100
    assert res.regime_stratified["ACTIVE_MONSOON"].sample_count == 72
    assert res.regime_stratified["NEUTRAL_TRANSITIONAL"].sample_count == 0


def test_insufficient_and_zero_sample_regime_handling():
    """Verify that zero/insufficient sample regimes do NOT produce fabricated metrics."""
    engine = PostProcessingInferenceEngine.get_instance()
    res: VerificationResponse = engine.get_verification_benchmarks()

    neutral_entry = res.regime_stratified["NEUTRAL_TRANSITIONAL"]
    assert neutral_entry.sample_count == 0
    assert neutral_entry.status == "NO_EVALUATION_SAMPLES"
    assert neutral_entry.raw_nwp is None
    assert neutral_entry.quantile_mapping is None
    assert neutral_entry.global_ml is None
    assert neutral_entry.regime_aware_ml is None


def test_sufficient_regimes_have_valid_numeric_metrics():
    """Verify that regimes with sufficient samples have valid numeric metrics across all 4 models."""
    engine = PostProcessingInferenceEngine.get_instance()
    res: VerificationResponse = engine.get_verification_benchmarks()

    sufficient_regimes = [
        "ACTIVE_MONSOON",
        "BREAK_MONSOON",
        "MONSOON_LOW_LPS",
        "COASTAL_CONVERGENCE",
        "OROGRAPHIC_RAINFALL",
        "WESTERN_DISTURBANCE",
    ]

    for r_key in sufficient_regimes:
        entry = res.regime_stratified[r_key]
        assert entry.status == "SUFFICIENT"
        assert entry.raw_nwp is not None
        assert entry.quantile_mapping is not None
        assert entry.global_ml is not None
        assert entry.regime_aware_ml is not None

        # Check numeric types
        assert isinstance(entry.regime_aware_ml.rmse_mm, float)
        assert isinstance(entry.regime_aware_ml.csi, float)
        assert isinstance(entry.regime_aware_ml.ets, float)
        assert isinstance(entry.regime_aware_ml.pod, float)
        assert isinstance(entry.regime_aware_ml.far, float)


def test_provenance_and_metadata():
    """Verify provenance label and evaluation period metadata."""
    engine = PostProcessingInferenceEngine.get_instance()
    res: VerificationResponse = engine.get_verification_benchmarks()

    assert "2024" in res.evaluation_period and "2025" in res.evaluation_period
    assert res.provenance_status == "HELD_OUT_PROTOTYPE_EVALUATION"
    assert "IMD" in res.ground_truth_source
