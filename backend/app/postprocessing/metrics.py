"""
Meteorological Verification Metrics Engine for PS26080.
Calculates:
- Continuous: RMSE, MAE, Mean Bias
- Categorical: POD, FAR, CSI, ETS across IMD heavy rainfall thresholds
- Spatial: Fractions Skill Score (FSS) with configurable neighborhood radius
- Regime-Conditional Verification breakdowns
"""

import math
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from pydantic import BaseModel, Field


class ContingencyTable2x2(BaseModel):
    """Standard 2x2 contingency table for binary event verification."""
    hits: int = Field(..., description="Hits (a): Forecast >= T, Observed >= T")
    false_alarms: int = Field(..., description="False Alarms (b): Forecast >= T, Observed < T")
    misses: int = Field(..., description="Misses (c): Forecast < T, Observed >= T")
    correct_negatives: int = Field(..., description="Correct Negatives (d): Forecast < T, Observed < T")
    total: int

    @property
    def pod(self) -> float:
        """Probability of Detection / Hit Rate: a / (a + c)."""
        denom = self.hits + self.misses
        return round(float(self.hits / denom), 3) if denom > 0 else 0.0

    @property
    def far(self) -> float:
        """False Alarm Ratio: b / (a + b)."""
        denom = self.hits + self.false_alarms
        return round(float(self.false_alarms / denom), 3) if denom > 0 else 0.0

    @property
    def csi(self) -> float:
        """Critical Success Index / Threat Score: a / (a + b + c)."""
        denom = self.hits + self.false_alarms + self.misses
        return round(float(self.hits / denom), 3) if denom > 0 else 0.0

    @property
    def ets(self) -> float:
        """Equitable Threat Score: (a - a_random) / (a + b + c - a_random)."""
        n = self.total
        if n == 0:
            return 0.0
        a_rand = ((self.hits + self.false_alarms) * (self.hits + self.misses)) / float(n)
        denom = (self.hits + self.false_alarms + self.misses) - a_rand
        if denom <= 0:
            return 0.0
        return round(float((self.hits - a_rand) / denom), 3)


class VerificationReport(BaseModel):
    """Complete evaluation report for a model over a test dataset."""
    model_id: str
    sample_count: int
    rmse_mm: float
    mae_mm: float
    mean_bias_mm: float
    
    # Categorical threshold metrics (at Heavy Rain >= 64.5mm)
    pod: float
    far: float
    csi: float
    ets: float
    fss_50km: float

    # Threshold-specific skill breakdown
    threshold_metrics: Dict[str, Dict[str, float]] = Field(default_factory=dict)


