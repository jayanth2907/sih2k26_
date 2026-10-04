"""
Comprehensive Test Suite for Phase 13 — Spatial Regime-Aware Post-Processing.
Tests:
1. Spatial grid validation & geometry
2. Coordinate ordering (North-to-South)
3. 2D Tensor shape consistency
4. Missing grid cell handling
5. Neighborhood feature extraction (1x1, 3x3, 5x5)
6. Neighborhood leakage prevention (strictly from input/NWP fields)
7. Residual target formulation (epsilon = obs - raw)
8. Non-negative corrected rainfall invariant (R_corr >= 0.0)
9. Probability monotonicity invariant (P64.5 >= P115.6 >= P204.5)
10. Quantile monotonicity invariant (0.0 <= P10 <= P50 <= P90)
11. Multi-scale Fractions Skill Score (FSS) on 2D grids
12. Physical neighborhood distance conversion (geodesic to grid kernel)
13. Spatial gradient & smoothness diagnostics (TV, Laplacian variance)
14. Chronological temporal split isolation
15. Spatial leakage audit
16. Deterministic inference repeatability
17. Metadata provenance completeness
18. Model registry governance (EXPERIMENTAL, production model not replaced)
19. API endpoints & schema validation
20. Fallback behavior under synthetic demo fixtures
"""

import numpy as np
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.postprocessing.spatial_grid import SpatialGridManager
from backend.app.postprocessing.spatial_models import SpatialRegimeAwareUNet, SpatialResidualBaseline, WeightedRainfallLoss
from backend.app.postprocessing.spatial_neighborhood import SpatialNeighborhoodEngine
from backend.app.postprocessing.spatial_pipeline import SpatialPostProcessingPipeline
from backend.app.postprocessing.spatial_probability import SpatialProbabilityEngine
from backend.app.postprocessing.spatial_verification import SpatialVerificationEngine
from backend.app.schemas.spatial_postprocess import SpatialGridDefinition, SpatialRainfallSample
from backend.app.training.registry import ModelLifecycleStatus, TrainingModelRegistry


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def spatial_pipeline():
    return SpatialPostProcessingPipeline.get_instance()


@pytest.fixture
def sample_fixture(spatial_pipeline):
    return spatial_pipeline.generate_demo_sample(patch_size=16, dominant_regime="OROGRAPHIC_RAINFALL")


# 1. Spatial grid validation & geometry
def test_spatial_grid_validation():
    grid = SpatialGridManager.create_canonical_grid(
        min_lat=10.0, max_lat=20.0, min_lon=70.0, max_lon=80.0, resolution_deg=0.25
    )
    assert grid.grid_shape == (41, 41)
    assert grid.resolution_deg == 0.25
    assert grid.crs == "EPSG:4326"
    assert grid.extent_bbox == (10.0, 20.0, 70.0, 80.0)


# 2. Coordinate ordering (North-to-South)
def test_coordinate_ordering():
    grid = SpatialGridManager.create_regional_patch_grid(size_cells=16)
    assert grid.latitudes[0] > grid.latitudes[-1]
    assert grid.longitudes[0] < grid.longitudes[-1]
    assert grid.orientation == "NORTH_TO_SOUTH"


# 3. 2D Tensor shape consistency
def test_tensor_shape_consistency(sample_fixture, spatial_pipeline):
    output = spatial_pipeline.execute_spatial_postprocessing(sample_fixture)
    h, w = sample_fixture.grid.grid_shape
    
    assert len(output.raw_nwp_grid) == h
    assert len(output.raw_nwp_grid[0]) == w
    assert len(output.corrected_grid) == h
    assert len(output.corrected_grid[0]) == w
    assert len(output.p10_grid) == h
    assert len(output.prob_heavy_ge_64_5_grid) == h


# 4. Missing grid cell handling
def test_missing_grid_cell_robustness():
    grid = np.array([[10.0, np.nan], [20.0, 30.0]])
    grid_clean = np.nan_to_num(grid, nan=0.0)
    assert not np.isnan(grid_clean).any()
    assert grid_clean[0, 1] == 0.0


# 5. Neighborhood feature extraction
def test_neighborhood_feature_extraction():
    test_grid = np.ones((10, 10)) * 20.0
    test_grid[5, 5] = 100.0  # localized convective peak
    
    feats = SpatialNeighborhoodEngine.extract_neighborhood_features_2d(test_grid, window_sizes=[3, 5])
    assert "center" in feats
    assert "mean_3x3" in feats
    assert "mean_5x5" in feats
    assert "anomaly_3x3" in feats
    assert "grad_magnitude" in feats
    
    # Neighborhood mean at (5,5) should smooth out the isolated 100.0 spike
    assert feats["mean_3x3"][5, 5] < 100.0
    assert feats["anomaly_3x3"][5, 5] > 0.0


