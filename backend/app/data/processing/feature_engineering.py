"""
Meteorological Derived Feature Engineering Pipeline for PS26080.
Computes synoptic wind metrics, thermodynamic indices, vertical shear, orographic lifting,
and moisture transport indicators from canonical records.
"""

import math
from typing import List, Optional, Tuple
from backend.app.data.schemas.meteorology import CanonicalMeteorologicalRecord, MeteorologicalFeatureSet


class MeteorologicalFeatureEngineer:
    """
    Transforms canonical atmospheric records into rich physical predictors
    for weather regime classification and AI post-processing models.
    """

    @staticmethod
    def compute_wind_speed_direction(u: Optional[float], v: Optional[float]) -> Tuple[float, float]:
        """
        Compute scalar wind speed (m/s) and meteorological direction (degrees from which wind blows).
        """
        if u is None or v is None:
            return 0.0, 0.0

        speed = math.sqrt(u**2 + v**2)
        # Meteorological direction: 270 - atan2(v, u) in degrees
        dir_deg = (270.0 - math.degrees(math.atan2(v, u))) % 360.0
        return round(speed, 2), round(dir_deg, 1)

    @staticmethod
    def calculate_wind_speed_and_direction(u: Optional[float], v: Optional[float]) -> Tuple[float, float]:
        """Alias for compute_wind_speed_direction."""
        return MeteorologicalFeatureEngineer.compute_wind_speed_direction(u, v)

    @staticmethod
    def compute_vertical_wind_shear(
        u_low: Optional[float],
        v_low: Optional[float],
        u_high: Optional[float],
        v_high: Optional[float],
    ) -> float:
        """
        Compute bulk vertical wind shear magnitude between two pressure levels (e.g. 850 hPa and 500 hPa).
        """
        if u_low is None or v_low is None or u_high is None or v_high is None:
            return 0.0

        du = u_high - u_low
        dv = v_high - v_low
        shear = math.sqrt(du**2 + dv**2)
        return round(shear, 2)

    @staticmethod
    def calculate_vertical_wind_shear(
        u_low: Optional[float],
        v_low: Optional[float],
        u_high: Optional[float],
        v_high: Optional[float],
    ) -> float:
        """Alias for compute_vertical_wind_shear."""
        return MeteorologicalFeatureEngineer.compute_vertical_wind_shear(u_low, v_low, u_high, v_high)

    @staticmethod
    def estimate_specific_humidity_g_kg(temp_k: Optional[float], rh_pct: Optional[float], p_hpa: float = 850.0) -> float:
        """
        Estimate specific humidity (g/kg) using Bolton's formulation for saturation vapor pressure.
        """
        if temp_k is None or rh_pct is None or rh_pct <= 0:
            return 10.0  # Standard tropical baseline

        # Convert Kelvin to Celsius if necessary
        t_c = temp_k - 273.15 if temp_k > 150.0 else temp_k

        # Saturation vapor pressure (hPa) via Tetens formula
        es_hpa = 6.112 * math.exp((17.67 * t_c) / (t_c + 243.5))
        e_hpa = (rh_pct / 100.0) * es_hpa

        # Specific humidity q = 0.622 * e / (p - 0.378 * e) * 1000 (g/kg)
        denom = max(1.0, p_hpa - 0.378 * e_hpa)
        q_g_kg = (0.622 * e_hpa / denom) * 1000.0
        return round(max(0.1, q_g_kg), 2)

    @staticmethod
    def compute_specific_humidity(temp_k: Optional[float], rh_percent: Optional[float], pressure_hpa: float = 850.0) -> float:
        """Alias for estimate_specific_humidity_g_kg."""
        return MeteorologicalFeatureEngineer.estimate_specific_humidity_g_kg(temp_k, rh_percent, pressure_hpa)

    @classmethod
    def compute_moisture_transport(
        cls,
        u850: Optional[float],
        v850: Optional[float],
        t850: Optional[float],
        rh850: Optional[float],
    ) -> float:
        """
        Compute Integrated Vapor Transport proxy at 850 hPa: q_850 * V_850 (g/kg * m/s).
        """
        speed, _ = cls.compute_wind_speed_direction(u850, v850)
        q_g_kg = cls.estimate_specific_humidity_g_kg(t850, rh850, 850.0)
        ivt_proxy = q_g_kg * speed
        return round(ivt_proxy, 2)

    @classmethod
    def compute_orographic_lift_index(
        cls,
        u850: Optional[float],
        v850: Optional[float],
        slope_deg: Optional[float],
        aspect_deg: Optional[float],
        elevation_m: Optional[float],
    ) -> float:
        """
        Compute Orographic Lift Index based on wind component perpendicular to terrain slope.
        """
        if not slope_deg or slope_deg <= 0 or not elevation_m or elevation_m <= 0:
            return 0.0

        speed, wind_dir = cls.compute_wind_speed_direction(u850, v850)
        aspect = aspect_deg or 270.0  # Default Western Ghats aspect (facing west)

        angle_diff_rad = math.radians(wind_dir - aspect)
        normal_wind = speed * abs(math.cos(angle_diff_rad))

        slope_rad = math.radians(min(60.0, slope_deg))
        lift_proxy = (normal_wind * math.tan(slope_rad)) * (elevation_m / 1000.0)
        return round(max(0.0, lift_proxy), 3)

    @classmethod
    def compute_coastal_moisture_indicator(
        cls,
        u850: Optional[float],
        v850: Optional[float],
        rh850: Optional[float],
        dist_coast_km: Optional[float],
    ) -> float:
        """
        Compute coastal convergence & moisture indicator based on onshore wind and coastal proximity.
        """
        if dist_coast_km is None or dist_coast_km > 300.0:
            return 0.0

        speed, _ = cls.compute_wind_speed_direction(u850, v850)
        rh = rh850 or 70.0

        prox_weight = math.exp(-dist_coast_km / 75.0)
        indicator = (speed * (rh / 100.0)) * prox_weight
        return round(float(indicator), 3)

    @classmethod
    def extract_features(
        cls,
        record: CanonicalMeteorologicalRecord,
        hourly_series: Optional[List[float]] = None,
    ) -> MeteorologicalFeatureSet:
        """
        Extract complete engineered feature set from a canonical meteorological record.
        """
        # Wind speeds and directions
        w_spd_850, w_dir_850 = cls.compute_wind_speed_direction(record.u850, record.v850)
        w_spd_700, w_dir_700 = cls.compute_wind_speed_direction(record.u700, record.v700)

        # Vertical Wind Shear between 850 and 500 hPa
        shear = cls.compute_vertical_wind_shear(record.u850, record.v850, record.u500, record.v500)

        # Moisture Transport Proxy (IVT)
        ivt = cls.compute_moisture_transport(record.u850, record.v850, record.temperature_850, record.relative_humidity_850)

        # Accumulations from hourly series if provided
        rain = record.rainfall
        acc_6h = sum((hourly_series or [rain / 24.0] * 24)[:6])
        acc_12h = sum((hourly_series or [rain / 24.0] * 24)[:12])
        acc_24h = sum((hourly_series or [rain / 24.0] * 24)[:24])

        # Ensemble Spread
        if record.ensemble_p90 is not None and record.ensemble_p10 is not None:
            spread = max(0.0, record.ensemble_p90 - record.ensemble_p10)
        elif record.ensemble_std is not None:
            spread = max(0.0, record.ensemble_std * 2.0)
        else:
            spread = round(rain * 0.25, 2)

        mean_rain = record.ensemble_mean or max(1.0, rain)
        disagreement = min(1.0, spread / mean_rain)

        # Terrain Gradient & Orographic Lift
        slope = record.slope or 1.5
        terrain_grad = round(math.tan(math.radians(slope)) * 1000.0, 2)
        orographic_lift = cls.compute_orographic_lift_index(
            record.u850, record.v850, record.slope, record.aspect, record.elevation
        )

        # Coastal Indicator
        coastal_ind = cls.compute_coastal_moisture_indicator(
            record.u850, record.v850, record.relative_humidity_850, record.distance_to_coast
        )

        # Pressure Gradient (Local Barometric departure from 1013.25 hPa)
        mslp = record.mslp or 1008.0
        p_grad = round(abs(mslp - 1013.25) / 5.0, 3)

        return MeteorologicalFeatureSet(
            wind_speed_850=w_spd_850,
            wind_direction_850=w_dir_850,
            wind_speed_700=w_spd_700,
            wind_direction_700=w_dir_700,
            vertical_wind_shear=shear,
            pressure_gradient=p_grad,
            moisture_transport_proxy=ivt,
            rainfall_accumulation_6h=round(acc_6h, 2),
            rainfall_accumulation_12h=round(acc_12h, 2),
            rainfall_accumulation_24h=round(acc_24h, 2),
            ensemble_spread=round(spread, 2),
            forecast_disagreement=round(disagreement, 3),
            terrain_gradient=terrain_grad,
            orographic_lift_index=orographic_lift,
            coastal_moisture_indicator=coastal_ind,
        )

    @classmethod
    def compute_all_features(
        cls,
        record: CanonicalMeteorologicalRecord,
        hourly_series: Optional[List[float]] = None,
    ) -> MeteorologicalFeatureSet:
        """Alias for extract_features."""
        return cls.extract_features(record, hourly_series)


# Uniform alias
MeteorologicalFeaturePipeline = MeteorologicalFeatureEngineer
