"""
Unit and Integration Tests for Phase 7: Multi-Scale Fractions Skill Score (FSS) Verification.
Covers:
- Deterministic mathematical verification of FSS formulation
- Zero-reference edge case handling (NO_EVENT_REFERENCE)
- Spatial window scaling at 25 km (w=1), 50 km (w=5), and 100 km (w=9)
- All four forecast models (RAW NWP, EQM, GLOBAL ML, REGIME-AWARE AI)
- Monotonicity of spatial scale smoothing
- Verification endpoint and schema contract compliance
- Preservation of Phase 6 regime verification and baseline 50 km benchmark
"""

import numpy as np
import pytest

from backend.app.postprocessing.inference import PostProcessingInferenceEngine
from backend.app.postprocessing.metrics import PostProcessingVerificationEngine
from backend.app.schemas.postprocess import VerificationResponse


# =========================================================================
# 1. Deterministic Mathematical Formula Unit Tests (Tiny Synthetic Grids)
# =========================================================================

def test_fss_formula_identical_forecast_and_observation():
    """Case 1: When forecast and observation are identical, FSS must equal 1.0."""
    grid = np.zeros((10, 10))
    grid[3:7, 3:7] = 80.0  # Event cells exceeding 64.5mm

    fss = PostProcessingVerificationEngine.compute_fractions_skill_score(
        forecast_grid=grid,
        observed_grid=grid,
        threshold_mm=64.5,
        window_size=3,
    )
    assert fss == 1.0


def test_fss_formula_zero_event_reference_returns_none():
    """Case 2: When neither forecast nor observation has events, MSE_ref is 0 -> return None (NO_EVENT_REFERENCE)."""
    grid_zero = np.zeros((10, 10))  # No precipitation exceeding 64.5mm

    fss = PostProcessingVerificationEngine.compute_fractions_skill_score(
        forecast_grid=grid_zero,
        observed_grid=grid_zero,
        threshold_mm=64.5,
        window_size=3,
    )
    assert fss is None


def test_fss_formula_complete_mismatch_single_cell():
    """Case 3: Complete spatial mismatch with 1x1 window (25 km local scale) -> FSS = 0.0."""
    grid_f = np.zeros((10, 10))
    grid_f[1, 1] = 100.0  # Forecast event at (1, 1)

    grid_o = np.zeros((10, 10))
    grid_o[8, 8] = 100.0  # Observed event at (8, 8)

    fss_25km = PostProcessingVerificationEngine.compute_fractions_skill_score(
        forecast_grid=grid_f,
        observed_grid=grid_o,
        threshold_mm=64.5,
        window_size=1,
    )
    assert fss_25km == 0.0


def test_fss_formula_scale_monotonicity():
    """Case 4: On displaced events, increasing the spatial window size must increase FSS monotonically."""
    grid_f = np.zeros((15, 15))
    grid_f[7, 6] = 90.0  # Forecast event

    grid_o = np.zeros((15, 15))
    grid_o[7, 8] = 90.0  # Observed event 2 grid cells away

    fss_w1 = PostProcessingVerificationEngine.compute_fractions_skill_score(grid_f, grid_o, threshold_mm=64.5, window_size=1)
    fss_w3 = PostProcessingVerificationEngine.compute_fractions_skill_score(grid_f, grid_o, threshold_mm=64.5, window_size=3)
    fss_w5 = PostProcessingVerificationEngine.compute_fractions_skill_score(grid_f, grid_o, threshold_mm=64.5, window_size=5)

    assert fss_w1 == 0.0  # 1x1 cannot see 2-cell displacement
    assert fss_w3 is not None and fss_w3 > fss_w1  # 3x3 begins to overlap
    assert fss_w5 is not None and fss_w5 >= fss_w3  # 5x5 captures full neighborhood


def test_fss_formula_bounds_and_validity():
    """Verify that any valid FSS score is bounded within [0.0, 1.0]."""
    rng = np.random.RandomState(123)
    f_arr = rng.uniform(0, 120, size=(20, 20))
    o_arr = rng.uniform(0, 120, size=(20, 20))

    for w in [1, 3, 5, 9]:
        fss = PostProcessingVerificationEngine.compute_fractions_skill_score(f_arr, o_arr, threshold_mm=64.5, window_size=w)
        assert fss is not None
        assert 0.0 <= fss <= 1.0


# =========================================================================
# 2. Multi-Scale Spatial Engine & Model Benchmarking Tests
# =========================================================================

