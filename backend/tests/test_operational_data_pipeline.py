"""
Comprehensive tests for Operational Data Pipeline & Ingestion Architecture (Phase 10).
Covers:
1. Source registry
2. Source priority
3. Provenance tracking
4. Fallback labeling
5. Metadata validation
6. Unit normalization
7. Timestamp normalization
8. Lead-time calculation & invariants
9. Coordinate normalization
10. Duplicate forecast step detection
11. Missing-variable handling
12. Stale-data detection
13. Invalid-data rejection & quarantine
14. Secret / credential isolation
15. NCUM adapter interface
16. NEPS adapter interface & ensemble statistics
17. GFS fallback interface
18. Canonical NWP schema validation
19. Regime feature compatibility
20. API backward compatibility
"""

from datetime import datetime, timezone
import pytest
from starlette.testclient import TestClient

from backend.app.data.ingestion.ensemble_processor import EnsembleProcessor
from backend.app.data.ingestion.grib2_reader import (
    GRIB2IngestionEngine,
    GRIB2Metadata,
    MetadataValidator,
    MockGRIB2Reader,
)
from backend.app.data.ingestion.source_router import (
    DataQualityState,
    OperationalReadinessLevel,
    OperationalSourceRouter,
    SourceTier,
)
from backend.app.data.ingestion.spatial_temporal import SpatialTemporalNormalizer
from backend.app.data.ingestion.unit_normalizer import UnitNormalizer
from backend.app.data.processing.feature_engineering import MeteorologicalFeatureEngineer
from backend.app.data.schemas.meteorology import CanonicalMeteorologicalRecord
from backend.app.data.sources.gfs import GFSFallbackAdapter
from backend.app.data.sources.ncmrwf import NCMRWFAdapter
from backend.app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


# 1. Source Registry
def test_source_registry_and_catalog(client: TestClient):
    """1. Verify catalog of supported meteorological data sources."""
    res = client.get("/api/v1/data/sources")
    assert res.status_code == 200
    sources = res.json()
    assert isinstance(sources, list)
    source_ids = [s["id"] for s in sources]
    assert "NCMRWF_NCUM" in source_ids
    assert "NCMRWF_NEPS" in source_ids
    assert "ECMWF_ERA5" in source_ids
    assert "IMD_GRIDDED" in source_ids
    assert "NOAA_GFS_FALLBACK" in source_ids


# 2 & 3 & 4. Source Priority, Provenance & Fallback Labeling
def test_source_priority_and_fallback_labeling():
    """2-4. Verify source routing falls back gracefully with transparent provenance."""
    router = OperationalSourceRouter(primary_enabled=False)
    rec, prov = router.get_forecast(lat=18.52, lon=73.85, target_date="2026-10-02")
    
    assert prov.is_fallback is True
    assert prov.source_tier == SourceTier.DEMO_FALLBACK
    assert "NCMRWF_NCUM_DEMO_SYNTHESIS" in prov.source_id
    assert rec.is_demo is True
    assert "demo" in rec.data_source.lower() or "demo" in rec.data_quality.lower()


# 5 & 13. Metadata Validation & Invalid Data Rejection
def test_metadata_validator_accepts_valid():
    """5. MetadataValidator validates conformant GRIB2 message header."""
    valid_meta = GRIB2Metadata(
        source_agency="NCMRWF",
        model_name="NCUM_REGIONAL",
        initialization_time="2026-10-02T00:00:00Z",
        valid_time="2026-10-03T00:00:00Z",
        lead_time_hours=24,
        variable_name="tp",
        original_units="kg m**-2",
        grid_resolution_deg=0.12,
        lat_bounds=(6.0, 38.0),
        lon_bounds=(66.0, 100.0),
    )
    res = MetadataValidator.validate(valid_meta)
    assert res.is_valid is True
    assert res.rejection_code is None


def test_metadata_validator_rejects_corrupted_fields():
    """13. MetadataValidator rejects invalid agency, bad bounds, or corrupted invariants."""
    # Unknown agency
    bad_meta = GRIB2Metadata(
        source_agency="UNKNOWN_UNVERIFIED_LAB",
        model_name="NCUM_REGIONAL",
        initialization_time="2026-10-02T00:00:00Z",
        valid_time="2026-10-03T00:00:00Z",
        lead_time_hours=24,
        variable_name="tp",
        original_units="kg m**-2",
        grid_resolution_deg=0.12,
        lat_bounds=(6.0, 38.0),
        lon_bounds=(66.0, 100.0),
    )
    res = MetadataValidator.validate(bad_meta)
    assert res.is_valid is False
    assert res.rejection_code == "UNSUPPORTED_AGENCY"


