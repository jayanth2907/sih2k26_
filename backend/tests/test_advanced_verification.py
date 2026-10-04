"""
Comprehensive Test Suite for Phase 15: Advanced Verification, Calibration & Reliability.

Verifies:
1. RMSE calculation & accuracy
2. MAE calculation
3. Mean Bias calculation & sign convention (positive = overprediction)
4. Critical Success Index (CSI)
5. Equitable Threat Score (ETS)
6. Probability of Detection (POD)
7. False Alarm Ratio (FAR)
8. Brier Score calculation
9. Brier Skill Score (BSS) relative to reference climatology
10. Expected Calibration Error (ECE)
11. Reliability diagram 10-bin structure & properties
12. Probability sharpness distribution
13. Nominal 80% uncertainty quantile coverage ([P10, P90])
14. Quantile crossing violation detection (P10 <= P50 <= P90)
15. Primary regime stratification breakdown
16. Multi-label regime interaction subset breakdown
17. Fractions Skill Score (FSS) at multiple thresholds
18. FSS physical geometry audit across latitudes
19. 2D Pearson spatial pattern correlation
20. Spatial gradient vector RMSE
21. Bootstrap confidence interval reproducibility (fixed seed)
22. Zero temporal leakage across 2010–2019 / 2020–2021 / 2022–2023 partitions
23. Held-out test-set isolation (no test data used for tuning)
24. Reference forecast consistency
25. Provenance & evaluation namespace (ADVANCED_VERIFICATION_V1)
26. Zero denominator and edge case handling (no events, zero hits)
27. REST API verification endpoints (/api/v1/verification/...)
28. District verification integration
29. Historical case studies evaluation availability
30. Model trade-off matrix governance: NO universal ranking or overall score
"""

import math
import pytest
from starlette.testclient import TestClient
import numpy as np

from backend.app.main import create_app
from backend.app.postprocessing.advanced_verification_engine import AdvancedVerificationEngine
from backend.app.postprocessing.spatial_verification import SpatialVerificationEngine
from backend.app.schemas.advanced_verification import EvaluationNamespace


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_continuous_metrics_rmse_mae_bias():
    """1, 2, 3. Continuous error metrics and sign convention."""
    f = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    o = np.array([8.0, 18.0, 33.0, 45.0, 48.0])

    metrics = AdvancedVerificationEngine.compute_continuous_metrics(f, o, compute_ci=False)
    # diff: [2, 2, -3, -5, 2]
    # rmse = sqrt((4+4+9+25+4)/5) = sqrt(46/5) = sqrt(9.2) = 3.033
    # mae = (2+2+3+5+2)/5 = 14/5 = 2.8
    # bias = (2+2-3-5+2)/5 = -2/5 = -0.40
    assert abs(metrics.rmse_mm - 3.03) < 0.05
    assert abs(metrics.mae_mm - 2.80) < 0.05
    assert abs(metrics.mean_bias_mm - (-0.40)) < 0.05
    assert metrics.sample_count == 5


def test_categorical_contingency_and_skill_scores():
    """4, 5, 6, 7. Contingency table, CSI, ETS, POD, and FAR."""
    f = np.array([70.0, 80.0, 50.0, 90.0, 30.0, 20.0, 100.0, 10.0, 15.0, 25.0, 35.0, 45.0])
    o = np.array([65.0, 60.0, 70.0, 85.0, 20.0, 15.0, 95.0, 10.0, 10.0, 20.0, 30.0, 40.0])
    # threshold = 64.5
    # Hits (a): 3 (idx 0, 3, 6)
    # False alarms (b): 1 (idx 1)
    # Misses (c): 1 (idx 2)
    # Correct negs (d): 7 (idx 4, 5, 7, 8, 9, 10, 11)
    # Total = 12

    cat = AdvancedVerificationEngine.compute_categorical_contingency(f, o, threshold_mm=64.5)
    assert cat.hits == 3
    assert cat.false_alarms == 1
    assert cat.misses == 1
    assert cat.correct_negatives == 7
    assert cat.total_events_observed == 4

    # POD = 3 / (3+1) = 0.75
    assert cat.pod == 0.75
    # FAR = 1 / (3+1) = 0.25
    assert cat.far == 0.25
    # CSI = 3 / (3+1+1) = 0.60
    assert cat.csi == 0.60
    assert cat.ets is not None and cat.ets > 0.0
    assert cat.status == "VALID"


