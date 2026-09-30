"""
Comprehensive Unit & Integration Tests for Meteorological Data Pipeline (PS26080).
Tests:
- Wind vector calculations (speed, direction, vertical shear)
- Humidity and thermodynamic validations (Tetens formula, RH bounds 0-100%)
- Rainfall physical quality control (negative handling, accumulation, unit conversion)
- Spatial normalization, longitude wrapping [-180, 180], Haversine & bilinear regridding
- Temporal alignment, lead-time computation, and causality enforcement (no future leakage)
- Data source adapters (NCMRWF NCUM/NEPS, ERA5, IMD, IMERG, GFS, Terrain, Districts)
- Transparent DEMO flag tagging and QC audit logging
"""

import pytest
from datetime import datetime, timezone
from backend.app.data.schemas.meteorology import (
    CanonicalMeteorologicalRecord,
    MeteorologicalFeatureSet,
    QualityControlLog,
)
from backend.app.data.processing.quality_control import MeteorologicalQualityControl
from backend.app.data.processing.regrid import SpatialGridStandardizer
from backend.app.data.processing.temporal_alignment import TemporalAligner
from backend.app.data.processing.feature_engineering import MeteorologicalFeaturePipeline
from backend.app.data.sources.ncmrwf import NCMRWFAdapter
from backend.app.data.sources.era5 import ERA5Adapter
from backend.app.data.sources.imerg import IMERGAdapter
from backend.app.data.sources.imd import IMDGriddedAdapter
from backend.app.data.sources.gfs import GFSFallbackAdapter
from backend.app.data.sources.terrain import TerrainSource
from backend.app.data.sources.districts import DistrictsSource


class TestWindCalculations:
    """Test wind speed, direction, and vertical wind shear physics."""

    def test_wind_speed_and_direction_westerlies(self):
        # Pure westerly wind (u=10, v=0) -> Speed=10 m/s, Direction=270° (from West)
        speed, direction = MeteorologicalFeaturePipeline.calculate_wind_speed_and_direction(u=10.0, v=0.0)
        assert pytest.approx(speed, 0.01) == 10.0
        assert pytest.approx(direction, 0.01) == 270.0

    def test_wind_speed_and_direction_southwesterlies(self):
        # Southwest monsoon wind (u=10, v=10) -> Speed=14.14 m/s, Direction=225° (from SW)
        speed, direction = MeteorologicalFeaturePipeline.calculate_wind_speed_and_direction(u=10.0, v=10.0)
        assert pytest.approx(speed, 0.01) == 14.14
        assert pytest.approx(direction, 0.01) == 225.0

    def test_wind_speed_and_direction_easterlies(self):
        # Pure easterly wind (u=-10, v=0) -> Speed=10 m/s, Direction=90° (from East)
        speed, direction = MeteorologicalFeaturePipeline.calculate_wind_speed_and_direction(u=-10.0, v=0.0)
        assert pytest.approx(speed, 0.01) == 10.0
        assert pytest.approx(direction, 0.01) == 90.0

    def test_vertical_wind_shear(self):
        # 850 hPa: (u=15, v=5), 500 hPa: (u=5, v=2)
        # Vector difference: du = -10, dv = -3 -> shear = sqrt(100 + 9) = sqrt(109) = 10.44 m/s
        shear = MeteorologicalFeaturePipeline.calculate_vertical_wind_shear(
            u_low=15.0, v_low=5.0, u_high=5.0, v_high=2.0
        )
        assert pytest.approx(shear, 0.01) == 10.44


class TestHumidityAndThermodynamics:
    """Test relative humidity validation, capping, and specific humidity derivations."""

    def test_rh_bounds_valid(self):
        qc = MeteorologicalQualityControl()
        val, log = qc.sanitize_relative_humidity(85.5, "relative_humidity_850")
        assert val == 85.5
        assert log is None

    def test_rh_negative_capped_to_zero(self):
        qc = MeteorologicalQualityControl()
        val, log = qc.sanitize_relative_humidity(-12.0, "relative_humidity_850")
        assert val == 0.0
        assert log is not None
        assert log.action_taken == "CORRECTED"

    def test_rh_oversaturated_capped_to_100(self):
        qc = MeteorologicalQualityControl()
        val, log = qc.sanitize_relative_humidity(108.4, "relative_humidity_850")
        assert val == 100.0
        assert log is not None
        assert log.action_taken == "CAPPED"

    def test_specific_humidity_tetens(self):
        # At T = 20°C (293.15 K), P = 850 hPa, RH = 80%
        # Saturation vapor pressure ~ 23.38 hPa -> e ~ 18.7 hPa -> q ~ 13.8 g/kg
        q = MeteorologicalFeaturePipeline.compute_specific_humidity(
            temp_k=293.15, rh_percent=80.0, pressure_hpa=850.0
        )
        assert 10.0 <= q <= 18.0


class TestRainfallValidationAndQC:
    """Test rainfall rate bounds, accumulation curves, and unit normalization."""

    def test_negative_rainfall_correction(self):
        qc = MeteorologicalQualityControl()
        val, log = qc.sanitize_rainfall(-5.5)
        assert val == 0.0
        assert log is not None
        assert log.action_taken == "CORRECTED"

    def test_extreme_rainfall_capped(self):
        qc = MeteorologicalQualityControl()
        val, log = qc.sanitize_rainfall(1850.0, is_daily=True)
        assert val == 1500.0
        assert log is not None
        assert log.action_taken == "CAPPED"

    def test_pressure_unit_conversion_pa_to_hpa(self):
        qc = MeteorologicalQualityControl()
        # 101325 Pa -> 1013.25 hPa
        val, log = qc.sanitize_mslp(101325.0)
        assert pytest.approx(val, 0.01) == 1013.25
        assert log is not None
        assert log.action_taken == "CORRECTED"


