"""
Empirical Quantile Mapping (EQM) Statistical Bias Correction Model for PS26080.
Fits empirical cumulative distribution functions on historical training NWP and observed precipitation,
and applies inverse transformation to calibrate forecasts during inference.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from backend.app.postprocessing.base import (
    BasePostProcessingModel,
    PostProcessingInput,
    PostProcessingOutput,
)


class EmpiricalQuantileMappingModel(BasePostProcessingModel):
    """
    Statistical Empirical Quantile Mapping baseline.
    Maps raw NWP precipitation quantiles to observed ground truth quantiles.
    """

    def __init__(
        self,
        model_id: str = "quantile_mapping",
        model_name: str = "Empirical Quantile Mapping (EQM)",
        version: str = "EQM_v1.0_Empirical",
        n_quantiles: int = 500,
    ):
        super().__init__(model_id=model_id, model_name=model_name, version=version)
        self.n_quantiles = n_quantiles
        self.quantiles: np.ndarray = np.linspace(0.001, 0.999, n_quantiles)
        self.nwp_quantiles: Optional[np.ndarray] = None
        self.obs_quantiles: Optional[np.ndarray] = None
        self.dry_threshold_mm: float = 0.1
        self.dry_ratio_obs: float = 0.0
        self.dry_ratio_nwp: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray, raw_nwp: Optional[np.ndarray] = None, observed: Optional[np.ndarray] = None, **kwargs) -> "EmpiricalQuantileMappingModel":
        """
        Fit empirical CDFs on historical training data.

        Parameters
        ----------
        X : np.ndarray
            Feature matrix (where column 0 is raw_nwp_rainfall).
        y : np.ndarray
            Residual errors (observed - raw_nwp).
        raw_nwp : np.ndarray, optional
            Direct array of training raw NWP precipitation.
        observed : np.ndarray, optional
            Direct array of training observed precipitation.
        """
        nwp_samples = raw_nwp if raw_nwp is not None else X[:, 0]
        obs_samples = observed if observed is not None else (nwp_samples + y)

        # Sanitize non-negative & finite
        nwp_clean = np.nan_to_num(np.maximum(0.0, nwp_samples), nan=0.0)
        obs_clean = np.nan_to_num(np.maximum(0.0, obs_samples), nan=0.0)

        # Calculate dry-day probabilities
        self.dry_ratio_nwp = float(np.mean(nwp_clean <= self.dry_threshold_mm))
        self.dry_ratio_obs = float(np.mean(obs_clean <= self.dry_threshold_mm))

        # Fit empirical quantile arrays
        self.nwp_quantiles = np.percentile(nwp_clean, self.quantiles * 100.0)
        self.obs_quantiles = np.percentile(obs_clean, self.quantiles * 100.0)

        # Ensure monotonicity
        self.nwp_quantiles = np.maximum.accumulate(self.nwp_quantiles)
        self.obs_quantiles = np.maximum.accumulate(self.obs_quantiles)

        self.is_fitted = True
        self.training_period = "2018-2022 (Historical JJAS Training Period)"
        return self

    def predict_corrected_scalar(self, raw_rain: float) -> float:
        """Apply quantile mapping to a single raw rainfall forecast value."""
        if not self.is_fitted:
            # Fallback scaling if called before fit
            return max(0.0, raw_rain * 1.18)

        if raw_rain <= self.dry_threshold_mm:
            return 0.0

        # Find quantile rank in NWP distribution
        rank = np.interp(raw_rain, self.nwp_quantiles, self.quantiles, left=0.0, right=1.0)

        # Map to observed distribution quantile
        if rank >= 0.999:
            # Extreme value extrapolation: preserve delta from top quantile
            top_nwp = self.nwp_quantiles[-1]
            top_obs = self.obs_quantiles[-1]
            delta = raw_rain - top_nwp
            corrected = top_obs + delta * (top_obs / max(1.0, top_nwp))
        else:
            corrected = float(np.interp(rank, self.quantiles, self.obs_quantiles))

        return max(0.0, float(corrected))

    def predict_error(self, X: np.ndarray) -> np.ndarray:
        """Predict residual errors (corrected - raw_nwp) for batch feature matrix."""
        raw_vals = X[:, 0]
        corrected_vals = np.array([self.predict_corrected_scalar(r) for r in raw_vals], dtype=np.float32)
        return corrected_vals - raw_vals

    def predict(self, sample: PostProcessingInput) -> PostProcessingOutput:
        """Generate full standardized PostProcessingOutput for EQM."""
        raw = max(0.0, sample.raw_nwp_rainfall)
        corrected = self.predict_corrected_scalar(raw)
        delta = corrected - raw

        # Uncertainty estimation (statistical spread of EQM ~ 18%)
        spread = max(2.0, corrected * 0.18)
        p10 = max(0.0, corrected - 1.28 * spread)
        p50 = corrected
        p90 = corrected + 1.28 * spread

        # Heavy rainfall probabilities via logistic sigmoid calibration
        def _calc_prob(val: float, thresh: float, sp: float) -> float:
            z = (val - thresh) / max(6.0, sp * 1.5)
            return float(1.0 / (1.0 + np.exp(-z)))

        p_heavy = min(0.99, max(0.01, _calc_prob(corrected, 64.5, spread)))
        p_vheavy = min(p_heavy * 0.82, max(0.01, _calc_prob(corrected, 115.6, spread)))
        p_extreme = min(p_vheavy * 0.45, max(0.01, _calc_prob(corrected, 204.5, spread)))

        # 24h hourly synthesis
        hourly = [round((corrected / 24.0) * (0.8 + 0.4 * np.sin(i * 0.26)), 2) for i in range(24)]

        return PostProcessingOutput(
            model_id=self.model_id,
            model_name=self.model_name,
            raw_rainfall_24h_mm=round(raw, 2),
            corrected_rainfall_24h_mm=round(corrected, 2),
            predicted_bias_delta_mm=round(delta, 2),
            rainfall_p10_mm=round(p10, 2),
            rainfall_p50_mm=round(p50, 2),
            rainfall_p90_mm=round(p90, 2),
            uncertainty_width_mm=round(p90 - p10, 2),
            heavy_rain_prob_ge_64_5mm=round(p_heavy, 3),
            very_heavy_rain_prob_ge_115_6mm=round(p_vheavy, 3),
            extreme_rain_prob_ge_204_5mm=round(p_extreme, 3),
            hourly_series_mm=hourly,
            primary_regime=sample.primary_regime,
            regime_confidence=sample.regime_confidence,
            data_source=sample.data_source,
            is_demo=sample.is_demo,
        )
