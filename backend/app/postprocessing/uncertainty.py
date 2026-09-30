"""
Uncertainty Quantification and Probabilistic Bounds Engine for PS26080.
Calculates calibrated P10, P50, P90 percentiles and empirical residual spread.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field


class UncertaintyBounds(BaseModel):
    """Container for quantified forecast uncertainty percentiles."""
    p10_mm: float = Field(..., ge=0.0, description="10th percentile / lower forecast bound (mm)")
    p50_mm: float = Field(..., ge=0.0, description="Median forecast value (mm)")
    p90_mm: float = Field(..., ge=0.0, description="90th percentile / upper forecast bound (mm)")
    uncertainty_width_mm: float = Field(..., ge=0.0, description="Uncertainty band width (P90 - P10) in mm")
    uncertainty_category: str = Field(..., description="LOW, MODERATE, HIGH, EXTREME uncertainty")


class UncertaintyQuantifier:
    """
    Quantifies predictive uncertainty for deterministic and ensemble forecast corrections.
    """

    @staticmethod
    def estimate_uncertainty(
        corrected_rainfall_mm: float,
        model_id: str = "regime_aware_ml",
        ensemble_members: Optional[List[float]] = None,
    ) -> UncertaintyBounds:
        """
        Derive calibrated P10, P50, P90 uncertainty bounds.

        Parameters
        ----------
        corrected_rainfall_mm : float
            Calibrated point forecast in mm.
        model_id : str
            Model type ('raw_nwp', 'quantile_mapping', 'global_ml', 'regime_aware_ml').
        ensemble_members : List[float], optional
            Raw ensemble member values if available.

        Returns
        -------
        UncertaintyBounds
            Calibrated percentiles and uncertainty categorization.
        """
        corr = max(0.0, float(corrected_rainfall_mm))

        if ensemble_members and len(ensemble_members) >= 5:
            # Empirical ensemble percentiles
            ens_arr = np.maximum(0.0, np.array(ensemble_members))
            p10 = float(np.percentile(ens_arr, 10.0))
            p50 = float(np.percentile(ens_arr, 50.0))
            p90 = float(np.percentile(ens_arr, 90.0))
        else:
            # Calibrated model-specific residual spread factor
            if model_id == "regime_aware_ml":
                spread_factor = 0.10  # Tightest uncertainty
            elif model_id == "global_ml":
                spread_factor = 0.14
            elif model_id == "quantile_mapping":
                spread_factor = 0.18
            else:  # raw_nwp
                spread_factor = 0.22

            spread = max(1.5, corr * spread_factor)
            p10 = max(0.0, corr - 1.28 * spread)
            p50 = corr
            p90 = corr + 1.28 * spread

        width = round(max(0.0, p90 - p10), 2)

        # Categorize uncertainty
        if width < 8.0:
            category = "LOW"
        elif width < 22.0:
            category = "MODERATE"
        elif width < 50.0:
            category = "HIGH"
        else:
            category = "EXTREME"

        return UncertaintyBounds(
            p10_mm=round(p10, 2),
            p50_mm=round(p50, 2),
            p90_mm=round(p90, 2),
            uncertainty_width_mm=width,
            uncertainty_category=category,
        )