class TestSpatialStandardization:
    """Test coordinate wrapping, distance, bearing, and bilinear interpolation."""

    def test_longitude_normalization_wrapping(self):
        # Longitude 190° should normalize to -170°
        lon_wrapped = SpatialGridStandardizer.normalize_longitude(190.0)
        assert lon_wrapped == -170.0

        # Longitude -195° should normalize to 165°
        lon_wrapped_neg = SpatialGridStandardizer.normalize_longitude(-195.0)
        assert lon_wrapped_neg == 165.0

    def test_haversine_distance_mumbai_to_pune(self):
        # Mumbai (19.0760, 72.8777) to Pune (18.5204, 73.8567) is ~120 km
        dist_km = SpatialGridStandardizer.haversine_distance(19.0760, 72.8777, 18.5204, 73.8567)
        assert 110.0 <= dist_km <= 135.0

    def test_initial_compass_bearing(self):
        # Northward bearing: (0, 0) to (10, 0) is 0°
        bearing_n = SpatialGridStandardizer.calculate_initial_bearing(0.0, 0.0, 10.0, 0.0)
        assert pytest.approx(bearing_n, 0.1) == 0.0

        # Eastward bearing: (0, 0) to (0, 10) is 90°
        bearing_e = SpatialGridStandardizer.calculate_initial_bearing(0.0, 0.0, 0.0, 10.0)
        assert pytest.approx(bearing_e, 0.1) == 90.0

    def test_bilinear_interpolation_2d_grid(self):
        grid = [
            [10.0, 20.0],
            [30.0, 40.0],
        ]
        lats = [20.0, 21.0]
        lons = [70.0, 71.0]

        # Center interpolation at (20.5, 70.5) should yield average: (10+20+30+40)/4 = 25.0
        val = SpatialGridStandardizer.bilinear_interpolate(grid, lats, lons, target_lat=20.5, target_lon=70.5)
        assert pytest.approx(val, 0.01) == 25.0


class TestTemporalAlignmentAndCausality:
    """Test lead-time calculations and causality verification (no lookahead bias)."""

    def test_lead_time_calculation(self):
        init_time = "2026-07-15T00:00:00Z"
        valid_time = "2026-07-16T00:00:00Z"
        lead_hrs = TemporalAligner.calculate_lead_time_hours(init_time, valid_time)
        assert lead_hrs == 24

    def test_valid_temporal_causality_pass(self):
        # Observation at T+0 is available at initialization
        init_time = "2026-07-15T00:00:00Z"
        obs_time = "2026-07-14T18:00:00Z"
        assert TemporalAligner.verify_no_data_leakage(obs_time, init_time) is True

    def test_lookahead_bias_detection(self):
        # Observation timestamp is in the future relative to forecast initialization -> REJECT with ValueError
        init_time = "2026-07-15T00:00:00Z"
        future_obs_time = "2026-07-16T12:00:00Z"
        with pytest.raises(ValueError) as exc:
            TemporalAligner.verify_no_data_leakage(future_obs_time, init_time)
        assert "Data Leakage Detected" in str(exc.value)


class TestDataSourceAdapters:
    """Test all 7 modular meteorological data sources and DEMO labeling."""

    def test_ncmrwf_adapter_demo_tagging(self):
        adapter = NCMRWFAdapter(live_connection_active=False)
        record = adapter.fetch_point_forecast(19.0760, 72.8777, "2026-07-15")
        assert record.is_demo is True
        assert record.data_source == "NCMRWF_NCUM_DEMO_SYNTHESIS"
        assert record.data_quality == "DEMO_UNVERIFIED"

    def test_era5_adapter_reanalysis(self):
        adapter = ERA5Adapter()
        record = adapter.fetch_reanalysis_point(19.0760, 72.8777, "2023-07-15T12:00:00Z")
        assert record.is_demo is False
        assert record.data_source == "ECMWF_ERA5_REANALYSIS"

    def test_imerg_satellite_precipitation(self):
        adapter = IMERGAdapter()
        record = adapter.fetch_precipitation_estimate(19.0760, 72.8777, "2026-07-15T12:00:00Z")
        assert record.rainfall >= 0.0
        assert record.is_demo is False

    def test_imd_gridded_observation(self):
        adapter = IMDGriddedAdapter()
        record = adapter.fetch_daily_observation(19.0760, 72.8777, "2026-07-15")
        assert record.rainfall >= 0.0
        assert record.is_demo is False

    def test_gfs_fallback_adapter(self):
        adapter = GFSFallbackAdapter()
        record = adapter.fetch_forecast_record(19.0760, 72.8777, "2026-07-15T12:00:00Z")
        assert record.is_demo is True
        assert record.data_source == "NOAA_GFS_OPENMETEO_FALLBACK"

    def test_terrain_source_western_ghats(self):
        # Mahabaleshwar coordinates (17.92, 73.65) -> High elevation & steep slope
        topo = TerrainSource.get_terrain_features(17.92, 73.65)
        assert topo.elevation > 400.0
        assert topo.slope > 1.0

    def test_districts_source_lookup(self):
        dists = DistrictsSource.get_all_districts()
        assert len(dists) >= 10
        mumbai = DistrictsSource.find_district_by_coords(19.0760, 72.8777)
        assert mumbai is not None
        assert "Mumbai" in mumbai["district"]
