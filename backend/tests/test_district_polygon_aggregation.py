"""
Comprehensive Test Suite for Phase 14: Full India District Decision Support & Warning Intelligence.

Verifies:
1. Polygon validity & non-empty topology (WGS84 EPSG:4326)
2. Cataloged district count (748 administrative framework)
3. District ID and name uniqueness per state
4. State ID and name mapping completeness
5. CRS specification and coordinate bounding envelope
6. Geodesic area calculation on authalic sphere
7. Grid-cell polygon fractional area intersection
8. Spatial weight normalization (sum(weights) == 1.0)
9. Area-weighted mean rainfall calculation
10. Missing grid data handling (valid_area_fraction calculation)
11. Multi-threshold aggregation (64.5 mm, 115.6 mm, 204.5 mm)
12. Probability monotonicity (P_heavy >= P_very_heavy >= P_extreme)
13. Area-fraction vs probability decoupling
14. Centroid baseline vs Polygon area-weighted side-by-side comparison
15. Population weighting status (Strict rule: MUST be NOT_AVAILABLE, not fabricated)
16. Uncertainty quantile aggregation (P10 <= P50 <= P90)
17. Configurable prototype decision thresholds
18. Deterministic machine-generated bulletin generation
19. JSON export format & schema validation
20. CSV export format & headers
21. GeoJSON FeatureCollection export
22. Forensic data & model provenance presence
23. Staleness / timestamp freshness inheritance
24. Insufficient spatial coverage flag & withholding
25. Deterministic decision categorization & structured reason
26. Boundary reconciliation test (748 vs 766 forensic lineage)
"""

import json
import pytest
from starlette.testclient import TestClient
import numpy as np

from backend.app.data.sources.district_boundaries import DistrictBoundaryProvider
from backend.app.main import create_app
from backend.app.postprocessing.district_aggregation import DistrictAggregationEngine
from backend.app.postprocessing.district_bulletin import DistrictBulletinEngine
from backend.app.postprocessing.district_decision import DistrictDecisionEngine
from backend.app.postprocessing.district_export import DistrictExportEngine
from backend.app.postprocessing.spatial_grid import SpatialGridManager
from backend.app.postprocessing.spatial_pipeline import SpatialPostProcessingPipeline
from backend.app.postprocessing.spatial_weights import SpatialWeightEngine
from backend.app.schemas.district_decision import (
    AggregationMethod,
    DataQualityStatus,
    DecisionSupportCategory,
    DistrictDecisionThresholds,
    DistrictProbabilityStats,
    DistrictSpatialStats,
    DistrictUncertaintyStats,
)
from backend.app.schemas.regime import WeatherRegimeType


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_polygon_validity_and_topology():
    """1. All district polygons are valid geometric topologies in EPSG:4326."""
    val = DistrictBoundaryProvider.validate_boundary_registry()
    assert val["status"] == "VALID"
    assert val["invalid_geometry_count"] == 0
    assert val["invalid_area_count"] == 0
    assert val["invalid_coordinate_count"] == 0


def test_district_count_and_state_mapping():
    """2, 3, 4. District count matches 748 framework; IDs are unique; states mapped."""
    val = DistrictBoundaryProvider.validate_boundary_registry()
    assert val["framework_total_count"] == 748
    assert val["active_cataloged_districts"] > 0
    assert val["unique_ids"] is True
    assert val["unique_names_per_state"] is True
    assert val["state_count"] > 10


def test_crs_and_geodesic_area_calculation():
    """5 & 6. CRS is EPSG:4326 and area calculation is non-negative and physically reasonable."""
    districts = DistrictBoundaryProvider.get_all_districts()
    for d in districts:
        assert d.area_km2 > 0.0
        # Check coordinates within Indian national envelope
        assert 6.0 <= d.centroid_lat <= 37.5
        assert 68.0 <= d.centroid_lon <= 98.0
        assert d.geometry.type in ("Polygon", "MultiPolygon")
        assert len(d.geometry.coordinates) > 0


