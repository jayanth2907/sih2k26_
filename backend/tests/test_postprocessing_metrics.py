"""
Unit Tests for Meteorological Verification Metrics Engine.
Tests:
- Continuous metrics: RMSE, MAE, Mean Bias
- Contingency table metrics: POD, FAR, CSI, ETS
- Spatial verification: Fractions Skill Score (FSS)
- Regime-conditional evaluation breakdown
"""

import numpy as np
import pytest

from backend.app.postprocessing.metrics import (
    ContingencyTable2x2,
    PostProcessingVerificationEngine,
    VerificationReport,
)


def test_continuous_metrics_mathematical_precision():
    """Verify exact formula computations for RMSE, MAE, and Mean Bias."""
    f = np.array([50.0, 70.0, 100.0, 20.0])
    o = np.array([40.0, 80.0, 90.0, 30.0])
    # diffs = [+10, -10, +10, -10]
    # diff^2 = [100, 100, 100, 100], mean = 100, sqrt = 10.0
    # abs(diff) = [10, 10, 10, 10], mean = 10.0
    # mean_bias = 0.0
    rmse, mae, bias = PostProcessingVerificationEngine.compute_continuous_metrics(f, o)
    assert rmse == 10.0
    assert mae == 10.0
    assert bias == 0.0


def test_contingency_table_formulas_and_edge_cases():
    """Verify 2x2 contingency table calculations: POD, FAR, CSI, ETS."""
    # Forecast >= 64.5, Observed >= 64.5
    f = np.array([70.0, 80.0, 30.0, 20.0, 75.0, 10.0])
    o = np.array([75.0, 60.0, 80.0, 15.0, 90.0, 10.0])
    # Threshold 64.5:
    # f_bin = [T, T, F, F, T, F]
    # o_bin = [T, F, T, F, T, F]
    # Hits (a) = indices 0, 4 -> 2
    # False alarms (b) = index 1 -> 1
    # Misses (c) = index 2 -> 1
    # Correct negatives (d) = indices 3, 5 -> 2
    tbl = PostProcessingVerificationEngine.compute_contingency_table(f, o, threshold_mm=64.5)
    assert tbl.hits == 2
    assert tbl.false_alarms == 1
    assert tbl.misses == 1
    assert tbl.correct_negatives == 2
    assert tbl.total == 6

    # POD = 2 / (2 + 1) = 2/3 = 0.667
    assert tbl.pod == pytest.approx(0.667, abs=0.01)
    # FAR = 1 / (2 + 1) = 1/3 = 0.333
    assert tbl.far == pytest.approx(0.333, abs=0.01)
    # CSI = 2 / (2 + 1 + 1) = 2/4 = 0.500
    assert tbl.csi == pytest.approx(0.500, abs=0.01)


def test_perfect_and_zero_skill_contingency():
    """Test extreme cases: perfect score and zero hits."""
    # Perfect forecast
    tbl_perfect = ContingencyTable2x2(hits=10, false_alarms=0, misses=0, correct_negatives=10, total=20)
    assert tbl_perfect.pod == 1.0
    assert tbl_perfect.far == 0.0
    assert tbl_perfect.csi == 1.0
    assert tbl_perfect.ets == 1.0

    # Complete miss
    tbl_miss = ContingencyTable2x2(hits=0, false_alarms=5, misses=5, correct_negatives=10, total=20)
    assert tbl_miss.pod == 0.0
    assert tbl_miss.far == 1.0
    assert tbl_miss.csi == 0.0
    assert tbl_miss.ets <= 0.0


def test_fractions_skill_score_spatial():
    """Verify Fractions Skill Score (FSS) on synthetic spatial grid matrices."""
    # Identical 5x5 grids -> FSS = 1.0
    grid_f = np.zeros((5, 5))
    grid_f[2, 2] = 100.0
    grid_o = np.zeros((5, 5))
    grid_o[2, 2] = 100.0

    fss_perfect = PostProcessingVerificationEngine.compute_fractions_skill_score(
        grid_f, grid_o, threshold_mm=64.5, window_size=3
    )
    assert fss_perfect == 1.0

    # Non-overlapping distant points
    grid_mismatch_o = np.zeros((5, 5))
    grid_mismatch_o[0, 0] = 100.0

    fss_mismatch = PostProcessingVerificationEngine.compute_fractions_skill_score(
        grid_f, grid_mismatch_o, threshold_mm=64.5, window_size=1
    )
    assert fss_mismatch == 0.0


def test_regime_conditional_benchmarking():
    """Verify regime-conditional evaluation across multiple models and weather regimes."""
    n = 60
    f_raw = np.random.uniform(20.0, 100.0, size=n)
    f_eqm = f_raw * 1.1
    f_global = f_raw * 1.2
    f_regime = f_raw * 1.25
    observed = f_raw * 1.22

    regimes = ["ACTIVE_MONSOON"] * 30 + ["OROGRAPHIC_RAINFALL"] * 30

    models_forecasts = {
        "raw_nwp": f_raw,
        "quantile_mapping": f_eqm,
        "global_ml": f_global,
        "regime_aware_ml": f_regime,
    }

    benchmarks = PostProcessingVerificationEngine.compute_regime_conditional_benchmarks(
        models_forecasts=models_forecasts,
        observed=observed,
        regimes=regimes,
    )

    assert "ALL_SAMPLES" in benchmarks
    assert "ACTIVE_MONSOON" in benchmarks
    assert "OROGRAPHIC_RAINFALL" in benchmarks

    for reg_key in ["ALL_SAMPLES", "ACTIVE_MONSOON", "OROGRAPHIC_RAINFALL"]:
        for m_id in models_forecasts.keys():
            report = benchmarks[reg_key][m_id]
            assert isinstance(report, VerificationReport)
            assert report.rmse_mm >= 0.0
            assert 0.0 <= report.pod <= 1.0
            assert 0.0 <= report.far <= 1.0
            assert 0.0 <= report.csi <= 1.0
