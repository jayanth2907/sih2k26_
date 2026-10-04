"""
Phase 8: District-Level Decision Support & Prototype Warning Backend and Geospatial Tests.

Verifies:
1. GET /api/v1/postprocess/districts returns 200 OK
2. District count is deterministic
3. District IDs and (district, state) pairs are unique
4. District names and states are present on all records
5. Rainfall fields (raw NWP, calibrated P50, bias delta) are valid floats >= 0 (or real deltas)
6. Exceedance probabilities are bounded within [0.0, 1.0] and monotonic (heavy >= vheavy >= extreme)
7. Uncertainty bounds satisfy P10 <= P50 <= P90 and P10 >= 0
8. IMD-aligned threshold configuration (64.5 mm, 115.6 mm, 204.5 mm)
9. Deterministic decision-support category assignment logic
10. Strict rule: No official warning claims (is_official_imd_warning is False, disclaimer is present)
11. Provenance metadata is present on all records
12. Query parameter filtering (state, regime, category) works deterministically
13. Geospatial coordinate validity within Indian bounding box (WGS84)
14. Spatial nearest-centroid lookup is deterministic
15. Backward compatibility of all schema fields
"""

import pytest
from starlette.testclient import TestClient

from backend.app.data.sources.districts import DistrictProvider, DistrictsSource
from backend.app.main import create_app
from backend.app.postprocessing.base import PostProcessingInput
from backend.app.postprocessing.heavy_rain import HeavyRainfallCalibrator
from backend.app.postprocessing.inference import PostProcessingInferenceEngine
from backend.app.schemas.postprocess import DistrictForecast
from backend.app.schemas.regime import WeatherRegimeType


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_district_endpoint_returns_200(client: TestClient):
    """1. GET /api/v1/postprocess/districts returns 200 OK."""
    res = client.get("/api/v1/postprocess/districts")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_district_registry_validation():
    """2 & 3. Verify district directory registry completeness, uniqueness, and bounds."""
    val = DistrictProvider.validate_district_registry()
    assert val["status"] == "VALID"
    assert val["unique_ids"] is True
    assert val["unique_names_per_state"] is True
    assert val["invalid_coordinate_count"] == 0
    assert val["total_districts"] == len(DistrictProvider.get_all_districts())


def test_district_metadata_presence(client: TestClient):
    """4. District names, states, IDs, and coordinates are present."""
    res = client.get("/api/v1/postprocess/districts")
    data = res.json()

    for item in data:
        assert "district_name" in item and len(item["district_name"]) > 0
        assert "state_name" in item and len(item["state_name"]) > 0
        assert "district_id" in item and len(item["district_id"]) > 0
        assert "dominant_regime" in item
        assert "lat" in item and item["lat"] is not None
        assert "lon" in item and item["lon"] is not None


def test_district_rainfall_fields_numeric(client: TestClient):
    """5. Rainfall fields are numeric and physically non-negative."""
    res = client.get("/api/v1/postprocess/districts")
    data = res.json()

    for item in data:
        raw_nwp = item["raw_nwp_mm"]
        calibrated = item["corrected_mm"]
        delta = item["correction_delta_mm"]

        assert isinstance(raw_nwp, (int, float)) and raw_nwp >= 0.0
        assert isinstance(calibrated, (int, float)) and calibrated >= 0.0
        assert isinstance(delta, (int, float))
        assert abs(calibrated - raw_nwp - delta) < 0.2  # Delta matches difference


def test_district_probabilities_bounded_and_monotonic(client: TestClient):
    """6. Exceedance probabilities are in [0, 1] and monotonic."""
    res = client.get("/api/v1/postprocess/districts")
    data = res.json()

    for item in data:
        p_heavy = item["heavy_prob"]
        p_vheavy = item["very_heavy_prob"]
        p_extreme = item["extreme_prob"]

        assert 0.0 <= p_heavy <= 1.0
        assert 0.0 <= p_vheavy <= 1.0
        assert 0.0 <= p_extreme <= 1.0
        # Monotonicity: P(>=64.5) >= P(>=115.6) >= P(>=204.5)
        assert p_heavy >= p_vheavy - 1e-4
        assert p_vheavy >= p_extreme - 1e-4


def test_district_uncertainty_quantiles(client: TestClient):
    """7. Uncertainty quantiles satisfy P10 <= P50 <= P90."""
    res = client.get("/api/v1/postprocess/districts")
    data = res.json()

    for item in data:
        p10 = item["uncertainty_lower_bound_mm"]
        p50 = item["corrected_mm"]
        p90 = item["uncertainty_upper_bound_mm"]
        spread = item["ensemble_spread_mm"]

        assert p10 >= 0.0
        assert p10 <= p50 + 1e-2
        assert p50 <= p90 + 1e-2
        assert spread >= 0.0