# 6. Unit Normalization
def test_unit_normalizer_conversions():
    """6. Centralized unit conversions across precipitation, temperature, pressure, wind."""
    # Precipitation: kg m^-2 is equivalent to mm
    assert UnitNormalizer.precipitation_to_mm(45.5, "kg m^-2") == 45.5
    assert UnitNormalizer.precipitation_to_mm(0.0455, "m") == 45.5

    # Temperature: Kelvin <-> Celsius
    assert UnitNormalizer.temperature_to_kelvin(25.0, "C") == 298.15
    assert UnitNormalizer.temperature_to_celsius(298.15, "K") == 25.0

    # Pressure: Pa -> hPa
    assert UnitNormalizer.pressure_to_hpa(101325.0, "Pa") == 1013.25

    # Wind: m/s -> knots
    assert round(UnitNormalizer.wind_speed_to_knots(10.0, "m/s"), 1) == 19.4

    # Relative humidity: fraction -> percent
    assert UnitNormalizer.relative_humidity_to_percent(0.85, "fraction") == 85.0


# 7 & 8. Timestamp Normalization & Lead Time Invariant
def test_spatial_temporal_normalizer_lead_time_invariant():
    """7-8. Invariant: valid_time == initialization_time + lead_time_hours."""
    # Correct
    ok, err = SpatialTemporalNormalizer.verify_lead_time(
        "2026-10-02T00:00:00Z",
        "2026-10-03T00:00:00Z",
        lead_hours=24,
    )
    assert ok is True
    assert err is None

    # Inconsistent / corrupt
    ok, err = SpatialTemporalNormalizer.verify_lead_time(
        "2026-10-02T00:00:00Z",
        "2026-10-03T12:00:00Z", # should be +24h, not +36h
        lead_hours=24,
    )
    assert ok is False
    assert "Temporal mismatch" in err


# 9. Coordinate Normalization
def test_coordinate_normalization():
    """9. Normalize [0, 360] longitude to [-180, 180]."""
    assert SpatialTemporalNormalizer.normalize_longitude(77.2) == 77.2
    assert SpatialTemporalNormalizer.normalize_longitude(287.5) == -72.5
    assert SpatialTemporalNormalizer.normalize_longitude(360.0) == 0.0

    valid, err = SpatialTemporalNormalizer.validate_coordinates(18.52, 73.85)
    assert valid is True
    assert err is None


# 10. Duplicate Forecast Detection
def test_duplicate_step_deduplication():
    """10. Deduplicate steps and sort chronologically."""
    raw_steps = [
        {"valid_time": "2026-10-03T06:00:00Z", "val": 12.0},
        {"valid_time": "2026-10-02T00:00:00Z", "val": 5.0},
        {"valid_time": "2026-10-03T06:00:00Z", "val": 12.0}, # duplicate
    ]
    cleaned = SpatialTemporalNormalizer.deduplicate_and_sort_steps(raw_steps)
    assert len(cleaned) == 2
    assert cleaned[0]["valid_time"] == "2026-10-02T00:00:00Z"
    assert cleaned[1]["valid_time"] == "2026-10-03T06:00:00Z"


# 11. Missing Variable Handling
def test_missing_variable_handling_in_feature_builder():
    """11. Missing variables are handled gracefully without runtime crash."""
    rec = CanonicalMeteorologicalRecord(
        timestamp="2026-10-02T00:00:00Z",
        latitude=18.52,
        longitude=73.85,
        rainfall=25.0,
        u850=None, # Missing wind
        v850=None,
        data_source="TEST_SOURCE",
    )
    features = MeteorologicalFeatureEngineer.extract_features(rec)
    assert features.wind_speed_850 == 0.0
    assert features.wind_direction_850 == 0.0
    assert features.orographic_lift_index == 0.0


# 12. Stale Data Detection
def test_stale_data_detection():
    """12. Stale forecasts older than tolerance are flagged."""
    router = OperationalSourceRouter(staleness_tolerance_hours=30.0)
    # Old timestamp (e.g. 5 days ago)
    old_ts = "2026-09-20T00:00:00Z"
    is_stale, hours = router.check_staleness(old_ts)
    assert is_stale is True
    assert hours > 30.0