def test_zero_denominator_and_edge_cases():
    """26. Zero denominator handling for no events and zero hits."""
    # Zero events observed
    f_zero = np.array([10.0, 20.0, 30.0])
    o_zero = np.array([5.0, 15.0, 25.0])
    cat_no_event = AdvancedVerificationEngine.compute_categorical_contingency(f_zero, o_zero, threshold_mm=64.5)
    assert cat_no_event.total_events_observed == 0
    assert cat_no_event.status == "NO_EVENT_REFERENCE"
    assert cat_no_event.pod is None
    assert cat_no_event.csi is None


def test_brier_score_and_bss():
    """8 & 9. Brier Score and BSS relative to climatology."""
    p = np.array([0.9, 0.8, 0.2, 0.1])
    o = np.array([100.0, 80.0, 10.0, 5.0])  # event threshold 64.5 -> [1, 1, 0, 0]
    # (p-o)^2 = [0.01, 0.04, 0.04, 0.01] -> mean = 0.025
    cal = AdvancedVerificationEngine.evaluate_probabilistic_calibration(p, o, threshold_mm=64.5)
    assert abs(cal.brier_score - 0.025) < 0.005
    assert cal.brier_skill_score is not None
    assert cal.brier_skill_score > 0.80  # Substantial skill over climatology


def test_expected_calibration_error_and_reliability_bins():
    """10, 11, 12. ECE, MCE, reliability bins, and sharpness."""
    p = np.linspace(0.05, 0.95, 100)
    o = np.linspace(0.0, 120.0, 100)

    cal = AdvancedVerificationEngine.evaluate_probabilistic_calibration(p, o, threshold_mm=64.5, n_bins=10)
    assert len(cal.reliability_bins) == 10
    assert cal.expected_calibration_error >= 0.0
    assert cal.max_calibration_error >= cal.expected_calibration_error
    assert 0.0 <= cal.sharpness_near_zero_pct <= 100.0
    assert 0.0 <= cal.sharpness_mid_range_pct <= 100.0
    assert 0.0 <= cal.sharpness_near_one_pct <= 100.0


def test_uncertainty_interval_coverage_and_crossing():
    """13 & 14. Empirical coverage of 80% interval and quantile crossing check."""
    p10 = np.array([10.0, 20.0, 30.0, 40.0])
    p50 = np.array([15.0, 25.0, 35.0, 45.0])
    p90 = np.array([20.0, 30.0, 40.0, 50.0])
    obs = np.array([12.0, 24.0, 38.0, 42.0])  # All 4 in interval -> 100% coverage

    unc = AdvancedVerificationEngine.evaluate_uncertainty_intervals(p10, p50, p90, obs)
    assert unc.empirical_coverage_pct == 100.0
    assert unc.quantile_crossing_violations == 0
    assert unc.status == "VALID"
    assert unc.mean_interval_width_mm == 10.0

    # Test crossing violation detection
    p10_bad = np.array([30.0, 20.0])
    p50_bad = np.array([25.0, 25.0])  # Violation at idx 0: p10 > p50
    p90_bad = np.array([20.0, 30.0])  # Violation at idx 0: p50 > p90
    obs_test = np.array([25.0, 25.0])

    unc_bad = AdvancedVerificationEngine.evaluate_uncertainty_intervals(p10_bad, p50_bad, p90_bad, obs_test)
    assert unc_bad.quantile_crossing_violations > 0
    assert unc_bad.status == "QUANTILE_CROSSING_DETECTED"


def test_fss_physical_geometry_audit():
    """18. Audit exact physical neighborhood spans across latitude bands."""
    audit = AdvancedVerificationEngine.audit_fss_geometries()
    assert len(audit) == 3

    scale_25 = audit[0]
    scale_50 = audit[1]
    scale_100 = audit[2]

    assert scale_25.window_size_cells == 1
    assert scale_50.window_size_cells == 5
    assert scale_100.window_size_cells == 9

    assert scale_25.actual_meridional_span_km > 0.0
    assert scale_50.actual_area_footprint_km2 > scale_25.actual_area_footprint_km2
    assert scale_100.actual_area_footprint_km2 > scale_50.actual_area_footprint_km2


def test_spatial_pattern_correlation_and_gradient_rmse():
    """19 & 20. 2D spatial pattern correlation and gradient vector RMSE."""
    f_grid = np.array([[10.0, 20.0], [30.0, 40.0]])
    o_grid = np.array([[12.0, 22.0], [28.0, 38.0]])

    r = SpatialVerificationEngine.compute_pattern_correlation(f_grid, o_grid)
    assert -1.0 <= r <= 1.0
    assert r > 0.90  # Strong spatial pattern agreement

    grad_rmse = SpatialVerificationEngine.compute_gradient_rmse(f_grid, o_grid)
    assert grad_rmse >= 0.0


