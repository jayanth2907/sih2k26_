"""
Spatial Probability & Quantile Uncertainty Engine (Phase 13).
Generates calibrated 2D heavy rainfall exceedance fields (P64.5, P115.6, P204.5),
enforces strict mathematical monotonicity invariants:
1. P64.5 >= P115.6 >= P204.5 at every cell
2. 0 <= P10 <= P50 <= P90 at every cell
"""

import math
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.ndimage import uniform_filter


class SpatialProbabilityEngine:
    """
    Computes calibrated probabilistic rainfall fields and spatial quantile uncertainty grids.
    """

    @classmethod
    def generate_exceedance_probabilities(
        cls,
        corrected_grid: np.ndarray,
        dominant_regime: str = "ACTIVE_MONSOON",
        regime_confidence: float = 0.85,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute calibrated 2D exceedance probability fields for 64.5 mm, 115.6 mm, and 204.5 mm.
        Guarantees strict monotonicity: P64.5(x, y) >= P115.6(x, y) >= P204.5(x, y) for all cells.
        """
        r = np.asarray(corrected_grid, dtype=np.float64)
        
        # Regime-dependent dispersion factor (sigma)
        sigma_map = {
            "ACTIVE_MONSOON": 14.5,
            "BREAK_MONSOON": 8.0,
            "MONSOON_LOW_LPS": 22.0,
            "COASTAL_CONVERGENCE": 18.5,
            "OROGRAPHIC_RAINFALL": 26.0,
            "WESTERN_DISTURBANCE": 16.0,
            "NEUTRAL": 11.0,
        }
        sigma = sigma_map.get(dominant_regime, 15.0)

        # Logistic empirical cumulative distribution mapping: P(R >= T) = 1 / (1 + exp(-(R - T) / (0.55 * sigma)))
        # Logistic scale parameter s = (sqrt(3) / pi) * sigma ~ 0.55 * sigma
        scale = max(4.0, 0.55 * sigma)

        z64 = (r - 64.5) / scale
        z115 = (r - 115.6) / scale
        z204 = (r - 204.5) / scale

        # Numerically stable logistic sigmoid
        p64 = 1.0 / (1.0 + np.exp(-np.clip(z64, -20.0, 20.0)))
        p115 = 1.0 / (1.0 + np.exp(-np.clip(z115, -20.0, 20.0)))
        p204 = 1.0 / (1.0 + np.exp(-np.clip(z204, -20.0, 20.0)))

        # Direct physical zero-clamping for dry cells
        p64[r < 5.0] = 0.0
        p115[r < 25.0] = 0.0
        p204[r < 60.0] = 0.0

        # Enforce strict Monotonicity Invariant: P64.5 >= P115.6 >= P204.5
        p115 = np.minimum(p115, p64)
        p204 = np.minimum(p204, p115)

        # Clamp bounds [0.0, 1.0]
        p64 = np.clip(p64, 0.0, 1.0)
        p115 = np.clip(p115, 0.0, 1.0)
        p204 = np.clip(p204, 0.0, 1.0)

        return np.round(p64, 4), np.round(p115, 4), np.round(p204, 4)

    @classmethod
    def generate_spatial_quantiles(
        cls,
        corrected_grid: np.ndarray,
        dominant_regime: str = "ACTIVE_MONSOON",
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Produce 2D spatial quantile fields: P10 (lower bound), P50 (median/corrected), P90 (upper bound).
        Guarantees strict Monotonicity Invariant: 0.0 <= P10(x, y) <= P50(x, y) <= P90(x, y).
        """
        p50 = np.asarray(corrected_grid, dtype=np.float64)
        
        # Regime-conditioned uncertainty scaling factors
        spread_factors = {
            "ACTIVE_MONSOON": (0.75, 1.30),
            "BREAK_MONSOON": (0.85, 1.15),
            "MONSOON_LOW_LPS": (0.65, 1.45),
            "COASTAL_CONVERGENCE": (0.70, 1.35),
            "OROGRAPHIC_RAINFALL": (0.60, 1.55),
            "WESTERN_DISTURBANCE": (0.72, 1.32),
            "NEUTRAL": (0.80, 1.25),
        }
        lower_fac, upper_fac = spread_factors.get(dominant_regime, (0.75, 1.30))

        p10 = np.maximum(0.0, p50 * lower_fac)
        p90 = np.maximum(p50, p50 * upper_fac)

        # Enforce strict quantile monotonicity
        p10 = np.minimum(p10, p50)
        p90 = np.maximum(p90, p50)

        return np.round(p10, 2), np.round(p50, 2), np.round(p90, 2)

    @classmethod
    def compute_neighborhood_event_probability(
        cls,
        prob_grid: np.ndarray,
        window_size: int = 5,
    ) -> np.ndarray:
        """
        Compute neighborhood-aware event occurrence probability: P(event in neighborhood) = 1 - prod(1 - p_i).
        Approximated via spatial box filter on log non-occurrence: 1 - exp(sum(log(1 - p_i))).
        """
        arr = np.clip(np.asarray(prob_grid, dtype=np.float64), 0.0, 0.9999)
        log_non_event = np.log(1.0 - arr)
        
        # Sum of log non-events in window = uniform_filter * (window_size^2)
        sum_log = uniform_filter(log_non_event, size=window_size, mode="nearest") * (window_size**2)
        p_neighborhood = 1.0 - np.exp(np.clip(sum_log, -50.0, 0.0))

        return np.round(np.clip(p_neighborhood, 0.0, 1.0), 4)
