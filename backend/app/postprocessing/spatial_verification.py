"""
Spatial Meteorological Verification & Multi-Scale Evaluation Engine (Phase 13).
Computes:
- 2D Pattern Correlation
- Spatial Gradient Vector RMSE
- Multi-Scale Fractions Skill Score (FSS) across physical footprints (25km, 50km, 100km)
- 2D Continuous and Categorical Skill Benchmarks (RMSE, MAE, Bias, POD, FAR, CSI, ETS)
"""

import math
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

from backend.app.postprocessing.metrics import PostProcessingVerificationEngine
from backend.app.schemas.spatial_postprocess import SpatialVerificationSummary


class SpatialVerificationEngine:
    """
    Forensic verification engine for 2D spatial rainfall fields.
    """

    @classmethod
    def compute_pattern_correlation(
        cls,
        forecast_grid: np.ndarray,
        observed_grid: np.ndarray,
    ) -> float:
        """
        Compute 2D Pearson spatial pattern correlation coefficient between forecast and observed fields.
        """
        f = np.asarray(forecast_grid, dtype=np.float64).flatten()
        o = np.asarray(observed_grid, dtype=np.float64).flatten()

        f_mean = np.mean(f)
        o_mean = np.mean(o)

        f_anom = f - f_mean
        o_anom = o - o_mean

        denom = np.sqrt(np.sum(f_anom ** 2) * np.sum(o_anom ** 2))
        if denom <= 1e-9:
            return 0.0

        r = float(np.sum(f_anom * o_anom) / denom)
        return round(float(max(-1.0, min(1.0, r))), 3)

    @classmethod
    def compute_gradient_rmse(
        cls,
        forecast_grid: np.ndarray,
        observed_grid: np.ndarray,
    ) -> float:
        """
        Compute Root Mean Square Error of the spatial gradient vector fields.
        """
        f = np.asarray(forecast_grid, dtype=np.float64)
        o = np.asarray(observed_grid, dtype=np.float64)

        fy, fx = np.gradient(f)
        oy, ox = np.gradient(o)

        diff_sq = (fx - ox) ** 2 + (fy - oy) ** 2
        grad_rmse = float(np.sqrt(np.mean(diff_sq)))
        return round(grad_rmse, 3)

    @classmethod
    def evaluate_spatial_model(
        cls,
        model_id: str,
        model_name: str,
        forecast_grids: List[np.ndarray],
        observed_grids: List[np.ndarray],
        threshold_mm: float = 64.5,
    ) -> SpatialVerificationSummary:
        """
        Evaluate a complete test set of 2D spatial forecast grids against matching observations.
        """
        if not forecast_grids or not observed_grids or len(forecast_grids) != len(observed_grids):
            raise ValueError("Forecast and observed grid lists must be non-empty and matching in length")

        sample_count = len(forecast_grids)
        all_f = np.concatenate([g.flatten() for g in forecast_grids])
        all_o = np.concatenate([g.flatten() for g in observed_grids])
        total_cells = len(all_f)

        # Continuous metrics
        rmse, mae, mean_bias = PostProcessingVerificationEngine.compute_continuous_metrics(all_f, all_o)

        # Categorical metrics at 64.5mm
        table = PostProcessingVerificationEngine.compute_contingency_table(all_f, all_o, threshold_mm=threshold_mm)

        # Multi-scale FSS averages
        fss_25_list = []
        fss_50_list = []
        fss_100_list = []
        pattern_corrs = []
        grad_rmses = []
        tvs = []

        for f_grid, o_grid in zip(forecast_grids, observed_grids):
            # 25 km (window = 1)
            s25 = PostProcessingVerificationEngine.compute_fractions_skill_score(f_grid, o_grid, threshold_mm, window_size=1)
            if s25 is not None:
                fss_25_list.append(s25)

            # 50 km (window = 5)
            s50 = PostProcessingVerificationEngine.compute_fractions_skill_score(f_grid, o_grid, threshold_mm, window_size=5)
            if s50 is not None:
                fss_50_list.append(s50)

            # 100 km (window = 9)
            s100 = PostProcessingVerificationEngine.compute_fractions_skill_score(f_grid, o_grid, threshold_mm, window_size=9)
            if s100 is not None:
                fss_100_list.append(s100)

            # Spatial field diagnostics
            pattern_corrs.append(cls.compute_pattern_correlation(f_grid, o_grid))
            grad_rmses.append(cls.compute_gradient_rmse(f_grid, o_grid))
            
            # Total variation
            diff_y = np.abs(np.diff(f_grid, axis=0))
            diff_x = np.abs(np.diff(f_grid, axis=1))
            tvs.append(float(np.sum(diff_y) + np.sum(diff_x)))

        mean_fss_25 = round(float(np.mean(fss_25_list)), 3) if fss_25_list else None
        mean_fss_50 = round(float(np.mean(fss_50_list)), 3) if fss_50_list else None
        mean_fss_100 = round(float(np.mean(fss_100_list)), 3) if fss_100_list else None
        mean_pattern_corr = round(float(np.mean(pattern_corrs)), 3) if pattern_corrs else 0.0
        mean_grad_rmse = round(float(np.mean(grad_rmses)), 3) if grad_rmses else 0.0
        mean_tv = round(float(np.mean(tvs)), 2) if tvs else 0.0

        return SpatialVerificationSummary(
            model_id=model_id,
            model_name=model_name,
            sample_count=sample_count,
            total_grid_cells=total_cells,
            rmse_mm=rmse,
            mae_mm=mae,
            mean_bias_mm=mean_bias,
            csi_64_5=table.csi,
            ets_64_5=table.ets,
            pod_64_5=table.pod,
            far_64_5=table.far,
            fss_25km=mean_fss_25,
            fss_50km=mean_fss_50,
            fss_100km=mean_fss_100,
            pattern_correlation=mean_pattern_corr,
            gradient_rmse=mean_grad_rmse,
            total_variation=mean_tv,
            status="EXPERIMENTAL_EVALUATION",
        )
