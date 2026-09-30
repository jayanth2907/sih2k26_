"""
Integration Tests for Regime & Data Catalog Endpoints (PS26080).
Tests:
- GET /api/v1/regime
- POST /api/v1/regime/classify
- GET /api/v1/data/status
- GET /api/v1/data/sources
"""

from fastapi.testclient import TestClient
from backend.app.main import create_app


app = create_app()
client = TestClient(app)


def test_get_regime_endpoint():
    response = client.get("/api/v1/regime?latitude=19.0760&longitude=72.8777&prediction_date=2026-07-15")
    assert response.status_code == 200
    data = response.json()
    assert "primary_regime" in data
    assert "confidence" in data
    assert "probabilities" in data
    assert "drivers" in data
    assert "synoptic_features" in data
    assert "is_demo" in data
    assert "data_source" in data
    assert len(data["drivers"]) >= 3


def test_post_regime_classify_endpoint():
    payload = {
        "timestamp": "2026-07-15T12:00:00Z",
        "forecast_initialization": "2026-07-15T00:00:00Z",
        "lead_time_hours": 12,
        "latitude": 17.92,
        "longitude": 73.65,
        "rainfall": 65.0,
        "temperature_850": 292.5,
        "temperature_700": 282.0,
        "temperature_500": 265.0,
        "relative_humidity_850": 90.0,
        "relative_humidity_700": 85.0,
        "relative_humidity_500": 65.0,
        "u850": 15.0,
        "v850": 6.0,
        "geopotential_850": 1470.0,
        "geopotential_500": 5850.0,
        "vertical_velocity": -0.4,
        "surface_pressure": 900.0,
        "mslp": 1007.0,
        "elevation": 1350.0,
        "slope": 5.0,
        "aspect": 270.0,
        "distance_to_coast": 55.0,
        "data_source": "NCMRWF_NCUM",
        "data_quality": "QC_PASSED",
        "is_demo": False,
    }

    response = client.post("/api/v1/regime/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["primary_regime"] in ["OROGRAPHIC_RAINFALL", "ACTIVE_MONSOON"]
    assert data["data_source"] == "NCMRWF_NCUM"
    assert data["is_demo"] is False
    assert 0.0 <= data["confidence"] <= 1.0


def test_get_data_status_endpoint():
    response = client.get("/api/v1/data/status")
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) >= 7
    source_ids = [s["source_id"] for s in sources]
    assert "NCMRWF_NCUM" in source_ids
    assert "NCMRWF_NEPS" in source_ids
    assert "ECMWF_ERA5" in source_ids
    assert "IMD_GRIDDED_RAINFALL" in source_ids
    assert "NASA_GPM_IMERG" in source_ids
    assert "SRTM_DEM_TOPOGRAPHY" in source_ids
    assert "SURVEY_OF_INDIA_DISTRICTS" in source_ids


def test_get_data_sources_catalog_endpoint():
    response = client.get("/api/v1/data/sources")
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) >= 7
    ncum = next(s for s in sources if s["id"] == "NCMRWF_NCUM")
    assert "National Centre for Medium Range Weather Forecasting" in ncum["provider"]
    assert ncum["is_demo"] is True
