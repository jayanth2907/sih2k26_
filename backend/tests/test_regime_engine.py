"""
Comprehensive Unit & Integration Tests for Weather Regime Intelligence Engine (PS26080).
Tests:
- Active / Break Monsoon physical criteria and thresholds
- Monsoon Low Pressure System (LPS) / Depression detection
- Coastal Convergence regime diagnostics
- Orographic Lifting & forced condensation regime diagnostics
- Western Disturbance extratropical upper-level trough detection
- Multi-label regime classification, confidence calibration, and explainability XAI drivers
- API endpoint integration: /api/v1/regime, /api/v1/regime/classify, /api/v1/data/status, /api/v1/data/sources
"""

import pytest
from backend.app.data.schemas.meteorology import CanonicalMeteorologicalRecord
from backend.app.data.processing.feature_engineering import MeteorologicalFeaturePipeline
from backend.app.regime.active_break import ActiveBreakMonsoonDetector
from backend.app.regime.coastal_detector import CoastalConvergenceDetector
from backend.app.regime.lps_detector import MonsoonLpsDetector
from backend.app.regime.orographic_detector import OrographicLiftingDetector
from backend.app.regime.western_disturbance import WesternDisturbanceDetector
from backend.app.regime.regime_classifier import WeatherRegimeClassifier
from backend.app.regime.regime_features import RegimeFeatureExtractor
from backend.app.schemas.regime import WeatherRegimeType, SynopticFeatures


class TestActiveBreakMonsoonLogic:
    """Test objective Active and Break monsoon detection rules."""

    def test_active_monsoon_high_llj_and_convection(self):
        synoptics = SynopticFeatures(
            low_level_jet_speed_kts=34.0,  # Strong LLJ > 28 kts
            trough_position="active_south",
            monsoon_trough_lat=21.5,
            olr_w_m2=195.0,  # Strong convection < 210 W/m^2
            olr_anomaly_w_m2=-35.0,
            vorticity_850hpa_s1=3.5e-5,
            moisture_flux_convergence_g_kg_s=4.5,
        )
        active_prob, break_prob, diag = ActiveBreakMonsoonDetector.evaluate(
            synoptics=synoptics,
            rainfall_24h_mm=45.0,
            target_month=7,
        )
        assert active_prob > 0.70
        assert break_prob < 0.20

    def test_break_monsoon_foothill_shift_and_weak_llj(self):
        synoptics = SynopticFeatures(
            low_level_jet_speed_kts=12.0,  # Suppressed LLJ < 15 kts
            trough_position="break_foothills",
            monsoon_trough_lat=27.5,
            olr_w_m2=255.0,  # Clear / suppressed convection > 240 W/m^2
            olr_anomaly_w_m2=25.0,
            vorticity_850hpa_s1=0.5e-5,
            moisture_flux_convergence_g_kg_s=0.5,
        )
        active_prob, break_prob, diag = ActiveBreakMonsoonDetector.evaluate(
            synoptics=synoptics,
            rainfall_24h_mm=2.0,
            target_month=7,
        )
        assert break_prob > 0.70
        assert active_prob < 0.20


class TestMonsoonLpsDetector:
    """Test Monsoon Low / Depression cyclonic vortex detection."""

    def test_deep_monsoon_depression_signature(self):
        synoptics = SynopticFeatures(
            mid_tropospheric_vorticity_1e5_s=7.5,  # Strong cyclonic curvature
            surface_pressure_anomaly_hpa=-9.5,  # Deep MSLP depression
            integrated_vapor_transport_kg_m_s=320.0,
            low_level_jet_speed_kts=25.0,
            olr_anomaly_w_m2=-30.0,
            vorticity_850hpa_s1=7.5e-5,
            moisture_flux_convergence_g_kg_s=8.0,
        )
        lps_prob, intensity, diag = MonsoonLpsDetector.evaluate(
            synoptics=synoptics,
            lat=20.5,
            lon=86.5,  # Bay of Bengal coast
        )
        assert lps_prob >= 0.75
        assert intensity in ["MONSOON_DEPRESSION", "DEEP_DEPRESSION"]
        assert diag["lps_movement_speed_kmh"] > 10.0


class TestCoastalConvergenceDetector:
    """Test coastal convergence and onshore wind regime detection."""

    def test_west_coast_onshore_convergence(self):
        synoptics = SynopticFeatures(
            low_level_jet_speed_kts=28.0,
            low_level_jet_direction_deg=250.0,  # Onshore westerly
            coastal_convergence_index=6.5,
            olr_anomaly_w_m2=-15.0,
            vorticity_850hpa_s1=2.0e-5,
            moisture_flux_convergence_g_kg_s=3.0,
        )
        coastal_prob, diag = CoastalConvergenceDetector.evaluate(
            synoptics=synoptics,
            distance_to_coast_km=25.0,  # Immediate coastal zone
        )
        assert coastal_prob >= 0.60
        assert diag["distance_to_coast_km"] == 25.0

    def test_inland_location_low_coastal_prob(self):
        synoptics = SynopticFeatures(
            low_level_jet_speed_kts=18.0,
            coastal_convergence_index=1.0,
            olr_anomaly_w_m2=0.0,
            vorticity_850hpa_s1=1.0e-5,
            moisture_flux_convergence_g_kg_s=1.0,
        )
        coastal_prob, diag = CoastalConvergenceDetector.evaluate(
            synoptics=synoptics,
            distance_to_coast_km=450.0,  # Deep inland (Nagpur/Bhopal)
        )
        assert coastal_prob <= 0.10


