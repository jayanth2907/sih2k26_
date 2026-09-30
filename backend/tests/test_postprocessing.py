"""
Unit Tests for PS26080 Post-Processing Foundations.
Tests:
- Base model contract & data structures
- Dataset generation and strict chronological splits (no temporal leakage)
- Feature vector extraction (44 dimensions)
- Uncertainty quantification (P10 <= P50 <= P90, non-negative)
- Heavy rainfall probability calibration (monotonicity, thresholds)
"""

import numpy as np
import pytest

from backend.app.postprocessing.base import (
    BasePostProcessingModel,
    PostProcessingInput,
    PostProcessingOutput,
)
from backend.app.postprocessing.datasets import (
    DatasetGenerator,
    FEATURE_NAMES,
    PostProcessingDataset,
    extract_feature_vector,
)
from backend.app.postprocessing.heavy_rain import HeavyRainfallCalibrator
from backend.app.postprocessing.uncertainty import UncertaintyQuantifier
from backend.app.schemas.regime import WeatherRegimeType


def test_postprocessing_input_validation():
    """Verify PostProcessingInput schema validation and feature access."""
    sample = PostProcessingInput(
        raw_nwp_rainfall=45.0,
        lead_time_hours=24,
        latitude=19.07,
        longitude=72.87,
        month=7,
        day_of_year=200,
        primary_regime="ACTIVE_MONSOON",
        regime_probabilities={"ACTIVE_MONSOON": 0.8, "BREAK_MONSOON": 0.05},
        is_demo=True,
    )
    assert sample.raw_nwp_rainfall == 45.0
    assert sample.lead_time_hours == 24
    assert sample.month == 7
    assert sample.is_demo is True
    assert sample.primary_regime == "ACTIVE_MONSOON"


def test_postprocessing_output_physical_constraints():
    """Ensure PostProcessingOutput respects physical non-negativity and bounds."""
    output = PostProcessingOutput(
        model_id="regime_aware_ml",
        model_name="Regime-Aware AI Post-Processing",
        raw_rainfall_24h_mm=30.0,
        corrected_rainfall_24h_mm=42.5,
        predicted_bias_delta_mm=12.5,
        rainfall_p10_mm=25.0,
        rainfall_p50_mm=42.5,
        rainfall_p90_mm=60.0,
        uncertainty_width_mm=35.0,
        heavy_rain_prob_ge_64_5mm=0.35,
        very_heavy_rain_prob_ge_115_6mm=0.10,
        extreme_rain_prob_ge_204_5mm=0.02,
        primary_regime="ACTIVE_MONSOON",
        regime_confidence=0.85,
        data_source="NCMRWF_NCUM",
        is_demo=True,
    )
    assert output.corrected_rainfall_24h_mm >= 0.0
    assert output.rainfall_p10_mm >= 0.0
    assert output.rainfall_p10_mm <= output.rainfall_p50_mm <= output.rainfall_p90_mm
    assert output.uncertainty_width_mm == pytest.approx(output.rainfall_p90_mm - output.rainfall_p10_mm)


def test_extract_feature_vector_dimensionality_and_values():
    """Verify feature vector extraction yields exact 44 numeric features."""
    sample = PostProcessingInput(
        raw_nwp_rainfall=50.0,
        lead_time_hours=48,
        latitude=18.9,
        longitude=72.8,
        month=8,
        day_of_year=220,
        wind_speed_850=16.0,
        wind_direction_850=250.0,
        elevation=120.0,
        slope=2.5,
        distance_to_coast=5.0,
        primary_regime="COASTAL_CONVERGENCE",
        regime_probabilities={
            "ACTIVE_MONSOON": 0.2,
            "COASTAL_CONVERGENCE": 0.7,
            "BREAK_MONSOON": 0.02,
        },
        is_demo=True,
    )
    vec = extract_feature_vector(sample)
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (44,)
    assert not np.isnan(vec).any()
    assert not np.isinf(vec).any()
    assert vec[0] == pytest.approx(50.0)  # raw_nwp_rainfall
    assert vec[1] == pytest.approx(48.0)  # lead_time_hours


