"""Post-Processing and Verification Service for PS26080 (MoES / NCMRWF)."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from backend.app.postprocessing.base import PostProcessingInput
from backend.app.postprocessing.inference import PostProcessingInferenceEngine
from backend.app.schemas.common import Coordinates
from backend.app.schemas.postprocess import (
    DistrictForecast,
    HeavyRainfallProbabilities,
    PostProcessingComparison,
    ProductDetail,
    ProbabilityTier,
    VerificationMetricSet,
    VerificationResponse,
)
from backend.app.schemas.regime import RegimeResponse, WeatherRegimeType
from backend.app.services.base import BaseService

logger = logging.getLogger("rainfall_backend.services.postprocessing_service")


class PostProcessingService(BaseService):
    """
    Regime-Aware Post-Processing and Spatial Bias Calibration Service.
    Implements 4 comparison products:
    1. Raw NWP (Baseline NCUM / GFS Fallback)
    2. Empirical Quantile Mapping (EQM)
    3. Global ML Correction (Standard non-regime Histogram Gradient Boosting)
    4. Regime-Aware AI Post-Processing (Target MoES/NCMRWF Soft-Conditioned Architecture)
    """

    def __init__(self):
        super().__init__(
            name="PostProcessingService",
            description="4-Product forecast post-processing, probability calibration, and verification benchmarks",
        )
        self.engine = PostProcessingInferenceEngine.get_instance()

    def check_connection(self) -> bool:
        return True

    def generate_products(
        self,
        raw_nwp_accumulated_mm: float,
        raw_peak_hourly_rate: float,
        raw_hourly_series: List[float],
        regime: RegimeResponse,
        coordinates: Coordinates,
        location_name: Optional[str] = None,
    ) -> Tuple[PostProcessingComparison, HeavyRainfallProbabilities, DistrictForecast, VerificationResponse]:
        """
        Generate 4 post-processing products, probability distributions, district aggregations, and verification skill.
        """
        raw_mm = max(0.0, raw_nwp_accumulated_mm)
        regime_str = regime.primary_regime.value if isinstance(regime.primary_regime, WeatherRegimeType) else str(regime.primary_regime)

        # Build PostProcessingInput payload
        sample = PostProcessingInput(
            raw_nwp_rainfall=raw_mm,
            lead_time_hours=24,
            latitude=coordinates.latitude,
            longitude=coordinates.longitude,
            month=7,
            day_of_year=200,
            regime_probabilities=regime.probabilities if regime.probabilities else {regime_str: 0.85},
            primary_regime=regime_str,
            regime_confidence=regime.confidence if regime.confidence is not None else 0.85,
            data_source=regime.data_source,
            is_demo=regime.is_demo,
        )

        comparison_summary = self.engine.compare_all(sample)
        comparison = self.engine.comparison_engine.to_legacy_comparison_schema(comparison_summary)

        # Update peak rates and hourly series from provided series if available
        if raw_hourly_series and len(raw_hourly_series) >= 24:
            comparison.raw_nwp.hourly_series = [round(x, 2) for x in raw_hourly_series[:24]]
            comparison.raw_nwp.peak_hourly_rate_mm_hr = round(max(raw_hourly_series[:24]), 2)
            
            # Scale hourly curves proportionally for post-processed models
            scale_qm = comparison.quantile_mapping.accumulated_24h_mm / max(1.0, raw_mm)
            comparison.quantile_mapping.hourly_series = [round(x * scale_qm, 2) for x in raw_hourly_series[:24]]
            comparison.quantile_mapping.peak_hourly_rate_mm_hr = round(max(comparison.quantile_mapping.hourly_series), 2)

            scale_global = comparison.global_ml_correction.accumulated_24h_mm / max(1.0, raw_mm)
            comparison.global_ml_correction.hourly_series = [round(x * scale_global, 2) for x in raw_hourly_series[:24]]
            comparison.global_ml_correction.peak_hourly_rate_mm_hr = round(max(comparison.global_ml_correction.hourly_series), 2)

            scale_regime = comparison.regime_aware_ml_correction.accumulated_24h_mm / max(1.0, raw_mm)
            comparison.regime_aware_ml_correction.hourly_series = [round(x * scale_regime, 2) for x in raw_hourly_series[:24]]
            comparison.regime_aware_ml_correction.peak_hourly_rate_mm_hr = round(max(comparison.regime_aware_ml_correction.hourly_series), 2)

        # Heavy rainfall probabilities from regime-aware model
        p_heavy = comparison_summary.regime_aware_ml.heavy_rain_prob_ge_64_5mm
        p_vheavy = comparison_summary.regime_aware_ml.very_heavy_rain_prob_ge_115_6mm
        p_extreme = comparison_summary.regime_aware_ml.extreme_rain_prob_ge_204_5mm

        probabilities = HeavyRainfallProbabilities(
            heavy_rainfall_ge_64_5mm=ProbabilityTier(
                probability=round(p_heavy, 3),
                predicted=p_heavy >= 0.55,
                threshold_mm=64.5,
                category="Heavy Rainfall (64.5 - 115.5 mm/day)",
            ),
            very_heavy_rainfall_ge_115_6mm=ProbabilityTier(
                probability=round(p_vheavy, 3),
                predicted=p_vheavy >= 0.40,
                threshold_mm=115.6,
                category="Very Heavy Rainfall (115.6 - 204.4 mm/day)",
            ),
            extremely_heavy_rainfall_ge_204_5mm=ProbabilityTier(
                probability=round(p_extreme, 3),
                predicted=p_extreme >= 0.25,
                threshold_mm=204.5,
                category="Extremely Heavy Rainfall (>= 204.5 mm/day)",
            ),
        )

        # District Forecast
        from backend.app.data.sources.districts import DistrictProvider
        dist_meta = DistrictProvider.lookup_district(coordinates.latitude, coordinates.longitude)
        dist_name = location_name or dist_meta.get("district", "Target Meteorological District")
        state_name = dist_meta.get("state", "Monsoon Monitoring Zone")
        dist_id = dist_meta.get("district_id", f"{state_name[:2].upper()}_{dist_name.replace(' ', '_').upper()}")
        reg_conf = getattr(regime, "confidence", 0.85) or 0.85

        district_forecast = self.engine.generate_district_forecast(
            district_id=dist_id,
            district_name=dist_name,
            state_name=state_name,
            lat=coordinates.latitude,
            lon=coordinates.longitude,
            raw_nwp_mm=raw_mm,
            regime_output=comparison_summary.regime_aware_ml,
            dominant_regime=regime_str,
            regime_confidence=reg_conf,
        )


        # Verification Response
        verification = self.engine.get_verification_benchmarks(regime_filter=regime_str, threshold_mm=64.5)

        return comparison, probabilities, district_forecast, verification
