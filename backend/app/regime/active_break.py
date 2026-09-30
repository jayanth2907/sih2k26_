"""
Active and Break Monsoon Regime Detector for PS26080.
Evaluates monsoon trough positioning, 850 hPa Low-Level Jet velocity, and convective OLR indices.
"""

from typing import Dict, Tuple
from backend.app.schemas.regime import SynopticFeatures


class ActiveBreakMonsoonDetector:
    """
    Objective detector for Active Monsoon and Break Monsoon synoptic regimes
    during the South Asian Summer Monsoon season (JJAS).
    """

    @classmethod
    def evaluate(
        cls,
        synoptics: SynopticFeatures,
        rainfall_24h_mm: float,
        target_month: int = 7,
    ) -> Tuple[float, float, Dict[str, any]]:
        """
        Compute active_probability and break_probability with physical evidence diagnostics.
        """
        # Monsoon seasonality check: June to September (months 6-9)
        if target_month not in [6, 7, 8, 9]:
            return 0.05, 0.05, {"season": "NON_MONSOON", "active_score": 0.05, "break_score": 0.05}

        # 1. Low-Level Jet (LLJ) Component Score
        # Active: strong LLJ (>28 kts), Break: suppressed (<15 kts)
        llj = synoptics.low_level_jet_speed_kts
        if llj >= 28.0:
            llj_active_score = min(1.0, 0.6 + (llj - 28.0) * 0.04)
            llj_break_score = 0.05
        elif llj <= 15.0:
            llj_active_score = 0.10
            llj_break_score = min(1.0, 0.6 + (15.0 - llj) * 0.05)
        else:
            # Transitional 15-28 kts
            llj_active_score = 0.3 + (llj - 15.0) / 13.0 * 0.3
            llj_break_score = 0.3 + (28.0 - llj) / 13.0 * 0.3

        # 2. Monsoon Trough Position Component Score
        trough = synoptics.trough_position
        if trough == "active_south":
            trough_active_score = 0.90
            trough_break_score = 0.05
        elif trough == "break_foothills":
            trough_active_score = 0.05
            trough_break_score = 0.90
        else:
            trough_active_score = 0.45
            trough_break_score = 0.20

        # 3. OLR Convection Score
        # OLR < 210 W/m^2 -> active deep convection, OLR > 240 W/m^2 -> clear/break
        olr = synoptics.olr_w_m2
        if olr <= 210.0:
            olr_active_score = min(1.0, 0.7 + (210.0 - olr) * 0.01)
            olr_break_score = 0.05
        elif olr >= 240.0:
            olr_active_score = 0.10
            olr_break_score = min(1.0, 0.6 + (olr - 240.0) * 0.01)
        else:
            olr_active_score = 0.40
            olr_break_score = 0.30

        # 4. Precipitation Reinforcement
        if rainfall_24h_mm >= 35.0:
            rain_active_score = 0.85
            rain_break_score = 0.05
        elif rainfall_24h_mm <= 4.0:
            rain_active_score = 0.15
            rain_break_score = 0.75
        else:
            rain_active_score = 0.50
            rain_break_score = 0.30

        # Composite Probability Formulation
        active_prob = (
            0.35 * llj_active_score
            + 0.30 * trough_active_score
            + 0.20 * olr_active_score
            + 0.15 * rain_active_score
        )
        break_prob = (
            0.35 * llj_break_score
            + 0.30 * trough_break_score
            + 0.20 * olr_break_score
            + 0.15 * rain_break_score
        )

        active_prob = round(max(0.01, min(0.99, active_prob)), 3)
        break_prob = round(max(0.01, min(0.99, break_prob)), 3)

        diagnostics = {
            "llj_speed_kts": llj,
            "trough_position": trough,
            "olr_w_m2": olr,
            "rainfall_24h_mm": rainfall_24h_mm,
            "llj_active_score": round(llj_active_score, 2),
            "trough_active_score": round(trough_active_score, 2),
            "olr_active_score": round(olr_active_score, 2),
        }

        return active_prob, break_prob, diagnostics