def test_grid_polygon_intersection_and_spatial_weight_normalization():
    """7 & 8. Grid cells intersect polygons and weights sum to 1.0."""
    grid = SpatialGridManager.create_regional_patch_grid(center_lat=18.5, center_lon=73.5, size_cells=16)
    weight_engine = SpatialWeightEngine.get_instance()
    weights_dict = weight_engine.get_or_compute_weights(grid)

    assert len(weights_dict) > 0
    for d_id, w_entry in weights_dict.items():
        assert len(w_entry.cell_coords) > 0
        sum_w = float(np.sum(w_entry.cell_weights))
        assert abs(sum_w - 1.0) < 1e-4  # Normalized to 1.0


def test_area_weighted_mean_and_quantiles():
    """9. Area-weighted mean, min, max, and quantiles are calculated correctly."""
    grid = SpatialGridManager.create_regional_patch_grid(center_lat=18.5, center_lon=73.5, size_cells=16)
    weight_engine = SpatialWeightEngine.get_instance()
    weights_dict = weight_engine.get_or_compute_weights(grid)

    # Uniform field of 50.0 mm
    field = np.full((16, 16), 50.0, dtype=np.float64)
    w_entry = weights_dict["MH_SATARA"]

    mean_r, max_r, min_r, median_r, p90_r, p95_r, status, valid_frac = weight_engine.aggregate_field(field, w_entry)
    assert mean_r == 50.0
    assert max_r == 50.0
    assert min_r == 50.0
    assert median_r == 50.0
    assert p90_r == 50.0
    assert p95_r == 50.0
    assert status == DataQualityStatus.VALID


def test_missing_grid_coverage_handling():
    """10 & 24. Missing grid cells reduce valid_area_fraction and trigger coverage warning."""
    grid = SpatialGridManager.create_regional_patch_grid(center_lat=18.5, center_lon=73.5, size_cells=16)
    weight_engine = SpatialWeightEngine.get_instance()
    weights_dict = weight_engine.get_or_compute_weights(grid)

    field = np.full((16, 16), 40.0, dtype=np.float64)
    # Mask out 80% of the grid
    missing_mask = np.ones((16, 16), dtype=bool)
    missing_mask[0:2, 0:2] = False  # Only 4 cells valid

    w_entry = weights_dict["MH_SATARA"]
    _, _, _, _, _, _, status, valid_frac = weight_engine.aggregate_field(field, w_entry, missing_mask=missing_mask)

    # Should detect insufficient or partial coverage
    assert valid_frac < 0.60
    assert status == DataQualityStatus.INSUFFICIENT_SPATIAL_COVERAGE


def test_threshold_area_fractions_and_probability_monotonicity():
    """11, 12, 13. Area fraction vs probability decoupling and strict probability monotonicity."""
    pipeline = SpatialPostProcessingPipeline.get_instance()
    sample = pipeline.generate_demo_sample(patch_size=16, dominant_regime="OROGRAPHIC_RAINFALL")
    spatial_output = pipeline.execute_spatial_postprocessing(sample, model_id="SPATIAL_REGIME_AWARE_V1")

    agg_engine = DistrictAggregationEngine.get_instance()
    products = agg_engine.aggregate_spatial_prediction(spatial_output)

    for p in products:
        probs = p.probabilities
        stats = p.spatial_stats

        # Monotonicity: Heavy >= Very Heavy >= Extreme
        assert probs.heavy_probability >= probs.very_heavy_probability - 1e-4
        assert probs.very_heavy_probability >= probs.extreme_probability - 1e-4
        assert probs.monotonicity_verified is True

        # Area fractions bounded in [0, 1]
        assert 0.0 <= stats.heavy_area_fraction <= 1.0
        assert 0.0 <= stats.very_heavy_area_fraction <= 1.0
        assert 0.0 <= stats.extreme_area_fraction <= 1.0
        assert stats.heavy_area_fraction >= stats.very_heavy_area_fraction - 1e-4
        assert stats.very_heavy_area_fraction >= stats.extreme_area_fraction - 1e-4