def test_multi_scale_fss_engine_computation():
    """Verify compute_multi_scale_fss across 25km, 50km, and 100km for all 4 models."""
    n = 100
    rng = np.random.RandomState(42)
    obs = rng.uniform(10, 100, size=n)
    models = {
        "raw_nwp": obs * 0.7,
        "quantile_mapping": obs * 0.9,
        "global_ml": obs * 0.97,
        "regime_aware_ml": obs * 0.99,
    }

    res = PostProcessingVerificationEngine.compute_multi_scale_fss(
        models_forecasts=models,
        observed=obs,
        threshold_mm=64.5,
    )

    assert "25km" in res
    assert "50km" in res
    assert "100km" in res

    for scale_key in ["25km", "50km", "100km"]:
        scale_data = res[scale_key]
        assert scale_data["threshold_mm"] == 64.5
        assert scale_data["status"] == "VALID"
        assert scale_data["valid_grid_cells"] == n
        for m_id in ["raw_nwp", "quantile_mapping", "global_ml", "regime_aware_ml"]:
            assert m_id in scale_data
            score = scale_data[m_id]
            assert score is not None
            assert 0.0 <= score <= 1.0


def test_pipeline_verification_benchmark_includes_multi_scale_fss():
    """Verify that UnifiedPostProcessingPipeline returns valid multi_scale_fss report."""
    pipeline = PostProcessingInferenceEngine.get_instance()
    response = pipeline.get_verification_benchmarks(threshold_mm=64.5)

    assert isinstance(response, VerificationResponse)
    assert response.multi_scale_fss is not None

    report = response.multi_scale_fss
    assert report.threshold_mm == 64.5
    assert report.grid_resolution_km == 25.0
    assert "25km" in report.scales
    assert "50km" in report.scales
    assert "100km" in report.scales

    # Verify 50 km baseline consistency
    scale_50 = report.scales["50km"]
    assert scale_50.scale_km == 50
    assert scale_50.window_size_cells == 5
    assert scale_50.raw_nwp == pytest.approx(0.502, abs=0.005)
    assert scale_50.quantile_mapping == pytest.approx(0.922, abs=0.005)
    assert scale_50.global_ml == pytest.approx(0.961, abs=0.005)
    assert scale_50.regime_aware_ml == pytest.approx(0.957, abs=0.005)

    # Verify 25 km scale
    scale_25 = report.scales["25km"]
    assert scale_25.scale_km == 25
    assert scale_25.window_size_cells == 1
    assert 0.0 <= scale_25.raw_nwp <= 1.0
    assert 0.0 <= scale_25.quantile_mapping <= 1.0
    assert 0.0 <= scale_25.global_ml <= 1.0
    assert 0.0 <= scale_25.regime_aware_ml <= 1.0

    # Verify 100 km scale
    scale_100 = report.scales["100km"]
    assert scale_100.scale_km == 100
    assert scale_100.window_size_cells == 9
    assert 0.0 <= scale_100.raw_nwp <= 1.0
    assert 0.0 <= scale_100.quantile_mapping <= 1.0
    assert 0.0 <= scale_100.global_ml <= 1.0
    assert 0.0 <= scale_100.regime_aware_ml <= 1.0

    # Verify spatial monotonicity across scales: FSS_25 <= FSS_50 <= FSS_100
    assert scale_25.raw_nwp <= scale_50.raw_nwp <= scale_100.raw_nwp
    assert scale_25.quantile_mapping <= scale_50.quantile_mapping <= scale_100.quantile_mapping
    assert scale_25.global_ml <= scale_50.global_ml <= scale_100.global_ml
    assert scale_25.regime_aware_ml <= scale_50.regime_aware_ml <= scale_100.regime_aware_ml


def test_provenance_and_phase_6_preservation():
    """Verify Phase 6 regime scorecard, sample counts (N=800), and provenance are preserved."""
    pipeline = PostProcessingInferenceEngine.get_instance()
    response = pipeline.get_verification_benchmarks(threshold_mm=64.5)

    assert response.sample_count == 800
    assert response.provenance_status == "HELD_OUT_PROTOTYPE_EVALUATION"
    assert len(response.regime_stratified) == 7

    total_regime_samples = sum(entry.sample_count for entry in response.regime_stratified.values())
    assert total_regime_samples == 800

    # Ensure regime scorecard retains honest fss_available=False
    for entry in response.regime_stratified.values():
        assert entry.fss_available is False