def test_chronological_splits_and_zero_future_leakage():
    """
    Strictly verify zero future data leakage across chronological partitions:
    - Train: 2018–2022
    - Val: 2023
    - Test: 2024–2025
    """
    train_ds = DatasetGenerator.generate_synthetic_dataset(split="train", seed=42)
    val_ds = DatasetGenerator.generate_synthetic_dataset(split="val", seed=42)
    test_ds = DatasetGenerator.generate_synthetic_dataset(split="test", seed=42)

    train_years = {int(ts[:4]) for ts in train_ds.timestamps}
    val_years = {int(ts[:4]) for ts in val_ds.timestamps}
    test_years = {int(ts[:4]) for ts in test_ds.timestamps}

    assert train_years.issubset({2018, 2019, 2020, 2021, 2022})
    assert val_years == {2023}
    assert test_years.issubset({2024, 2025})

    # Assert no overlap between splits
    assert train_years.isdisjoint(val_years)
    assert train_years.isdisjoint(test_years)
    assert val_years.isdisjoint(test_years)

    # Assert target is strictly residual: y = observed - raw_nwp
    for ds in (train_ds, val_ds, test_ds):
        np.testing.assert_allclose(ds.y_residual, ds.observed - ds.raw_nwp, rtol=1e-4, atol=1e-4)


def test_uncertainty_quantifier():
    """Test UncertaintyQuantifier bounds, percentiles, and category assignment."""
    quantifier = UncertaintyQuantifier()

    # Deterministic estimate
    res = quantifier.estimate_uncertainty(corrected_rainfall_mm=80.0, model_id="regime_aware_ml")
    assert res.p10_mm <= res.p50_mm <= res.p90_mm
    assert res.p10_mm >= 0.0
    assert res.uncertainty_width_mm == pytest.approx(res.p90_mm - res.p10_mm, abs=0.01)

    # Category checks
    res_low = quantifier.estimate_uncertainty(corrected_rainfall_mm=10.0, model_id="regime_aware_ml")
    assert res_low.uncertainty_category in ("LOW", "MODERATE", "HIGH", "EXTREME")

    res_extreme = quantifier.estimate_uncertainty(corrected_rainfall_mm=250.0, model_id="raw_nwp")
    assert res_extreme.uncertainty_category in ("HIGH", "EXTREME")


def test_heavy_rainfall_calibrator():
    """Test HeavyRainfallCalibrator probabilities and monotonic threshold ordering."""
    calibrator = HeavyRainfallCalibrator()

    # Moderate rain (50mm) -> heavy prob moderate, very heavy low, extreme near 0
    probs_50 = calibrator.calculate_probabilities(rainfall_mm=50.0, uncertainty_spread_mm=8.0)
    assert 0.0 <= probs_50.heavy_prob_ge_64_5mm <= 1.0
    assert 0.0 <= probs_50.very_heavy_prob_ge_115_6mm <= 1.0
    assert 0.0 <= probs_50.extreme_prob_ge_204_5mm <= 1.0
    assert probs_50.heavy_prob_ge_64_5mm >= probs_50.very_heavy_prob_ge_115_6mm >= probs_50.extreme_prob_ge_204_5mm

    # Extreme rain (220mm) -> high probabilities across all tiers
    probs_220 = calibrator.calculate_probabilities(rainfall_mm=220.0, uncertainty_spread_mm=15.0)
    assert probs_220.heavy_prob_ge_64_5mm > 0.85
    assert probs_220.very_heavy_prob_ge_115_6mm > 0.70
    assert probs_220.extreme_prob_ge_204_5mm > 0.40
    assert probs_220.heavy_prob_ge_64_5mm >= probs_220.very_heavy_prob_ge_115_6mm >= probs_220.extreme_prob_ge_204_5mm
    assert "Extremely Heavy" in probs_220.imd_warning_category