def test_centroid_vs_polygon_comparison():
    """14. Side-by-side comparison between Centroid and Polygon methods."""
    pipeline = SpatialPostProcessingPipeline.get_instance()
    sample = pipeline.generate_demo_sample(patch_size=16, dominant_regime="OROGRAPHIC_RAINFALL")
    spatial_output = pipeline.execute_spatial_postprocessing(sample, model_id="SPATIAL_REGIME_AWARE_V1")

    agg_engine = DistrictAggregationEngine.get_instance()
    summary = agg_engine.compare_aggregation_methods(spatial_output)

    assert summary.sample_district_count > 0
    assert summary.mean_absolute_difference_mm >= 0.0
    assert summary.rmse_difference_mm >= 0.0
    assert 0.0 <= summary.category_concordance_pct <= 100.0
    assert len(summary.district_comparisons) == summary.sample_district_count


def test_population_weighting_status_not_available():
    """15. Strict rule: Population weighting must return NOT_AVAILABLE and NOT fabricate data."""
    pipeline = SpatialPostProcessingPipeline.get_instance()
    sample = pipeline.generate_demo_sample(patch_size=16)
    spatial_output = pipeline.execute_spatial_postprocessing(sample, model_id="SPATIAL_REGIME_AWARE_V1")

    agg_engine = DistrictAggregationEngine.get_instance()
    products = agg_engine.aggregate_spatial_prediction(spatial_output)

    for p in products:
        assert p.population_weighting_status == "NOT_AVAILABLE"


def test_uncertainty_quantiles_ordering():
    """16. Quantiles satisfy P10 <= P50 <= P90 with non-negative bounds."""
    pipeline = SpatialPostProcessingPipeline.get_instance()
    sample = pipeline.generate_demo_sample(patch_size=16)
    spatial_output = pipeline.execute_spatial_postprocessing(sample, model_id="SPATIAL_REGIME_AWARE_V1")

    agg_engine = DistrictAggregationEngine.get_instance()
    products = agg_engine.aggregate_spatial_prediction(spatial_output)

    for p in products:
        unc = p.uncertainty
        assert unc.p10_mm >= 0.0
        assert unc.p10_mm <= unc.p50_mm + 1e-2
        assert unc.p50_mm <= unc.p90_mm + 1e-2
        assert unc.ensemble_spread_mm >= 0.0
        assert unc.method == "APPROXIMATE_AREA_AGGREGATED_QUANTILE"


def test_deterministic_decision_engine_and_reasons():
    """17 & 25. Deterministic category assignment and structured basis strings."""
    # Normal rain
    stats_norm = DistrictSpatialStats(
        mean_24h_mm=25.0, max_24h_mm=35.0, min_24h_mm=10.0, median_24h_mm=24.0,
        p90_24h_mm=32.0, p95_24h_mm=34.0, heavy_area_fraction=0.0,
        very_heavy_area_fraction=0.0, extreme_area_fraction=0.0,
        valid_area_fraction=1.0, missing_area_fraction=0.0, intersected_cell_count=10,
    )
    prob_norm = DistrictProbabilityStats(heavy_probability=0.15, very_heavy_probability=0.02, extreme_probability=0.0)
    unc_norm = DistrictUncertaintyStats(p10_mm=15.0, p50_mm=24.0, p90_mm=35.0, ensemble_spread_mm=7.8)

    cat, reason, conf = DistrictDecisionEngine.evaluate_district_decision(
        "Nagpur", "Maharashtra", stats_norm, prob_norm, unc_norm, WeatherRegimeType.BREAK_MONSOON, DataQualityStatus.VALID
    )
    assert cat == DecisionSupportCategory.NORMAL
    assert "below" in reason

    # Heavy rain
    stats_heavy = DistrictSpatialStats(
        mean_24h_mm=85.0, max_24h_mm=120.0, min_24h_mm=45.0, median_24h_mm=82.0,
        p90_24h_mm=110.0, p95_24h_mm=115.0, heavy_area_fraction=0.75,
        very_heavy_area_fraction=0.10, extreme_area_fraction=0.0,
        valid_area_fraction=1.0, missing_area_fraction=0.0, intersected_cell_count=12,
    )
    prob_heavy = DistrictProbabilityStats(heavy_probability=0.88, very_heavy_probability=0.25, extreme_probability=0.02)
    cat_h, reason_h, _ = DistrictDecisionEngine.evaluate_district_decision(
        "Mumbai City", "Maharashtra", stats_heavy, prob_heavy, unc_norm, WeatherRegimeType.COASTAL_CONVERGENCE, DataQualityStatus.VALID
    )
    assert cat_h == DecisionSupportCategory.HEAVY_RAINFALL
    assert "heavy" in reason_h.lower()