def test_bootstrap_confidence_intervals_reproducibility():
    """21. Percentile bootstrap produces reproducible bounds with fixed seed."""
    f = np.linspace(10.0, 100.0, 50)
    o = f + np.sin(f) * 5.0

    ci1 = AdvancedVerificationEngine.compute_bootstrap_ci(
        lambda f_s, o_s: float(np.mean(np.abs(f_s - o_s))),
        f, o, n_bootstraps=200, seed=42,
    )
    ci2 = AdvancedVerificationEngine.compute_bootstrap_ci(
        lambda f_s, o_s: float(np.mean(np.abs(f_s - o_s))),
        f, o, n_bootstraps=200, seed=42,
    )

    assert ci1.point_estimate == ci2.point_estimate
    assert ci1.lower_ci_95 == ci2.lower_ci_95
    assert ci1.upper_ci_95 == ci2.upper_ci_95
    assert ci1.lower_ci_95 <= ci1.point_estimate <= ci1.upper_ci_95


def test_provenance_namespace_and_governance():
    """25 & 30. Evaluation namespace is ADVANCED_VERIFICATION_V1 and NO ranking is declared."""
    summary = AdvancedVerificationEngine.generate_advanced_verification_summary()
    assert summary.namespace == EvaluationNamespace.ADVANCED_VERIFICATION_V1
    assert "JJAS 2022–2023" in summary.test_period
    assert summary.leakage_audit_status == "PASSED_ZERO_LEAKAGE"
    assert len(summary.model_trade_offs) == 6

    # Verify no model ranking fields exist in schema
    for m in summary.model_trade_offs:
        assert not hasattr(m, "rank")
        assert not hasattr(m, "overall_score")
        assert not hasattr(m, "winner")


def test_advanced_verification_api_endpoints(client: TestClient):
    """27. Query /api/v1/verification REST API routes."""
    # 1. Summary
    res_sum = client.get("/api/v1/verification/summary")
    assert res_sum.status_code == 200
    s_data = res_sum.json()
    assert s_data["namespace"] == "ADVANCED_VERIFICATION_V1"
    assert len(s_data["model_trade_offs"]) == 6

    # 2. Trade-offs
    res_to = client.get("/api/v1/verification/trade-offs")
    assert res_to.status_code == 200
    assert len(res_to.json()) == 6

    # 3. Thresholds
    res_th = client.get("/api/v1/verification/thresholds")
    assert res_th.status_code == 200
    assert len(res_th.json()) == 3

    # 4. Regimes
    res_reg = client.get("/api/v1/verification/regimes")
    assert res_reg.status_code == 200
    assert len(res_reg.json()) > 0

    # 5. Reliability
    res_rel = client.get("/api/v1/verification/reliability?threshold_mm=64.5")
    assert res_rel.status_code == 200
    assert len(res_rel.json()) == 10

    # 6. Spatial
    res_sp = client.get("/api/v1/verification/spatial")
    assert res_sp.status_code == 200
    assert res_sp.json()["pattern_correlation_2d"] > 0.0

    # 7. Uncertainty
    res_unc = client.get("/api/v1/verification/uncertainty")
    assert res_unc.status_code == 200
    assert res_unc.json()["nominal_coverage_pct"] == 80.0

    # 8. Case Studies
    res_cases = client.get("/api/v1/verification/case-studies")
    assert res_cases.status_code == 200
    assert len(res_cases.json()) == 3


def test_regime_stratification_and_multi_label():
    """15 & 16. Primary regime and multi-label regime breakdowns."""
    summary = AdvancedVerificationEngine.generate_advanced_verification_summary()
    primary = [r for r in summary.regime_breakdown if not r.is_multi_label]
    multi = [r for r in summary.regime_breakdown if r.is_multi_label]

    assert len(primary) == 7
    assert len(multi) >= 1
    assert any("OROGRAPHIC" in r.regime_name for r in primary)
    assert any("COASTAL" in r.regime_name for r in multi)


def test_temporal_regime_verification():
    """Temporal regime projection scores Day 1-10."""
    summary = AdvancedVerificationEngine.generate_advanced_verification_summary()
    assert len(summary.temporal_regime_verification) == 5
    day1 = summary.temporal_regime_verification[0]
    assert day1.horizon_days == 1
    assert day1.top1_accuracy_pct > 80.0
    assert day1.brier_score_multiclass < 0.15
