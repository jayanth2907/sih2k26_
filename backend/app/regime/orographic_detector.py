"""
Orographic Lifting Weather Regime Detector for PS26080.
Evaluates complex terrain forced ascent along Western Ghats, Himalayas, and Northeast Hills (Garo-Khasi-Jaintia).
"""

import math
from typing import Dict, Tuple
from backend.app.schemas.regime import SynopticFeatures


class OrographicLiftingDetector:
    """
    Detector for Orographic Rainfall Enhancement & Mountain-Forced Condensation.
    """

    @classmethod
    def evaluate(
        cls,
        synoptics: SynopticFeatures,
        elevation_m: float,
        slope_deg: float,
        aspect_deg: float = 270.0,
        humidity_850_pct: float = 80.0,
        wind_speed_850_ms: float = 12.0,
        wind_direction_850_deg: float = 245.0,
    ) -> Tuple[float, Dict[str, any]]:
        """
        Compute orographic lifting regime probability and physical terrain forcing metrics.

        Parameters
        ----------
        synoptics : SynopticFeatures
            Diagnosed synoptic indices.
        elevation_m : float
            Station or grid elevation (meters above sea level).
        slope_deg : float
            Terrain incline angle in degrees.
        aspect_deg : float
            Terrain aspect / slope orientation angle (degrees azimuth).
        humidity_850_pct : float
            850 hPa relative humidity (percentage).
        wind_speed_850_ms : float
            850 hPa wind speed in m/s.
        wind_direction_850_deg : float
            850 hPa wind direction in degrees.

        Returns
        -------
        Tuple[float, Dict[str, any]]
            (orographic_probability, diagnostics_dict)
        """
        # 1. Elevation Forcing Factor (Sigmoid response: hills > 250m begin enhancement, > 800m high)
        if elevation_m < 80.0:
            elev_factor = 0.05
        elif elevation_m >= 1500.0:
            elev_factor = 1.0
        else:
            elev_factor = min(1.0, (elevation_m - 80.0) / 1420.0)

        # 2. Slope Incline Factor
        slope_factor = min(1.0, max(0.0, slope_deg / 6.0))

        # 3. Wind Component Normal to Mountain Face (V * cos(wind_dir - aspect))
        # Angle between incoming wind vector and mountain normal (aspect)
        angle_diff_rad = math.radians(abs(wind_direction_850_deg - aspect_deg))
        normal_wind_ms = max(0.0, wind_speed_850_ms * math.cos(angle_diff_rad))
        normal_wind_factor = min(1.0, normal_wind_ms / 14.0)

        # 4. Boundary Layer Moisture & Flux Factor
        rh_factor = max(0.0, min(1.0, (humidity_850_pct - 60.0) / 35.0))
        moisture_transport = synoptics.integrated_vapor_transport_kg_m_s or (wind_speed_850_ms * (humidity_850_pct / 100.0) * 15.0)
        moisture_factor = min(1.0, moisture_transport / 220.0)

        # 5. Pre-calculated Orographic Lift Index (if available)
        lift_idx = synoptics.orographic_lift_index
        lift_factor = min(1.0, lift_idx / 0.8) if lift_idx > 0 else (slope_factor * normal_wind_factor)

        # Composite Probability
        # If elevation is very low (<100m) and slope is flat, probability is capped
        if elevation_m < 150.0 and slope_deg < 0.5:
            orographic_prob = 0.03
        else:
            orographic_prob = (
                0.30 * elev_factor
                + 0.25 * slope_factor
                + 0.20 * normal_wind_factor
                + 0.15 * rh_factor
                + 0.10 * moisture_factor
            )
            orographic_prob = round(max(0.02, min(0.98, orographic_prob)), 3)

        diagnostics = {
            "orographic_probability": orographic_prob,
            "elevation_m": elevation_m,
            "slope_degrees": slope_deg,
            "normal_wind_component_ms": round(normal_wind_ms, 2),
            "humidity_850_pct": humidity_850_pct,
            "elevation_factor": round(elev_factor, 2),
            "slope_factor": round(slope_factor, 2),
            "normal_wind_factor": round(normal_wind_factor, 2),
        }

        return orographic_prob, diagnostics
