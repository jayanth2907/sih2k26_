"""
Smoke test all primary endpoints for Phase 8.
"""
from backend.app.main import create_app
from starlette.testclient import TestClient

app = create_app()
client = TestClient(app)

print("1. GET /health")
r = client.get("/health")
print("Status:", r.status_code, r.json().get("status"))
assert r.status_code == 200

print("2. GET /api/v1/models/health")
r = client.get("/api/v1/models/health")
print("Status:", r.status_code, r.json().get("status"))
assert r.status_code == 200

print("3. GET /api/v1/postprocess/models")
r = client.get("/api/v1/postprocess/models")
print("Status:", r.status_code, "Models:", len(r.json()))
assert r.status_code == 200

print("4. GET /api/v1/postprocess/compare")
r = client.get("/api/v1/postprocess/compare?raw_rainfall_mm=45.0&latitude=19.07&longitude=72.87")
print("Status:", r.status_code, "Best Model:", r.json().get("best_performing_model_id"))
assert r.status_code == 200

print("5. GET /api/v1/postprocess/districts")
r = client.get("/api/v1/postprocess/districts")
print("Status:", r.status_code, "Districts count:", len(r.json()))
assert r.status_code == 200

print("6. GET /api/v1/postprocess/verification")
r = client.get("/api/v1/postprocess/verification")
print("Status:", r.status_code, "Evaluated samples:", r.json().get("sample_count"))
assert r.status_code == 200

print("7. GET /api/v1/data/status")
r = client.get("/api/v1/data/status")
print("Status:", r.status_code, "Sources count:", len(r.json()))
assert r.status_code == 200


print("8. GET /api/v1/data/sources")
r = client.get("/api/v1/data/sources")
print("Status:", r.status_code, "Source catalog:", len(r.json()))
assert r.status_code == 200

print("9. POST /api/v1/predict")
payload = {
    "latitude": 19.0760,
    "longitude": 72.8777,
    "prediction_date": "2024-07-15",
    "location_name": "Mumbai City",
    "nwp_horizon_hours": 24,
    "include_geojson_contours": False
}
r = client.post("/api/v1/predict", json=payload)
print("Status:", r.status_code, "Regime:", r.json().get("regime", {}).get("primary_regime"))
print("District forecast output:", r.json().get("district_forecast", {}).get("district_name"), "Calibrated:", r.json().get("district_forecast", {}).get("corrected_mm"))
assert r.status_code == 200

print("10. POST /api/v1/regime/classify")
regime_payload = {
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
r = client.post("/api/v1/regime/classify", json=regime_payload)
print("Status:", r.status_code, "Regime:", r.json().get("primary_regime"))
assert r.status_code == 200

print("ALL 10 API SMOKE TESTS PASSED CLEANLY!")