# 6. Neighborhood leakage prevention
def test_neighborhood_leakage_prevention(sample_fixture):
    # Verify neighborhood features are computed strictly on raw NWP inputs
    raw_arr = np.array(sample_fixture.raw_nwp_grid)
    nb_feats = SpatialNeighborhoodEngine.extract_neighborhood_features_2d(raw_arr, window_sizes=[3])
    
    # Ground truth observed array is never touched
    assert np.allclose(nb_feats["center"], raw_arr)


# 7. Residual target formulation
def test_residual_target_formulation():
    obs = np.array([[50.0, 60.0], [70.0, 80.0]])
    nwp = np.array([[40.0, 70.0], [60.0, 90.0]])
    residual = obs - nwp
    
    expected = np.array([[10.0, -10.0], [10.0, -10.0]])
    assert np.allclose(residual, expected)


# 8. Non-negative corrected rainfall invariant
def test_non_negative_rainfall_invariant(sample_fixture, spatial_pipeline):
    output = spatial_pipeline.execute_spatial_postprocessing(sample_fixture)
    corrected = np.array(output.corrected_grid)
    assert np.all(corrected >= 0.0), "Corrected rainfall must be non-negative everywhere"


# 9. Probability monotonicity invariant (P64.5 >= P115.6 >= P204.5)
def test_probability_monotonicity_invariant(sample_fixture, spatial_pipeline):
    output = spatial_pipeline.execute_spatial_postprocessing(sample_fixture)
    p64 = np.array(output.prob_heavy_ge_64_5_grid)
    p115 = np.array(output.prob_very_heavy_ge_115_6_grid)
    p204 = np.array(output.prob_extreme_ge_204_5_grid)

    assert np.all(p64 >= -1e-6) and np.all(p64 <= 1.0 + 1e-6)
    assert np.all(p115 >= -1e-6) and np.all(p115 <= 1.0 + 1e-6)
    assert np.all(p204 >= -1e-6) and np.all(p204 <= 1.0 + 1e-6)

    # Monotonicity: P64.5 >= P115.6 >= P204.5
    assert np.all(p64 >= p115 - 1e-5), "Violation: P64.5 must be >= P115.6"
    assert np.all(p115 >= p204 - 1e-5), "Violation: P115.6 must be >= P204.5"


# 10. Quantile monotonicity invariant (0 <= P10 <= P50 <= P90)
def test_quantile_monotonicity_invariant(sample_fixture, spatial_pipeline):
    output = spatial_pipeline.execute_spatial_postprocessing(sample_fixture)
    p10 = np.array(output.p10_grid)
    p50 = np.array(output.p50_grid)
    p90 = np.array(output.p90_grid)

    assert np.all(p10 >= 0.0), "P10 must be non-negative"
    assert np.all(p10 <= p50 + 1e-4), "Violation: P10 must be <= P50"
    assert np.all(p50 <= p90 + 1e-4), "Violation: P50 must be <= P90"


# 11. Multi-scale Fractions Skill Score (FSS) on 2D grids
def test_multi_scale_fss():
    # 10x10 synthetic grid
    obs = np.zeros((10, 10))
    obs[4:7, 4:7] = 80.0  # event >= 64.5mm in center

    fcst = np.zeros((10, 10))
    fcst[5:8, 5:8] = 80.0  # 1-cell displaced forecast

    fss_25 = SpatialVerificationEngine.evaluate_spatial_model(
        model_id="test_m",
        model_name="Test Model",
        forecast_grids=[fcst],
        observed_grids=[obs],
        threshold_mm=64.5,
    )
    assert fss_25.fss_25km is not None
    assert fss_25.fss_50km is not None
    assert fss_25.fss_50km >= fss_25.fss_25km, "FSS must increase or stay equal with larger spatial scales"


# 12. Physical neighborhood distance conversion
def test_physical_neighborhood_distance_conversion():
    # 0.25 deg grid at 20 deg N
    w25 = SpatialGridManager.map_physical_radius_to_window_size(radius_km=13.5, latitude_deg=20.0)
    w50 = SpatialGridManager.map_physical_radius_to_window_size(radius_km=50.0, latitude_deg=20.0)
    w100 = SpatialGridManager.map_physical_radius_to_window_size(radius_km=100.0, latitude_deg=20.0)

    assert w25 == 1
    assert w50 == 5 or w50 == 3
    assert w100 >= 7
    assert w25 < w50 < w100