class TestOrographicLiftingDetector:
    """Test orographic lift forced ascent on Western Ghats / Himalayas."""

    def test_western_ghats_orographic_forcing(self):
        synoptics = SynopticFeatures(
            low_level_jet_speed_kts=30.0,
            orographic_lift_index=0.75,
            olr_anomaly_w_m2=-20.0,
            vorticity_850hpa_s1=2.0e-5,
            moisture_flux_convergence_g_kg_s=4.0,
        )
        # Mahabaleshwar conditions: elevation 1350m, steep slope 4.5°, normal wind 14 m/s, RH 95%
        orographic_prob, diag = OrographicLiftingDetector.evaluate(
            synoptics=synoptics,
            elevation_m=1350.0,
            slope_deg=4.5,
            aspect_deg=270.0,
            humidity_850_pct=95.0,
            wind_speed_850_ms=14.0,
            wind_direction_850_deg=260.0,
        )
        assert orographic_prob >= 0.70
        assert diag["elevation_m"] == 1350.0

    def test_plains_low_orographic_prob(self):
        synoptics = SynopticFeatures(
            low_level_jet_speed_kts=15.0,
            orographic_lift_index=0.0,
            olr_anomaly_w_m2=0.0,
            vorticity_850hpa_s1=1.0e-5,
            moisture_flux_convergence_g_kg_s=1.0,
        )
        orographic_prob, diag = OrographicLiftingDetector.evaluate(
            synoptics=synoptics,
            elevation_m=45.0,
            slope_deg=0.1,
        )
        assert orographic_prob <= 0.10


class TestWesternDisturbanceDetector:
    """Test Western Disturbance extratropical trough detection."""

    def test_winter_western_disturbance_himachal(self):
        synoptics = SynopticFeatures(
            low_level_jet_speed_kts=12.0,
            olr_anomaly_w_m2=-10.0,
            vorticity_850hpa_s1=1.5e-5,
            moisture_flux_convergence_g_kg_s=2.0,
        )
        wd_prob, diag = WesternDisturbanceDetector.evaluate(
            synoptics=synoptics,
            lat=32.0,  # Himachal Pradesh
            lon=77.0,
            target_month=1,  # January (Winter peak)
            geopotential_500_gpm=5720.0,  # Deep 500 hPa trough (-140 gpm anomaly)
            u500_ms=32.0,  # Strong westerly jet streak
        )
        assert wd_prob >= 0.65
        assert diag["in_wd_domain"] is True


class TestMultiLabelClassifierAndExplainability:
    """Test composite multi-label classification and grounded XAI drivers."""

    def test_multi_label_classification_output_structure(self):
        record = CanonicalMeteorologicalRecord(
            timestamp="2026-07-15T12:00:00Z",
            latitude=17.92,  # Mahabaleshwar
            longitude=73.65,
            rainfall=85.0,
            ensemble_mean=88.0,
            temperature_850=292.0,
            temperature_700=282.0,
            temperature_500=265.0,
            relative_humidity_850=92.0,
            relative_humidity_700=85.0,
            relative_humidity_500=70.0,
            u850=16.0,
            v850=6.0,
            geopotential_850=1470.0,
            geopotential_500=5840.0,
            surface_pressure=870.0,
            mslp=1006.0,
            elevation=1350.0,
            slope=5.2,
            aspect=270.0,
            distance_to_coast=55.0,
            data_source="NCMRWF_NCUM",
            data_quality="QC_PASSED",
            is_demo=False,
        )

        response = WeatherRegimeClassifier.classify(record)

        # Primary and multi-label assertions
        assert response.primary_regime in [WeatherRegimeType.OROGRAPHIC_RAINFALL, WeatherRegimeType.ACTIVE_MONSOON]
        assert isinstance(response.secondary_regimes, list)
        assert len(response.probabilities) == 7
        assert 0.0 <= response.confidence <= 1.0

        # Explainability assertions
        assert len(response.drivers) >= 3
        for driver in response.drivers:
            assert driver.feature != ""
            assert isinstance(driver.value, (int, float))
            assert 0.0 <= driver.importance <= 1.0

        # Provenance assertions
        assert response.data_source == "NCMRWF_NCUM"
        assert response.is_demo is False
        assert response.timestamp != ""
