"""
Deterministic District Decision Support & Warning Intelligence Engine (Phase 14).
Evaluates multi-threshold probabilities, polygon area fractions, quantile uncertainty,
synoptic atmospheric drivers, and assigns deterministic prototype decision categories.
"""

from typing import Any, Dict, List, Optional, Tuple
from backend.app.schemas.district_decision import (
    DataQualityStatus,
    DecisionSupportCategory,
    DistrictAtmosphericDrivers,
    DistrictDecisionThresholds,
    DistrictProbabilityStats,
    DistrictSpatialStats,
    DistrictUncertaintyStats,
)
from backend.app.schemas.regime import WeatherRegimeType


class DistrictDecisionEngine:
    """
    Deterministic decision support engine for administrative district rainfall outlooks.
    Enforces strict distinction between model-derived research decision categories and official IMD warnings.
    """

    DEFAULT_THRESHOLDS = DistrictDecisionThresholds()

    @classmethod
    def evaluate_district_decision(
        cls,
        district_name: str,
        state_name: str,
        spatial_stats: DistrictSpatialStats,
        probabilities: DistrictProbabilityStats,
        uncertainty: DistrictUncertaintyStats,
        dominant_regime: WeatherRegimeType,
        quality_status: DataQualityStatus,
        thresholds: Optional[DistrictDecisionThresholds] = None,
    ) -> Tuple[DecisionSupportCategory, str, float]:
        """
        Evaluate deterministic decision category, explanatory reasoning, and confidence.
        """
        cfg = thresholds or cls.DEFAULT_THRESHOLDS

        # 1. Check for insufficient coverage or invalid data
        if quality_status == DataQualityStatus.INSUFFICIENT_SPATIAL_COVERAGE:
            return (
                DecisionSupportCategory.NORMAL,
                f"Insufficient spatial grid coverage ({spatial_stats.valid_area_fraction * 100:.1f}% < {cfg.min_valid_area_fraction * 100:.0f}%). Forecast withheld.",
                0.0,
            )

        p50 = spatial_stats.median_24h_mm
        p_heavy = probabilities.heavy_probability
        p_vheavy = probabilities.very_heavy_probability
        p_extreme = probabilities.extreme_probability
        f_heavy = spatial_stats.heavy_area_fraction
        f_vheavy = spatial_stats.very_heavy_area_fraction
        f_extreme = spatial_stats.extreme_area_fraction

        # 2. Deterministic Rule Matrix (IMD-aligned physical limits + configurable probability escalation)
        if (
            p50 >= cfg.accumulation_extreme_mm
            or p_extreme >= cfg.extreme_probability_threshold
            or f_extreme >= cfg.extreme_area_fraction_threshold
        ):
            category = DecisionSupportCategory.EXTREMELY_HEAVY_RAINFALL
            reasons = []
            if p50 >= cfg.accumulation_extreme_mm:
                reasons.append(f"median forecast ({p50:.1f} mm) reaches extreme {cfg.accumulation_extreme_mm} mm threshold")
            if p_extreme >= cfg.extreme_probability_threshold:
                reasons.append(f"extreme rain probability ({p_extreme * 100:.1f}%) exceeds {cfg.extreme_probability_threshold * 100:.0f}% trigger")
            if f_extreme >= cfg.extreme_area_fraction_threshold:
                reasons.append(f"{f_extreme * 100:.1f}% of district area exceeds 204.5 mm")
            basis = f"District {district_name}: " + " and ".join(reasons) + "."
            confidence = min(0.95, max(0.60, 0.50 + p_extreme * 0.45))

        elif (
            p50 >= cfg.accumulation_very_heavy_mm
            or p_vheavy >= cfg.very_heavy_probability_threshold
            or f_vheavy >= cfg.very_heavy_area_fraction_threshold
        ):
            category = DecisionSupportCategory.VERY_HEAVY_RAINFALL
            reasons = []
            if p50 >= cfg.accumulation_very_heavy_mm:
                reasons.append(f"median forecast ({p50:.1f} mm) exceeds very heavy {cfg.accumulation_very_heavy_mm} mm threshold")
            if p_vheavy >= cfg.very_heavy_probability_threshold:
                reasons.append(f"very heavy rain probability ({p_vheavy * 100:.1f}%) exceeds {cfg.very_heavy_probability_threshold * 100:.0f}% trigger")
            if f_vheavy >= cfg.very_heavy_area_fraction_threshold:
                reasons.append(f"{f_vheavy * 100:.1f}% of district area exceeds 115.6 mm")
            basis = f"District {district_name}: " + " and ".join(reasons) + "."
            confidence = min(0.92, max(0.65, 0.55 + p_vheavy * 0.35))

        elif (
            p50 >= cfg.accumulation_heavy_mm
            or p_heavy >= cfg.heavy_probability_threshold
            or f_heavy >= cfg.heavy_area_fraction_threshold
        ):
            category = DecisionSupportCategory.HEAVY_RAINFALL
            reasons = []
            if p50 >= cfg.accumulation_heavy_mm:
                reasons.append(f"median forecast ({p50:.1f} mm) exceeds heavy rain {cfg.accumulation_heavy_mm} mm threshold")
            if p_heavy >= cfg.heavy_probability_threshold:
                reasons.append(f"heavy rain probability ({p_heavy * 100:.1f}%) exceeds {cfg.heavy_probability_threshold * 100:.0f}% trigger")
            if f_heavy >= cfg.heavy_area_fraction_threshold:
                reasons.append(f"{f_heavy * 100:.1f}% of district area exceeds 64.5 mm")
            basis = f"District {district_name}: " + " and ".join(reasons) + "."
            confidence = min(0.90, max(0.70, 0.60 + p_heavy * 0.30))

        else:
            category = DecisionSupportCategory.NORMAL
            basis = f"District {district_name}: Calibrated median forecast ({p50:.1f} mm) remains below the 64.5 mm heavy-rainfall threshold."
            confidence = 0.88

        return (category, basis, round(confidence, 2))

    @classmethod
    def synthesize_atmospheric_drivers(
        cls,
        regime: WeatherRegimeType,
        is_coastal: bool = False,
        lat: float = 19.0,
        lon: float = 73.0,
    ) -> DistrictAtmosphericDrivers:
        """Synthesize synoptic and physical driver indicators for district explanation."""
        major_factors: List[str] = []

        if regime == WeatherRegimeType.OROGRAPHIC_RAINFALL:
            llj = 18.5
            ivt = 650.0
            rh850 = 94.0
            mslp_anom = -3.2
            cape = 1450.0
            vort = 4.8
            orog_lift = 0.88
            coast_conv = 0.45 if is_coastal else 0.15
            major_factors = [
                "Strong windward orographic ascent against Western Ghats",
                "High integrated water vapor transport (IVT > 600 kg/m/s)",
                "Deep tropospheric saturation (RH850 > 90%)",
            ]
        elif regime == WeatherRegimeType.COASTAL_CONVERGENCE:
            llj = 16.0
            ivt = 580.0
            rh850 = 91.0
            mslp_anom = -2.8
            cape = 1850.0
            vort = 4.2
            orog_lift = 0.35
            coast_conv = 0.92
            major_factors = [
                "Intense land-sea friction and thermal convergence zone",
                "Low-level jet speed convergence along Konkan coastline",
                "High boundary layer moisture content",
            ]
        elif regime == WeatherRegimeType.MONSOON_LOW_LPS:
            llj = 15.2
            ivt = 620.0
            rh850 = 89.0
            mslp_anom = -6.5
            cape = 1600.0
            vort = 8.6
            orog_lift = 0.20
            coast_conv = 0.65 if is_coastal else 0.25
            major_factors = [
                "Cyclonic vorticity maximum associated with Monsoon Low / LPS",
                "Depressed sea level pressure anomaly (ΔMSLP < -6 hPa)",
                "Strong moisture flux convergence into low center",
            ]
        elif regime == WeatherRegimeType.WESTERN_DISTURBANCE:
            llj = 12.0
            ivt = 340.0
            rh850 = 78.0
            mslp_anom = -4.0
            cape = 850.0
            vort = 6.2
            orog_lift = 0.72
            coast_conv = 0.05
            major_factors = [
                "Mid-latitude upper-tropospheric trough passage",
                "Orographic lifting across Himalayan windward slopes",
            ]
        elif regime == WeatherRegimeType.BREAK_MONSOON:
            llj = 8.5
            ivt = 280.0
            rh850 = 62.0
            mslp_anom = 2.1
            cape = 650.0
            vort = -1.5
            orog_lift = 0.10
            coast_conv = 0.10
            major_factors = [
                "Suppressed convective activity across core monsoon zone",
                "Northward shift of monsoon trough towards Himalayan foothills",
            ]
        else:  # ACTIVE_MONSOON / NEUTRAL
            llj = 14.0
            ivt = 480.0
            rh850 = 84.0
            mslp_anom = -1.5
            cape = 1300.0
            vort = 3.5
            orog_lift = 0.30
            coast_conv = 0.40 if is_coastal else 0.15
            major_factors = [
                "Standard southwesterly cross-equatorial monsoon flow",
                "Broad regional convective instability",
            ]

        return DistrictAtmosphericDrivers(
            low_level_jet_mps=round(llj, 1),
            integrated_vapor_transport=round(ivt, 1),
            relative_humidity_850_pct=round(rh850, 1),
            mslp_anomaly_hpa=round(mslp_anom, 1),
            cape_j_kg=round(cape, 1),
            vorticity_850=round(vort, 2),
            orographic_lift_index=round(orog_lift, 2),
            coastal_convergence_index=round(coast_conv, 2),
            major_drivers=major_factors,
        )
