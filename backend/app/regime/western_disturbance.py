"""
Western Disturbance (WD) Weather Regime Detector for PS26080.
Evaluates mid-to-upper tropospheric westerly troughs, 500 hPa geopotential height anomalies,
subtropical jet stream dynamics, and seasonality over North/Northwest India.
"""

from typing import Dict, Optional, Tuple
from backend.app.schemas.regime import SynopticFeatures


class WesternDisturbanceDetector:
    """
    Detector for extratropical mid-latitude weather systems (Western Disturbances)
    affecting the Western Himalayas and Indo-Gangetic Plains.
    """

    LAT_MIN = 24.0
    LAT_MAX = 38.0
    LON_MIN = 68.0
    LON_MAX = 88.0
    ACTIVE_MONTHS = [1, 2, 3, 4, 10, 11, 12]
    MONSOON_INTERACTION_MONTHS = [6, 7, 8, 9]

    @classmethod
    def evaluate(
        cls,
        synoptics: SynopticFeatures,
        lat: float,
        lon: float,
        target_month: int = 7,
        geopotential_500_gpm: Optional[float] = 5820.0,
        u500_ms: Optional[float] = 12.0,
        v500_ms: Optional[float] = 4.0,
    ) -> Tuple[float, Dict[str, any]]:
        """
        Compute Western Disturbance probability and upper-tropospheric trough diagnostics.

        Parameters
        ----------
        synoptics : SynopticFeatures
            Diagnosed synoptic indices.
        lat : float
            Latitude in degrees North.
        lon : float
            Longitude in degrees East.
        target_month : int
            Calendar month (1-12).
        geopotential_500_gpm : float, optional
            500 hPa geopotential height (gpm).
        u500_ms : float, optional
            500 hPa zonal wind (m/s).
        v500_ms : float, optional
            500 hPa meridional wind (m/s).

        Returns
        -------
        Tuple[float, Dict[str, any]]
            (western_disturbance_probability, diagnostics_dict)
        """
        # 1. Geographic Domain Check (North / Northwest India & Himalayas)
        in_domain = (cls.LAT_MIN <= lat <= cls.LAT_MAX) and (cls.LON_MIN <= lon <= cls.LON_MAX)
        if not in_domain:
            # Latitudinal distance penalty
            dist_lat = min(abs(lat - cls.LAT_MIN), abs(lat - cls.LAT_MAX)) if lat < cls.LAT_MIN or lat > cls.LAT_MAX else 0.0
            geo_factor = max(0.0, 1.0 - (dist_lat / 6.0))
        else:
            geo_factor = 1.0

        # 2. Seasonality Factor
        if target_month in cls.ACTIVE_MONTHS:
            season_factor = 1.0
        elif target_month in cls.MONSOON_INTERACTION_MONTHS:
            season_factor = 0.35  # Rare Monsoon-WD interaction (e.g. 2013 Kedarnath, 2023 Himachal)
        else:
            season_factor = 0.50

        # 3. Upper Tropospheric 500 hPa Geopotential Height Anomaly
        # Standard tropical 500 hPa is ~5880 gpm; mid-latitude trough dips to <5760 gpm
        standard_500_gpm = 5860.0
        gpm_anomaly = (geopotential_500_gpm or 5820.0) - standard_500_gpm

        if gpm_anomaly <= -60.0:
            gpm_score = 0.95
        elif gpm_anomaly <= -30.0:
            gpm_score = 0.60 + abs(gpm_anomaly + 30.0) / 30.0 * 0.35
        elif gpm_anomaly <= -10.0:
            gpm_score = 0.25 + abs(gpm_anomaly + 10.0) / 20.0 * 0.35
        else:
            gpm_score = 0.05

        # 4. Upper-level Westerly Wind Forcing (Subtropical Westerly Jet component)
        u_wind = u500_ms if u500_ms is not None else 10.0
        v_wind = v500_ms if v500_ms is not None else 2.0
        westerly_speed = max(0.0, u_wind)

        if westerly_speed >= 25.0:
            wind_score = 0.90
        elif westerly_speed >= 12.0:
            wind_score = 0.40 + (westerly_speed - 12.0) / 13.0 * 0.50
        else:
            wind_score = max(0.05, westerly_speed / 12.0 * 0.40)

        # Composite Probability
        wd_prob = geo_factor * season_factor * (0.50 * gpm_score + 0.50 * wind_score)
        wd_prob = round(max(0.01, min(0.98, wd_prob)), 3)

        diagnostics = {
            "western_disturbance_probability": wd_prob,
            "in_wd_domain": in_domain,
            "season_factor": season_factor,
            "geopotential_500_gpm": geopotential_500_gpm,
            "geopotential_anomaly_gpm": round(gpm_anomaly, 1),
            "u500_westerly_speed_ms": round(westerly_speed, 1),
            "gpm_score": round(gpm_score, 2),
            "wind_score": round(wind_score, 2),
        }

        return wd_prob, diagnostics
