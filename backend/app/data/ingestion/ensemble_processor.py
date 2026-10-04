"""
Ensemble Processing Engine for NEPS (NCMRWF Ensemble Prediction System).
Calculates non-parametric and parametric ensemble statistics without fabricating members.
"""

from typing import Dict, List, Optional
import numpy as np


class EnsembleProcessor:
    """
    Ingests and processes multi-member NWP ensemble forecasts (e.g., NEPS 23 members).
    """

    @staticmethod
    def process_member_array(
        member_values: List[float],
        thresholds: Optional[List[float]] = None,
    ) -> Dict[str, Optional[float]]:
        """
        Compute ensemble metrics from actual member forecasts.
        Returns: mean, std, min, max, p10, p50, p90, iqr, exceedances.
        """
        if not member_values or len(member_values) == 0:
            return {
                "ensemble_status": "NOT_AVAILABLE",
                "member_count": 0,
                "mean": None,
                "std": None,
                "min": None,
                "max": None,
                "p10": None,
                "p50": None,
                "p90": None,
                "iqr": None,
            }

        arr = np.array(member_values, dtype=float)
        # Filter NaNs or non-finite values if any
        arr = arr[np.isfinite(arr)]
        if len(arr) == 0:
            return {
                "ensemble_status": "NOT_AVAILABLE",
                "member_count": 0,
                "mean": None,
                "std": None,
                "min": None,
                "max": None,
                "p10": None,
                "p50": None,
                "p90": None,
                "iqr": None,
            }

        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))
        p10_val = float(np.percentile(arr, 10))
        p50_val = float(np.percentile(arr, 50))
        p90_val = float(np.percentile(arr, 90))
        p25_val = float(np.percentile(arr, 25))
        p75_val = float(np.percentile(arr, 75))
        iqr_val = float(p75_val - p25_val)

        res: Dict[str, Optional[float]] = {
            "ensemble_status": "AVAILABLE",
            "member_count": len(arr),
            "mean": round(mean_val, 2),
            "std": round(std_val, 2),
            "min": round(min_val, 2),
            "max": round(max_val, 2),
            "p10": round(p10_val, 2),
            "p50": round(p50_val, 2),
            "p90": round(p90_val, 2),
            "iqr": round(iqr_val, 2),
        }

        # Threshold exceedance probabilities
        default_thresholds = thresholds or [15.6, 64.5, 115.6, 204.5]
        for t in default_thresholds:
            prob = float(np.mean(arr >= t) * 100.0)
            res[f"prob_exceed_{t}mm"] = round(prob, 1)

        return res

    @staticmethod
    def deterministic_to_ensemble_record(
        deterministic_value: float,
    ) -> Dict[str, Optional[float]]:
        """
        Return deterministic-only record when ensemble members are not available.
        Strict rule: Never fabricate fake ensemble members.
        """
        return {
            "ensemble_status": "NOT_AVAILABLE",
            "member_count": 1,
            "mean": round(deterministic_value, 2),
            "std": None,
            "min": round(deterministic_value, 2),
            "max": round(deterministic_value, 2),
            "p10": None,
            "p50": round(deterministic_value, 2),
            "p90": None,
            "iqr": None,
        }
