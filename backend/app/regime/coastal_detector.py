"""
Coastal Convergence Weather Regime Detector for PS26080.
Evaluates coastal proximity, onshore moisture influx, and boundary layer convergence along Indian coastlines.
"""

from typing import Dict, Tuple
from backend.app.schemas.regime import SynopticFeatures


class CoastalConvergenceDetector:
    """
    Detector for Coastal Rainfall & Land-Sea Convergence Regimes (Konkan, Malabar, Coromandel).
    """

    @classmethod
    def evaluate(
        cls,
        synoptics: SynopticFeatures,
        distance_to_coast_km: float,
    ) -> Tuple[float, Dict[str, any]]:
        """
        Compute coastal convergence regime probability and supporting synoptic indicators.
        """
        # Distance to coast decay
        if distance_to_coast_km > 150.0:
            return 0.05, {"distance_km": distance_to_coast_km, "coastal_prob": 0.05, "status": "INLAND"}

        # Proximity factor
        prox_score = max(0.0, 1.0 - (distance_to_coast_km / 150.0))

        # Onshore wind and convergence index
        conv_index = synoptics.coastal_convergence_index
        conv_score = min(1.0, conv_index / 8.0)

        # Wind direction: westerlies (220-300 deg) favor west coast, easterlies (60-140 deg) favor east coast
        wind_dir = synoptics.low_level_jet_direction_deg
        if 210.0 <= wind_dir <= 310.0:
            onshore_weight = 1.0
        elif 50.0 <= wind_dir <= 150.0:
            onshore_weight = 0.8
        else:
            onshore_weight = 0.4

        coastal_prob = (0.50 * prox_score + 0.35 * conv_score + 0.15 * onshore_weight)
        coastal_prob = round(max(0.02, min(0.98, coastal_prob)), 3)

        diagnostics = {
            "coastal_probability": coastal_prob,
            "distance_to_coast_km": distance_to_coast_km,
            "coastal_convergence_index": conv_index,
            "onshore_wind_dir_deg": wind_dir,
        }

        return coastal_prob, diagnostics
