"""
Monsoon Low Pressure System (LPS) / Depression Detector for PS26080.
Detects synoptic cyclonic vortices, depressions, and deep depressions from barometric,
vorticity, and geopotential fields.
"""

from typing import Dict, Tuple
from backend.app.schemas.regime import SynopticFeatures


class MonsoonLpsDetector:
    """
    Detector for Bay of Bengal / Arabian Sea Monsoon Lows, Depressions, and LPS.
    """

    @classmethod
    def evaluate(
        cls,
        synoptics: SynopticFeatures,
        lat: float,
        lon: float,
    ) -> Tuple[float, str, Dict[str, any]]:
        """
        Evaluate LPS / depression probability, intensity category, and kinematic metrics.
        """
        vorticity = synoptics.mid_tropospheric_vorticity_1e5_s
        p_anomaly = synoptics.surface_pressure_anomaly_hpa
        ivt = synoptics.integrated_vapor_transport_kg_m_s

        # 1. Cyclonic Vorticity Score (> 3.5 is strong cyclonic curvature)
        if vorticity >= 6.0:
            vort_score = 0.95
        elif vorticity >= 3.5:
            vort_score = 0.65 + (vorticity - 3.5) / 2.5 * 0.30
        elif vorticity >= 1.5:
            vort_score = 0.30 + (vorticity - 1.5) / 2.0 * 0.35
        else:
            vort_score = max(0.05, vorticity * 0.1)

        # 2. Barometric Low Pressure Anomaly Score (Anomaly relative to 1013.25 hPa)
        # Deep anomaly: < -8 hPa -> score ~ 0.90
        if p_anomaly <= -8.0:
            p_score = min(1.0, 0.85 + abs(p_anomaly + 8.0) * 0.03)
        elif p_anomaly <= -4.0:
            p_score = 0.50 + abs(p_anomaly + 4.0) / 4.0 * 0.35
        elif p_anomaly <= -1.0:
            p_score = 0.20 + abs(p_anomaly + 1.0) / 3.0 * 0.30
        else:
            p_score = 0.05

        # 3. Moisture Transport Convergence Score
        ivt_score = min(1.0, ivt / 250.0)

        # Composite LPS Probability
        lps_prob = round(0.45 * vort_score + 0.35 * p_score + 0.20 * ivt_score, 3)

        # Categorize Intensity
        if lps_prob >= 0.75 and p_anomaly <= -8.0:
            intensity = "DEEP_DEPRESSION"
        elif lps_prob >= 0.50 and p_anomaly <= -5.0:
            intensity = "MONSOON_DEPRESSION"
        elif lps_prob >= 0.35:
            intensity = "MONSOON_LOW"
        else:
            intensity = "WEAK_OR_NONE"

        # Kinematics estimate (distance from typical Bay of Bengal genesis path)
        distance_km = round(max(50.0, abs(lon - 88.0) * 85.0), 1)
        direction_deg = 295.0 # Typical WNW monsoon depression track
        speed_kmh = 18.5

        diagnostics = {
            "lps_probability": lps_prob,
            "lps_intensity": intensity,
            "vorticity_1e5_s": vorticity,
            "pressure_anomaly_hpa": p_anomaly,
            "lps_distance_km": distance_km,
            "lps_direction_deg": direction_deg,
            "lps_movement_speed_kmh": speed_kmh,
        }

        return lps_prob, intensity, diagnostics