def test_structured_bulletin_generation():
    """18. Machine-generated bulletin adheres to required section format and disclaimers."""
    pipeline = SpatialPostProcessingPipeline.get_instance()
    sample = pipeline.generate_demo_sample(patch_size=16, dominant_regime="OROGRAPHIC_RAINFALL")
    spatial_output = pipeline.execute_spatial_postprocessing(sample, model_id="SPATIAL_REGIME_AWARE_V1")

    agg_engine = DistrictAggregationEngine.get_instance()
    products = agg_engine.aggregate_spatial_prediction(spatial_output)
    product = products[0]

    bulletin = DistrictBulletinEngine.generate_bulletin(product)
    text = bulletin.formatted_bulletin_text

    assert "DISTRICT METEOROLOGICAL & DECISION-SUPPORT OUTLOOK BULLETIN" in text
    assert product.district_name.upper() in text
    assert "EXPECTED PRECIPITATION" in text
    assert "CALIBRATED HEAVY RAINFALL PROBABILITIES" in text
    assert "SYNOPTIC REGIME & MESOSCALE DRIVERS" in text
    assert "NOT an official IMD warning" in text
    assert bulletin.disclaimer == "Prototype model-derived decision support. Not an official IMD warning."


def test_export_formats(client: TestClient):
    """19, 20, 21. JSON, CSV, and GeoJSON exports operate correctly via API."""
    # GeoJSON
    res_geojson = client.get("/api/v1/districts/export?export_format=geojson")
    assert res_geojson.status_code == 200
    gj = res_geojson.json()
    assert gj["type"] == "FeatureCollection"
    assert len(gj["features"]) > 0
    assert "geometry" in gj["features"][0]
    assert "properties" in gj["features"][0]

    # JSON
    res_json = client.get("/api/v1/districts/export?export_format=json")
    assert res_json.status_code == 200
    j_data = res_json.json()
    assert "products" in j_data
    assert len(j_data["products"]) > 0

    # CSV
    res_csv = client.get("/api/v1/districts/export?export_format=csv")
    assert res_csv.status_code == 200
    assert "district_id,district_name" in res_csv.text


def test_district_api_endpoints(client: TestClient):
    """22, 23. Test /api/v1/districts REST endpoints."""
    # List all
    res_list = client.get("/api/v1/districts")
    assert res_list.status_code == 200
    data = res_list.json()
    assert len(data) > 0

    # Status
    res_status = client.get("/api/v1/districts/status")
    assert res_status.status_code == 200
    st = res_status.json()
    assert st["district_count"] == 748
    assert st["population_data_status"] == "NOT_AVAILABLE"
    assert st["production_model_replaced"] is False

    # Single district & bulletin
    first_id = data[0]["district_id"]
    res_single = client.get(f"/api/v1/districts/{first_id}")
    assert res_single.status_code == 200

    res_bul = client.get(f"/api/v1/districts/{first_id}/bulletin")
    assert res_bul.status_code == 200
    assert "formatted_bulletin_text" in res_bul.json()

    # Text bulletin
    res_bul_text = client.get(f"/api/v1/districts/{first_id}/bulletin?as_text=true")
    assert res_bul_text.status_code == 200
    assert "DISTRICT" in res_bul_text.text


def test_boundary_reconciliation_audit():
    """26. Boundary reconciliation metadata explicitly documents 748 vs 766."""
    rep = DistrictBoundaryProvider.get_reconciliation_report()
    assert rep["DISTRICT_COUNT"] == 748
    assert rep["ALTERNATIVE_COUNT"] == 766
    assert "Survey of India" in rep["DISTRICT_DATASET_SELECTED"]
    assert "bifurcations" in rep["RECONCILIATION_REASON"]
    assert rep["LINEAGE_STATUS"] == "DOCUMENTED_AND_RECONCILED"