class PostProcessingVerificationEngine:
    """
    Computes standard WMO / NCMRWF forecast verification benchmarks.
    """

    @staticmethod
    def compute_continuous_metrics(
        forecast: np.ndarray,
        observed: np.ndarray,
    ) -> Tuple[float, float, float]:
        """
        Compute continuous Root Mean Square Error (RMSE), Mean Absolute Error (MAE), and Mean Bias.
        """
        f = np.asarray(forecast, dtype=np.float64)
        o = np.asarray(observed, dtype=np.float64)

        diff = f - o
        rmse = float(np.sqrt(np.mean(diff ** 2)))
        mae = float(np.mean(np.abs(diff)))
        mean_bias = float(np.mean(diff))

        return round(rmse, 2), round(mae, 2), round(mean_bias, 2)

    @staticmethod
    def compute_contingency_table(
        forecast: np.ndarray,
        observed: np.ndarray,
        threshold_mm: float = 64.5,
    ) -> ContingencyTable2x2:
        """
        Construct 2x2 contingency matrix for threshold exceedance.
        """
        f = np.asarray(forecast) >= threshold_mm
        o = np.asarray(observed) >= threshold_mm

        hits = int(np.sum(f & o))
        false_alarms = int(np.sum(f & (~o)))
        misses = int(np.sum((~f) & o))
        correct_negatives = int(np.sum((~f) & (~o)))
        total = len(forecast)

        return ContingencyTable2x2(
            hits=hits,
            false_alarms=false_alarms,
            misses=misses,
            correct_negatives=correct_negatives,
            total=total,
        )

    @staticmethod
    def compute_fractions_skill_score(
        forecast_grid: np.ndarray,
        observed_grid: np.ndarray,
        threshold_mm: float = 64.5,
        window_size: int = 5,
    ) -> float:
        """
        Compute Fractions Skill Score (FSS) over 2D spatial grid matrices.
        FSS = 1 - (MSE_n / MSE_ref)
        """
        f_binary = (forecast_grid >= threshold_mm).astype(np.float64)
        o_binary = (observed_grid >= threshold_mm).astype(np.float64)

        if f_binary.ndim == 1:
            # Reshape 1D array into square grid if needed
            side = int(math.isqrt(len(f_binary)))
            if side * side == len(f_binary):
                f_binary = f_binary.reshape((side, side))
                o_binary = o_binary.reshape((side, side))
            else:
                # 1D moving average fallback
                w = min(len(f_binary), window_size)
                f_frac = np.convolve(f_binary, np.ones(w) / w, mode="same")
                o_frac = np.convolve(o_binary, np.ones(w) / w, mode="same")
                mse = np.mean((f_frac - o_frac) ** 2)
                mse_ref = np.mean(f_frac ** 2) + np.mean(o_frac ** 2)
                if mse_ref <= 1e-6:
                    return 1.0 if np.array_equal(f_binary, o_binary) else 0.0
                return round(float(max(0.0, 1.0 - (mse / mse_ref))), 3)

        # 2D Spatial Box Smoothing
        from scipy.ndimage import uniform_filter
        f_frac = uniform_filter(f_binary, size=window_size, mode="constant")
        o_frac = uniform_filter(o_binary, size=window_size, mode="constant")

        mse = np.mean((f_frac - o_frac) ** 2)
        mse_ref = np.mean(f_frac ** 2) + np.mean(o_frac ** 2)

        if mse_ref <= 1e-6:
            return 1.0 if np.array_equal(f_binary, o_binary) else 0.0

        fss = max(0.0, 1.0 - (mse / mse_ref))
        return round(float(fss), 3)

    @classmethod
    def evaluate_model(
        cls,
        model_id: str,
        forecast: np.ndarray,
        observed: np.ndarray,
        thresholds: Optional[List[float]] = None,
    ) -> VerificationReport:
        """
        Generate complete evaluation report across continuous and threshold metrics.
        """
        if thresholds is None:
            thresholds = [64.5, 115.6, 204.5]

        rmse, mae, bias = cls.compute_continuous_metrics(forecast, observed)

        # Primary 64.5mm metrics
        table_heavy = cls.compute_contingency_table(forecast, observed, threshold_mm=64.5)
        fss = cls.compute_fractions_skill_score(forecast, observed, threshold_mm=64.5, window_size=5)

        thresh_metrics = {}
        for t in thresholds:
            tbl = cls.compute_contingency_table(forecast, observed, threshold_mm=t)
            thresh_metrics[f"{t}mm"] = {
                "pod": tbl.pod,
                "far": tbl.far,
                "csi": tbl.csi,
                "ets": tbl.ets,
                "hits": tbl.hits,
                "misses": tbl.misses,
                "false_alarms": tbl.false_alarms,
            }

        return VerificationReport(
            model_id=model_id,
            sample_count=len(forecast),
            rmse_mm=rmse,
            mae_mm=mae,
            mean_bias_mm=bias,
            pod=table_heavy.pod,
            far=table_heavy.far,
            csi=table_heavy.csi,
            ets=table_heavy.ets,
            fss_50km=fss,
            threshold_metrics=thresh_metrics,
        )

    @classmethod
    def compute_regime_conditional_benchmarks(
        cls,
        models_forecasts: Dict[str, np.ndarray],
        observed: np.ndarray,
        regimes: List[str],
    ) -> Dict[str, Dict[str, VerificationReport]]:
        """
        Compute verification metrics broken down by weather regime for all 4 models.

        Returns
        -------
        Dict[regime_name, Dict[model_id, VerificationReport]]
        """
        reg_arr = np.array(regimes)
        unique_regimes = list(np.unique(reg_arr))

        benchmark: Dict[str, Dict[str, VerificationReport]] = {}

        # 1. Overall benchmark (all samples)
        benchmark["ALL_SAMPLES"] = {}
        for m_id, f_arr in models_forecasts.items():
            benchmark["ALL_SAMPLES"][m_id] = cls.evaluate_model(m_id, f_arr, observed)

        # 2. Breakdown per regime
        for reg in unique_regimes:
            mask = (reg_arr == reg)
            if np.sum(mask) >= 5:
                benchmark[reg] = {}
                obs_sub = observed[mask]
                for m_id, f_arr in models_forecasts.items():
                    f_sub = f_arr[mask]
                    benchmark[reg][m_id] = cls.evaluate_model(m_id, f_sub, obs_sub)

        return benchmark
