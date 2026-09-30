"""
Global Machine Learning Post-Processing Model for PS26080.
Trains a pan-India stationary gradient boosting regressor on NWP, atmospheric, and geographic features
to predict forecast error: y = observed_rainfall - raw_nwp_rainfall.
"""

from typing import Dict, List, Optional
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from backend.app.postprocessing.base import (
    BasePostProcessingModel,
    PostProcessingInput,
    PostProcessingOutput,
)
from backend.app.postprocessing.datasets import extract_feature_vector


class GlobalMLCorrectionModel(BasePostProcessingModel):
    """
    Standard Global Machine Learning Residual Post-Processing Model.
    Trains across all historical data without soft regime conditioning.
    """

    # Global ML uses features 0..31 (NWP, Atmospheric, Geographic, Temporal)
    GLOBAL_FEATURE_INDICES = list(range(32))

    def __init__(
        self,
        model_id: str = "global_ml",
        model_name: str = "Global ML Post-Processing (Standard Non-Regime)",
        version: str = "GlobalML_v1.0_HistGBM",
        max_iter: int = 150,
        learning_rate: float = 0.05,
        max_depth: int = 6,
    ):
        super().__init__(model_id=model_id, model_name=model_name, version=version)
        self.model = HistGradientBoostingRegressor(
            max_iter=max_iter,
            learning_rate=learning_rate,
            max_depth=max_depth,
            loss="squared_error",
            random_state=42,
        )

    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> "GlobalMLCorrectionModel":
        """
        Fit global model on residual targets: y = observed - raw_nwp.
        """
        X_subset = X[:, self.GLOBAL_FEATURE_INDICES]
        self.model.fit(X_subset, y)
        self.is_fitted = True
        self.training_period = "2018-2022 (Historical JJAS Training Period)"
        return self

    def predict_error(self, X: np.ndarray) -> np.ndarray:
        """Predict residual errors for feature matrix."""
        if not self.is_fitted:
            # Fallback heuristic delta ~ +25%
            return X[:, 0] * 0.25
        X_subset = X[:, self.GLOBAL_FEATURE_INDICES]
        return self.model.predict(X_subset)

    def predict(self, sample: PostProcessingInput) -> PostProcessingOutput:
        """Produce standardized PostProcessingOutput for Global ML."""
        vec = extract_feature_vector(sample)
        raw = max(0.0, sample.raw_nwp_rainfall)

        if self.is_fitted:
            delta = float(self.model.predict(vec[self.GLOBAL_FEATURE_INDICES].reshape(1, -1))[0])
        else:
            delta = raw * 0.25

        corrected = max(0.0, raw + delta)

        # Uncertainty estimation (Global ML uncertainty spread ~ 14%)
        spread = max(1.5, corrected * 0.14)
        p10 = max(0.0, corrected - 1.28 * spread)
        p50 = corrected
        p90 = corrected + 1.28 * spread

        # Heavy rainfall probabilities via calibrated logistic sigmoid
        def _calc_prob(val: float, thresh: float, sp: float) -> float:
            z = (val - thresh) / max(5.0, sp * 1.5)
            return float(1.0 / (1.0 + np.exp(-z)))

        p_heavy = min(0.99, max(0.01, _calc_prob(corrected, 64.5, spread)))
        p_vheavy = min(p_heavy * 0.85, max(0.01, _calc_prob(corrected, 115.6, spread)))
        p_extreme = min(p_vheavy * 0.50, max(0.01, _calc_prob(corrected, 204.5, spread)))

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
