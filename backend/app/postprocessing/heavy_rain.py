"""
Heavy Rainfall Probability Estimation and IMD Warning Category Classifier for PS26080.
Supports configurable rainfall threshold tiers:
- Heavy: >= 64.5 mm/24h
- Very Heavy: >= 115.6 mm/24h
- Extremely Heavy: >= 204.5 mm/24h
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field


class RainfallProbabilityPackage(BaseModel):
    """Calibrated exceedance probabilities across IMD standard rainfall tiers."""
    heavy_prob_ge_64_5mm: float = Field(..., ge=0.0, le=1.0)
    very_heavy_prob_ge_115_6mm: float = Field(..., ge=0.0, le=1.0)
    extreme_prob_ge_204_5mm: float = Field(..., ge=0.0, le=1.0)
    imd_warning_category: str = Field(..., description="'No Warning', 'Watch (Heavy Rain)', 'Alert (Very Heavy Rain)', 'Warning (Extremely Heavy Rain)'")
    probability_source: str = Field(..., description="Method used for calibration")
    thresholds_evaluated: Dict[str, float]


class HeavyRainfallCalibrator:
    """
    Computes calibrated probability of exceeding critical monsoon rainfall thresholds.
    """

    DEFAULT_HEAVY_THRESHOLD = 64.5
    DEFAULT_VERY_HEAVY_THRESHOLD = 115.6
    DEFAULT_EXTREME_THRESHOLD = 204.5

    @classmethod
    def calculate_probabilities(
        cls,
        rainfall_mm: float,
        uncertainty_spread_mm: Optional[float] = None,
        ensemble_members: Optional[List[float]] = None,
        heavy_thresh: float = DEFAULT_HEAVY_THRESHOLD,
        vheavy_thresh: float = DEFAULT_VERY_HEAVY_THRESHOLD,
        extreme_thresh: float = DEFAULT_EXTREME_THRESHOLD,
    ) -> RainfallProbabilityPackage:
        """
        Estimate monotonic calibrated probabilities for Heavy, Very Heavy, and Extremely Heavy rainfall.
        """
        val = max(0.0, float(rainfall_mm))

        if ensemble_members and len(ensemble_members) >= 10:
            # Empirical ensemble exceedance fraction
            ens = np.array(ensemble_members)
            p_heavy = float(np.mean(ens >= heavy_thresh))
            p_vheavy = float(np.mean(ens >= vheavy_thresh))
            p_extreme = float(np.mean(ens >= extreme_thresh))
            source = "NEPS_ENSEMBLE_EXCEEDANCE"
        else:
            # Sigmoid / logistic residual tail calibration
            spread = max(3.0, uncertainty_spread_mm if uncertainty_spread_mm is not None else val * 0.12)

            def _sigmoid(x: float, t: float, s: float) -> float:
                z = (x - t) / max(4.0, s * 1.4)
                return float(1.0 / (1.0 + np.exp(-z)))

            p_heavy = _sigmoid(val, heavy_thresh, spread)
            p_vheavy = _sigmoid(val, vheavy_thresh, spread)
            p_extreme = _sigmoid(val, extreme_thresh, spread)

            # Monotonicity & scaling constraints
            p_heavy = min(0.99, max(0.01, p_heavy))
            p_vheavy = min(p_heavy * 0.88, max(0.01, p_vheavy))
            p_extreme = min(p_vheavy * 0.55, max(0.01, p_extreme))
            source = "LOGISTIC_RESIDUAL_CALIBRATION"

        # Determine IMD warning classification
        if p_extreme >= 0.25 or val >= extreme_thresh:
            category = "Warning (Extremely Heavy Rain)"
        elif p_vheavy >= 0.40 or val >= vheavy_thresh:
            category = "Alert (Very Heavy Rain)"
        elif p_heavy >= 0.55 or val >= heavy_thresh:
            category = "Watch (Heavy Rain)"
        else:
            category = "No Warning"

        return RainfallProbabilityPackage(
            heavy_prob_ge_64_5mm=round(p_heavy, 3),
            very_heavy_prob_ge_115_6mm=round(p_vheavy, 3),
            extreme_prob_ge_204_5mm=round(p_extreme, 3),
            imd_warning_category=category,
            probability_source=source,
            thresholds_evaluated={
                "heavy_mm": heavy_thresh,
                "very_heavy_mm": vheavy_thresh,
                "extremely_heavy_mm": extreme_thresh,
            },
        )
