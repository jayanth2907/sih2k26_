"""
Multi-Label Weather Regime Classification Engine for PS26080.
Combines rule-based physical atmospheric diagnostics with probabilistic calibration
to identify Primary and Secondary South Asian Monsoon regimes with grounded XAI drivers.
"""

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional, Tuple

from backend.app.data.schemas.meteorology import CanonicalMeteorologicalRecord, MeteorologicalFeatureSet
from backend.app.regime.active_break import ActiveBreakMonsoonDetector
from backend.app.regime.coastal_detector import CoastalConvergenceDetector
from backend.app.regime.lps_detector import MonsoonLpsDetector
from backend.app.regime.orographic_detector import OrographicLiftingDetector
from backend.app.regime.regime_features import RegimeFeatureExtractor
from backend.app.regime.western_disturbance import WesternDisturbanceDetector
from backend.app.schemas.regime import AtmosphericDriver, RegimeResponse, SynopticFeatures, WeatherRegimeType


class WeatherRegimeClassifier:
    """
    Hybrid Multi-Label Synoptic Regime Classifier.
    Integrates 6 specialized atmospheric regime detectors into a calibrated multi-label output.
    """

    MODEL_VERSION = "RegimeClassifier_v2.0_Hybrid"

    @classmethod
    def classify(
        cls,
        record: CanonicalMeteorologicalRecord,
        derived_features: Optional[MeteorologicalFeatureSet] = None,
        target_month: Optional[int] = None,
    ) -> RegimeResponse:
        """
        Classify synoptic and mesoscale weather regimes from a canonical meteorological record.

        Parameters
        ----------
        record : CanonicalMeteorologicalRecord
            Canonical standardized meteorological record.
        derived_features : MeteorologicalFeatureSet, optional
            Pre-computed derived features (if None, derived on the fly).
        target_month : int, optional
            Calendar month. If None, extracted from record timestamp.

        Returns
        -------
        RegimeResponse
            Full regime response with primary, secondary regimes, probability distribution, and top XAI drivers.
        """
        # Determine target month from record timestamp
        if target_month is None:
            try:
                dt = datetime.fromisoformat(record.timestamp.replace("Z", "+00:00"))
                target_month = dt.month
            except Exception:
                target_month = 7  # Default to peak monsoon (July)

        # 1. Feature extraction if not provided
        if derived_features is None:
            from backend.app.data.processing.feature_engineering import MeteorologicalFeaturePipeline
            derived_features = MeteorologicalFeaturePipeline.compute_all_features(record)

        synoptics = RegimeFeatureExtractor.extract_synoptic_features(record, derived_features)

        # 2. Run all individual detectors
        # Active / Break
        rain_24h = derived_features.rainfall_accumulation_24h or (record.rainfall * 24.0)
        active_prob, break_prob, active_diag = ActiveBreakMonsoonDetector.evaluate(
            synoptics=synoptics,
            rainfall_24h_mm=rain_24h,
            target_month=target_month,
        )

        # LPS / Monsoon Depression
        lps_prob, lps_intensity, lps_diag = MonsoonLpsDetector.evaluate(
            synoptics=synoptics,
            lat=record.latitude,
            lon=record.longitude,
        )

        # Coastal Convergence
        coastal_dist = record.distance_to_coast if record.distance_to_coast is not None else 85.0
        coastal_prob, coastal_diag = CoastalConvergenceDetector.evaluate(
            synoptics=synoptics,
            distance_to_coast_km=coastal_dist,
        )

        # Orographic Lifting
        elev = record.elevation if record.elevation is not None else 450.0
        slope = record.slope if record.slope is not None else 2.5
        aspect = record.aspect if record.aspect is not None else 270.0
        rh_850 = record.relative_humidity_850 or 80.0
        w_speed_850 = derived_features.wind_speed_850
        w_dir_850 = derived_features.wind_direction_850

        orographic_prob, orographic_diag = OrographicLiftingDetector.evaluate(
            synoptics=synoptics,
            elevation_m=elev,
            slope_deg=slope,
            aspect_deg=aspect,
            humidity_850_pct=rh_850,
            wind_speed_850_ms=w_speed_850,
            wind_direction_850_deg=w_dir_850,
        )

        # Western Disturbance
        wd_prob, wd_diag = WesternDisturbanceDetector.evaluate(
            synoptics=synoptics,
            lat=record.latitude,
            lon=record.longitude,
            target_month=target_month,
            geopotential_500_gpm=record.geopotential_500,
            u500_ms=record.u500,
            v500_ms=record.v500,
        )

        # Neutral baseline probability (suppressed activity)
        max_active = max(active_prob, lps_prob, coastal_prob, orographic_prob, wd_prob)
        neutral_prob = round(max(0.02, min(0.95, 1.0 - max_active)), 3)

        # Compile Probability Map
        probabilities: Dict[str, float] = {
            WeatherRegimeType.ACTIVE_MONSOON.value: active_prob,
            WeatherRegimeType.BREAK_MONSOON.value: break_prob,
            WeatherRegimeType.MONSOON_LOW_LPS.value: lps_prob,
            WeatherRegimeType.COASTAL_CONVERGENCE.value: coastal_prob,
            WeatherRegimeType.OROGRAPHIC_RAINFALL.value: orographic_prob,
            WeatherRegimeType.WESTERN_DISTURBANCE.value: wd_prob,
            WeatherRegimeType.NEUTRAL.value: neutral_prob,
        }

        # 3. Determine Primary Regime
        # Sort regimes by probability descending
        sorted_regimes = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
        primary_regime_str, primary_prob = sorted_regimes[0]
        primary_regime = WeatherRegimeType(primary_regime_str)

        # 4. Multi-Label: Secondary Regimes (regimes above 0.28 probability excluding primary)
        secondary_regimes: List[WeatherRegimeType] = []
        for reg_str, prob in sorted_regimes[1:]:
            if prob >= 0.28 and reg_str != WeatherRegimeType.NEUTRAL.value and reg_str != WeatherRegimeType.BREAK_MONSOON.value:
                secondary_regimes.append(WeatherRegimeType(reg_str))
            if len(secondary_regimes) >= 3:
                break

        # 5. Regime Confidence derived from margin of victory and signal strength
        # Difference between #1 and #2 probability
        runner_up_prob = sorted_regimes[1][1] if len(sorted_regimes) > 1 else 0.0
        prob_margin = primary_prob - runner_up_prob
        calculated_confidence = round(min(0.98, max(0.40, primary_prob * 0.70 + prob_margin * 0.30 + 0.15)), 2)

        # 6. Extract Top Atmospheric Drivers for Explainability (XAI)
        drivers = cls._extract_atmospheric_drivers(
            record=record,
            derived_features=derived_features,
            synoptics=synoptics,
            primary_regime=primary_regime,
        )

        # 7. Generate Physical Narrative
        narrative = cls._generate_narrative(
            primary=primary_regime,
            secondary=secondary_regimes,
            confidence=calculated_confidence,
            synoptics=synoptics,
            derived_features=derived_features,
            lps_intensity=lps_intensity,
        )

        return RegimeResponse(
            primary_regime=primary_regime,
            confidence=calculated_confidence,
            primary_confidence=calculated_confidence,
            secondary_regimes=secondary_regimes,
            probabilities=probabilities,
            drivers=drivers,
            synoptic_features=synoptics,
            regime_narrative=narrative,
            model_version=cls.MODEL_VERSION,
            data_source=record.data_source,
            is_demo=record.is_demo,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def _extract_atmospheric_drivers(
        cls,
        record: CanonicalMeteorologicalRecord,
        derived_features: MeteorologicalFeatureSet,
        synoptics: SynopticFeatures,
        primary_regime: WeatherRegimeType,
    ) -> List[AtmosphericDriver]:
        """
        Derive top quantified atmospheric drivers explaining the classified regime.
        """
        drivers: List[AtmosphericDriver] = []

        if primary_regime == WeatherRegimeType.ACTIVE_MONSOON:
            drivers.append(
                AtmosphericDriver(
                    feature="850_hPa_wind_speed",
                    value=round(derived_features.wind_speed_850, 1),
                    importance=0.34,
                    description="Strong cross-equatorial Low-Level Jet feeding monsoon trough",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="relative_humidity_850",
                    value=round(record.relative_humidity_850 or 82.0, 1),
                    importance=0.26,
                    description="Deep boundary layer moisture saturation",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="moisture_transport_proxy",
                    value=round(derived_features.moisture_transport_proxy, 1),
                    importance=0.22,
                    description="High integrated water vapor flux convergence",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="rainfall_accumulation_24h",
                    value=round(derived_features.rainfall_accumulation_24h, 1),
                    importance=0.18,
                    description="Widespread core monsoon rainfall activity",
                )
            )

        elif primary_regime == WeatherRegimeType.MONSOON_LOW_LPS:
            drivers.append(
                AtmosphericDriver(
                    feature="mid_tropospheric_vorticity",
                    value=round(synoptics.mid_tropospheric_vorticity_1e5_s, 2),
                    importance=0.38,
                    description="Strong cyclonic vorticity maximum in 850-700 hPa layer",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="mslp_anomaly",
                    value=round(synoptics.surface_pressure_anomaly_hpa, 1),
                    importance=0.32,
                    description="Significant barometric sea-level pressure depression",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="vertical_wind_shear",
                    value=round(derived_features.vertical_wind_shear, 1),
                    importance=0.18,
                    description="Moderate easterly shear maintaining organized cyclonic vortex",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="moisture_transport_proxy",
                    value=round(derived_features.moisture_transport_proxy, 1),
                    importance=0.12,
                    description="Vortex-induced moisture inflow convergence",
                )
            )

        elif primary_regime == WeatherRegimeType.OROGRAPHIC_RAINFALL:
            drivers.append(
                AtmosphericDriver(
                    feature="terrain_elevation",
                    value=round(record.elevation or 650.0, 0),
                    importance=0.35,
                    description="High topographic barrier triggering forced adiabatic ascent",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="850_hPa_wind_speed",
                    value=round(derived_features.wind_speed_850, 1),
                    importance=0.28,
                    description="Perpendicular onshore wind vector impinging on mountain ridge",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="orographic_lift_index",
                    value=round(derived_features.orographic_lift_index, 3),
                    importance=0.22,
                    description="Strong slope-normal velocity condensation potential",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="relative_humidity_850",
                    value=round(record.relative_humidity_850 or 85.0, 1),
                    importance=0.15,
                    description="Near-saturated inflow at cloud base level",
                )
            )

        elif primary_regime == WeatherRegimeType.COASTAL_CONVERGENCE:
            drivers.append(
                AtmosphericDriver(
                    feature="distance_to_coast",
                    value=round(record.distance_to_coast or 35.0, 1),
                    importance=0.36,
                    description="Immediate coastal proximity with land-sea friction gradient",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="coastal_moisture_indicator",
                    value=round(derived_features.coastal_moisture_indicator, 3),
                    importance=0.30,
                    description="Onshore maritime moisture convergence along shoreline",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="850_hPa_wind_direction",
                    value=round(derived_features.wind_direction_850, 1),
                    importance=0.20,
                    description="Onshore wind angle producing coastal speed convergence",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="surface_pressure",
                    value=round(record.surface_pressure or 1005.0, 1),
                    importance=0.14,
                    description="Offshore trough barometric pressure gradient",
                )
            )

        elif primary_regime == WeatherRegimeType.WESTERN_DISTURBANCE:
            drivers.append(
                AtmosphericDriver(
                    feature="geopotential_500",
                    value=round(record.geopotential_500 or 5780.0, 0),
                    importance=0.36,
                    description="Deep upper-tropospheric westerly trough at 500 hPa",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="500_hPa_u_wind",
                    value=round(record.u500 or 22.0, 1),
                    importance=0.32,
                    description="Strong subtropical westerly jet stream core",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="vertical_wind_shear",
                    value=round(derived_features.vertical_wind_shear, 1),
                    importance=0.18,
                    description="Baroclinic vertical wind shear over northern latitudes",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="relative_humidity_700",
                    value=round(record.relative_humidity_700 or 65.0, 1),
                    importance=0.14,
                    description="Mid-level moisture advection from Arabian Sea / Mediterranean",
                )
            )

        elif primary_regime == WeatherRegimeType.BREAK_MONSOON:
            drivers.append(
                AtmosphericDriver(
                    feature="850_hPa_wind_speed",
                    value=round(derived_features.wind_speed_850, 1),
                    importance=0.38,
                    description="Subdued Low-Level Jet speed over core monsoon zone",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="rainfall_accumulation_24h",
                    value=round(derived_features.rainfall_accumulation_24h, 1),
                    importance=0.30,
                    description="Suppressed precipitation over central Indian plains",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="relative_humidity_850",
                    value=round(record.relative_humidity_850 or 52.0, 1),
                    importance=0.20,
                    description="Dry continental air intrusion suppressing convection",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="monsoon_trough_lat",
                    value=round(synoptics.monsoon_trough_lat, 1),
                    importance=0.12,
                    description="Monsoon trough axis shifted northwards to Himalayan foothills",
                )
            )

        else:  # NEUTRAL
            drivers.append(
                AtmosphericDriver(
                    feature="850_hPa_wind_speed",
                    value=round(derived_features.wind_speed_850, 1),
                    importance=0.35,
                    description="Moderate background wind field without strong synoptic forcing",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="relative_humidity_850",
                    value=round(record.relative_humidity_850 or 65.0, 1),
                    importance=0.35,
                    description="Typical ambient humidity without organized deep ascent",
                )
            )
            drivers.append(
                AtmosphericDriver(
                    feature="rainfall_accumulation_24h",
                    value=round(derived_features.rainfall_accumulation_24h, 1),
                    importance=0.30,
                    description="Background localized precipitation",
                )
            )

        return drivers

    @classmethod
    def _generate_narrative(
        cls,
        primary: WeatherRegimeType,
        secondary: List[WeatherRegimeType],
        confidence: float,
        synoptics: SynopticFeatures,
        derived_features: MeteorologicalFeatureSet,
        lps_intensity: str,
    ) -> str:
        """
        Generate physical meteorological narrative describing classified regime state.
        """
        sec_text = ""
        if secondary:
            sec_names = [s.value.replace("_", " ") for s in secondary]
            sec_text = f" Co-occurring secondary physical mechanisms: {', '.join(sec_names)}."

        if primary == WeatherRegimeType.ACTIVE_MONSOON:
            return (
                f"Active Monsoon Synoptic State ({int(confidence * 100)}% confidence). "
                f"Driven by an intense 850 hPa Arabian Sea Low-Level Jet ({synoptics.low_level_jet_speed_kts:.1f} kts) "
                f"and active monsoon trough position ({synoptics.monsoon_trough_lat:.1f}°N). "
                f"Integrated vapor transport of {derived_features.moisture_transport_proxy:.1f} kg/(m·s) indicates "
                f"widespread convective organization.{sec_text}"
            )
        elif primary == WeatherRegimeType.MONSOON_LOW_LPS:
            return (
                f"Monsoon Low Pressure System / {lps_intensity} Detected ({int(confidence * 100)}% confidence). "
                f"Pronounced cyclonic relative vorticity ({synoptics.mid_tropospheric_vorticity_1e5_s:.1f} ×10⁻⁵ s⁻¹) "
                f"coupled with a barometric pressure anomaly of {synoptics.surface_pressure_anomaly_hpa:.1f} hPa. "
                f"Strong spiral moisture convergence active.{sec_text}"
            )
        elif primary == WeatherRegimeType.OROGRAPHIC_RAINFALL:
            return (
                f"Orographic Lifting Rainfall Enhancement ({int(confidence * 100)}% confidence). "
                f"Strong moist onshore inflow ({derived_features.wind_speed_850:.1f} m/s) impinging upon elevated terrain "
                f"inducing mechanical adiabatic expansion, saturated ascent, and heavy localized precipitation.{sec_text}"
            )
        elif primary == WeatherRegimeType.COASTAL_CONVERGENCE:
            return (
                f"Coastal Convergence & Boundary Layer Friction Regime ({int(confidence * 100)}% confidence). "
                f"Maritime moisture inflow converging along coastline with significant roughness differential.{sec_text}"
            )
        elif primary == WeatherRegimeType.WESTERN_DISTURBANCE:
            return (
                f"Western Disturbance Extratropical Trough ({int(confidence * 100)}% confidence). "
                f"Upper-level mid-latitude wave in the subtropical westerlies over Northern India triggering baroclinic precipitation.{sec_text}"
            )
        elif primary == WeatherRegimeType.BREAK_MONSOON:
            return (
                f"Break Monsoon Synoptic State ({int(confidence * 100)}% confidence). "
                f"Monsoon trough shifted towards Himalayan foothills ({synoptics.monsoon_trough_lat:.1f}°N) with weakened "
                f"peninsular LLJ winds ({synoptics.low_level_jet_speed_kts:.1f} kts) and suppressed rainfall over Central India.{sec_text}"
            )
        else:
            return (
                f"Neutral / Ambient Monsoon Regime ({int(confidence * 100)}% confidence). "
                f"No dominant extreme synoptic forcing signature detected. Ambient background convective activity.{sec_text}"
            )