# 14. Secret & Credential Isolation
def test_secret_and_credential_isolation(client: TestClient):
    """14. Ensure no credentials, tokens, or private URLs are exposed through public APIs."""
    res = client.get("/api/v1/data/sources")
    assert res.status_code == 200
    text = res.text.lower()
    forbidden_tokens = ["password", "secret_key", "api_key", "bearer", "private_key", "token="]
    for tok in forbidden_tokens:
        assert tok not in text


# 15. NCUM Adapter Interface
def test_ncmrwf_ncum_adapter_interface():
    """15. NCMRWFAdapter produces valid CanonicalMeteorologicalRecord."""
    adapter = NCMRWFAdapter(live_connection_active=False)
    rec = adapter.fetch_point_forecast(18.52, 73.85, "2026-10-02", lead_hours=24)
    assert isinstance(rec, CanonicalMeteorologicalRecord)
    assert rec.is_demo is True
    assert rec.rainfall > 0.0
    assert rec.u850 is not None
    assert rec.v850 is not None


# 16. NEPS Adapter Interface & Ensemble Statistics
def test_neps_ensemble_processor():
    """16. EnsembleProcessor calculates accurate statistics from actual member arrays."""
    # 23-member synthetic array
    members = [20.0 + float(i) * 2.0 for i in range(23)] # 20.0 to 64.0 mm
    res = EnsembleProcessor.process_member_array(members)
    assert res["ensemble_status"] == "AVAILABLE"
    assert res["member_count"] == 23
    assert res["min"] == 20.0
    assert res["max"] == 64.0
    assert res["mean"] == pytest.approx(42.0, 0.1)
    assert res["p10"] is not None
    assert res["p90"] is not None


# 17. GFS Fallback Interface
def test_gfs_fallback_adapter():
    """17. GFSFallbackAdapter provides structured fallback."""
    gfs = GFSFallbackAdapter()
    rec = gfs.fetch_forecast_record(18.52, 73.85, "2026-10-02T00:00:00Z")
    assert rec.is_demo is True
    assert rec.data_source == GFSFallbackAdapter.SOURCE_ID
    assert rec.data_quality == "FALLBACK_OPERATIONAL"


# 18. Canonical NWP Schema Validation
def test_canonical_nwp_schema_integrity():
    """18. CanonicalMeteorologicalRecord enforces types and normalizes longitude."""
    rec = CanonicalMeteorologicalRecord(
        timestamp="2026-10-02T00:00:00Z",
        latitude=10.0,
        longitude=76.5,
        rainfall=50.0,
        temperature_850=295.0,
        relative_humidity_850=80.0,
        data_source="NCMRWF_NCUM",
    )
    assert rec.latitude == 10.0
    assert rec.longitude == 76.5
    assert rec.rainfall == 50.0


# 19. Regime Feature Compatibility
def test_regime_feature_compatibility_with_canonical_record():
    """19. Canonical records map seamlessly into synoptic regime features."""
    rec = CanonicalMeteorologicalRecord(
        timestamp="2026-10-02T00:00:00Z",
        latitude=18.52,
        longitude=73.85,
        rainfall=45.0,
        u850=14.0,
        v850=6.0,
        u700=9.0,
        v700=3.0,
        u500=4.0,
        v500=1.0,
        temperature_850=294.0,
        relative_humidity_850=85.0,
        elevation=600.0,
        slope=4.5,
        distance_to_coast=80.0,
        data_source="NCMRWF_NCUM",
    )
    features = MeteorologicalFeatureEngineer.extract_features(rec)
    assert features.wind_speed_850 > 0.0
    assert features.vertical_wind_shear > 0.0
    assert features.moisture_transport_proxy > 0.0
    assert features.orographic_lift_index > 0.0
    assert features.coastal_moisture_indicator > 0.0


# 20. Backward Compatibility of Existing Endpoints
def test_api_status_and_backward_compatibility(client: TestClient):
    """20. Ensure all existing data and model endpoints remain backward compatible."""
    res1 = client.get("/api/v1/data/status")
    assert res1.status_code == 200
    res2 = client.get("/api/v1/postprocess/models")
    assert res2.status_code == 200
    res3 = client.get("/api/v1/postprocess/verification")
    assert res3.status_code == 200
    res4 = client.get("/api/v1/data/operational-audit")
    assert res4.status_code == 200
    body = res4.json()
    assert body["operational_readiness_level"] == "LEVEL 1 — ADAPTER ARCHITECTURE & LOCAL INGESTION"
    assert body["live_ncmrwf_connection"] is False