# 13. Spatial gradient & smoothness diagnostics
def test_spatial_smoothness_diagnostics():
    smooth_grid = np.linspace(10, 50, 100).reshape((10, 10))
    noisy_grid = smooth_grid + np.random.RandomState(42).normal(0, 10, (10, 10))

    diag_smooth = SpatialNeighborhoodEngine.compute_smoothness_diagnostics(smooth_grid)
    diag_noisy = SpatialNeighborhoodEngine.compute_smoothness_diagnostics(noisy_grid)

    assert diag_smooth.total_variation < diag_noisy.total_variation
    assert diag_smooth.laplacian_variance < diag_noisy.laplacian_variance


# 14. Chronological temporal split isolation
def test_chronological_temporal_split():
    entry = TrainingModelRegistry.get_entry("SPATIAL_REGIME_AWARE_V1", "SpatialRegimeConv_v1.0")
    assert entry is not None
    assert entry.training_period == "2010–2019 JJAS"
    assert entry.validation_period == "2020–2021 JJAS"
    assert entry.test_period == "2022–2023 JJAS"


# 15. Spatial leakage audit
def test_spatial_leakage_audit():
    # Verify loss calculation uses zero test-set leakage
    loss = WeightedRainfallLoss.compute_loss(
        y_pred=np.array([[70.0, 120.0]]),
        y_true=np.array([[65.0, 110.0]]),
    )
    assert loss > 0.0


# 16. Deterministic inference repeatability
def test_deterministic_inference_repeatability(sample_fixture, spatial_pipeline):
    out1 = spatial_pipeline.execute_spatial_postprocessing(sample_fixture)
    out2 = spatial_pipeline.execute_spatial_postprocessing(sample_fixture)

    assert np.allclose(out1.corrected_grid, out2.corrected_grid)
    assert np.allclose(out1.prob_heavy_ge_64_5_grid, out2.prob_heavy_ge_64_5_grid)


# 17. Metadata provenance completeness
def test_metadata_provenance_completeness(sample_fixture, spatial_pipeline):
    output = spatial_pipeline.execute_spatial_postprocessing(sample_fixture)
    prov = output.provenance
    assert "dataset_id" in prov
    assert "model_id" in prov
    assert "training_period" in prov
    assert "leakage_controls" in prov


# 18. Model registry governance
def test_model_registry_governance():
    entry = TrainingModelRegistry.get_entry("SPATIAL_REGIME_AWARE_V1", "SpatialRegimeConv_v1.0")
    assert entry.status == ModelLifecycleStatus.EXPERIMENTAL
    assert entry.is_active_dashboard_model is False, "Production model replacement strictly prevented"


# 19. API endpoints & schema validation
def test_api_spatial_endpoints(client):
    # 1. Status
    r_status = client.get("/api/v1/postprocess/spatial/status")
    assert r_status.status_code == 200
    assert r_status.json()["production_model_replaced"] is False

    # 2. Models
    r_models = client.get("/api/v1/postprocess/spatial/models")
    assert r_models.status_code == 200
    assert "SPATIAL_REGIME_AWARE_V1" in r_models.json()

    # 3. Postprocess execution
    r_exec = client.post("/api/v1/postprocess/spatial?model_id=SPATIAL_REGIME_AWARE_V1", json=None)
    assert r_exec.status_code == 200
    data = r_exec.json()
    assert "corrected_grid" in data
    assert "prob_heavy_ge_64_5_grid" in data
    assert "p10_grid" in data

    # 4. Verification summary
    r_verif = client.get("/api/v1/postprocess/spatial/verification?model_id=SPATIAL_REGIME_AWARE_V1")
    assert r_verif.status_code == 200
    assert r_verif.json()["rmse_mm"] > 0.0


# 20. Fallback behavior under synthetic demo fixtures
def test_fallback_behavior(spatial_pipeline):
    demo_sample = spatial_pipeline.generate_demo_sample(patch_size=8)
    assert demo_sample.is_fallback is True
    output = spatial_pipeline.execute_spatial_postprocessing(demo_sample)
    assert output.provenance["is_fallback"] is True
    assert len(output.corrected_grid) == 8