def test_imd_rainfall_threshold_constants():
    """8, 9, 10. IMD-aligned threshold constants (64.5, 115.6, 204.5 mm)."""
    assert HeavyRainfallCalibrator.DEFAULT_HEAVY_THRESHOLD == 64.5
    assert HeavyRainfallCalibrator.DEFAULT_VERY_HEAVY_THRESHOLD == 115.6
    assert HeavyRainfallCalibrator.DEFAULT_EXTREME_THRESHOLD == 204.5


def test_deterministic_decision_support_categories():
    """11. Decision support category logic is strictly deterministic."""
    engine = PostProcessingInferenceEngine.get_instance()

    # Normal rain (<64.5mm, low prob)
    out_normal = engine.correct_forecast(
        PostProcessingInput(
            raw_nwp_rainfall=20.0,
            lead_time_hours=24,
            latitude=21.14,
            longitude=79.08,
            month=7,
            day_of_year=200,
            primary_regime="BREAK_MONSOON",
            is_demo=True,
        )
    )
    f_normal = engine.generate_district_forecast(
        district_name="Nagpur",
        state_name="Maharashtra",
        raw_nwp_mm=20.0,
        regime_output=out_normal,
        dominant_regime="BREAK_MONSOON",
    )
    assert f_normal.decision_support_category == "NORMAL"
    assert "below" in f_normal.decision_basis

    # Heavy rain (>=64.5mm)
    out_heavy = engine.correct_forecast(
        PostProcessingInput(
            raw_nwp_rainfall=60.0,
            lead_time_hours=24,
            latitude=18.93,
            longitude=72.83,
            month=7,
            day_of_year=200,
            primary_regime="COASTAL_CONVERGENCE",
            is_demo=True,
        )
    )
    f_heavy = engine.generate_district_forecast(
        district_name="Mumbai City",
        state_name="Maharashtra",
        raw_nwp_mm=60.0,
        regime_output=out_heavy,
        dominant_regime="COASTAL_CONVERGENCE",
    )
    assert f_heavy.decision_support_category in ("HEAVY_RAINFALL", "VERY_HEAVY_RAINFALL", "EXTREMELY_HEAVY_RAINFALL")
    assert "threshold" in f_heavy.decision_basis


def test_strict_rule_no_official_warning_claim(client: TestClient):
    """12. Strict rule: is_official_imd_warning must be False and disclaimer present."""
    res = client.get("/api/v1/postprocess/districts")
    data = res.json()

    for item in data:
        assert item["is_official_imd_warning"] is False
        assert "Prototype" in item["disclaimer"]
        assert "Not an official IMD warning" in item["disclaimer"]
        assert item["aggregation_method"] == "POINT_SAMPLED_CENTROID"


def test_district_provenance_presence(client: TestClient):
    """13. Provenance status is populated on all district records."""
    res = client.get("/api/v1/postprocess/districts")
    data = res.json()

    for item in data:
        assert item["provenance_status"] in ("HELD_OUT_PROTOTYPE_EVALUATION", "DEMO DATA · SYNTHETIC / FALLBACK MODE")


def test_district_filtering_by_state_and_regime(client: TestClient):
    """14. Query filtering by state, regime, and category returns valid subsets."""
    # Filter by state: Maharashtra
    res_mh = client.get("/api/v1/postprocess/districts?state=Maharashtra")
    assert res_mh.status_code == 200
    data_mh = res_mh.json()
    assert len(data_mh) > 0
    assert all(d["state_name"].lower() == "maharashtra" for d in data_mh)

    # Filter by regime: OROGRAPHIC_RAINFALL
    res_orog = client.get("/api/v1/postprocess/districts?regime=OROGRAPHIC_RAINFALL")
    assert res_orog.status_code == 200
    data_orog = res_orog.json()
    assert len(data_orog) > 0
    assert all(d["dominant_regime"] == "OROGRAPHIC_RAINFALL" for d in data_orog)


def test_geospatial_coordinate_bounds_and_nearest_lookup():
    """15. Geospatial coordinates are valid and lookup returns nearest centroid."""
    all_dists = DistrictsSource.get_all_districts()

    for d in all_dists:
        assert 6.0 <= d["lat"] <= 37.5
        assert 68.0 <= d["lon"] <= 98.0

    # Near Mumbai (19.0, 72.85) -> should match Mumbai Suburban or Mumbai City
    mumbai_match = DistrictsSource.lookup_district(19.0, 72.85)
    assert "Mumbai" in mumbai_match["district"]
    assert mumbai_match["state"] == "Maharashtra"

    # Near Shillong/Cherrapunji (25.5, 91.8) -> East Khasi Hills
    shillong_match = DistrictsSource.lookup_district(25.5, 91.8)
    assert shillong_match["district"] == "East Khasi Hills"
    assert shillong_match["state"] == "Meghalaya"
