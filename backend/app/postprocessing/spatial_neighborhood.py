"""
Spatial Neighborhood Feature Extraction & Smoothness Diagnostics Engine (Phase 13).
Extracts multi-scale neighborhood statistics (1x1, 3x3, 5x5, 9x9) from NWP/atmospheric input fields
with zero observational target leakage, and computes physical smoothness metrics.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy.ndimage import uniform_filter, generic_filter, sobel, laplace

from backend.app.schemas.spatial_postprocess import SpatialSmoothnessDiagnostics


class SpatialNeighborhoodEngine:
    """
    Computes spatial context features and field diagnostics on 2D regular grids.
    """

    @classmethod
    def extract_neighborhood_features_2d(
        cls,
        grid_2d: np.ndarray,
        window_sizes: List[int] = [3, 5],
    ) -> Dict[str, np.ndarray]:
        """
        Compute multi-scale spatial neighborhood statistics from an input 2D forecast field.
        Strict Leakage Rule: Must ONLY be applied to forecast/atmospheric input grids, NEVER target ground truth.

        Parameters
        ----------
        grid_2d : np.ndarray
            2D numpy array [H, W] representing input field (e.g. raw NWP rainfall)
        window_sizes : List[int]
            List of odd window sizes in cells (e.g. 3 for 3x3, 5 for 5x5)

        Returns
        -------
        Dict[str, np.ndarray] : Dictionary of 2D feature grids matching input shape [H, W]
        """
        arr = np.asarray(grid_2d, dtype=np.float64)
        features: Dict[str, np.ndarray] = {
            "center": arr.copy()
        }

        # Spatial gradients (Sobel filter / central differences)
        grad_y, grad_x = np.gradient(arr)
        features["grad_x"] = grad_x
        features["grad_y"] = grad_y
        features["grad_magnitude"] = np.sqrt(grad_x**2 + grad_y**2)

        for w in window_sizes:
            if w <= 1:
                continue
            
            # Neighborhood mean
            mean_w = uniform_filter(arr, size=w, mode="nearest")
            features[f"mean_{w}x{w}"] = mean_w

            # Local anomaly: cell value minus neighborhood mean
            features[f"anomaly_{w}x{w}"] = arr - mean_w

            # Neighborhood standard deviation (variance = E[X^2] - (E[X])^2)
            sq_mean = uniform_filter(arr**2, size=w, mode="nearest")
            var_w = np.maximum(0.0, sq_mean - mean_w**2)
            features[f"std_{w}x{w}"] = np.sqrt(var_w)

        return features

    @classmethod
    def extract_cell_neighborhood_vector(
        cls,
        grid_2d: np.ndarray,
        row_idx: int,
        col_idx: int,
        window_sizes: List[int] = [3, 5],
    ) -> np.ndarray:
        """
        Extract a 1D feature vector of neighborhood statistics for a single cell (row_idx, col_idx).
        """
        feats_dict = cls.extract_neighborhood_features_2d(grid_2d, window_sizes)
        vec = [feats_dict[k][row_idx, col_idx] for k in sorted(feats_dict.keys())]
        return np.array(vec, dtype=np.float64)

    @classmethod
    def compute_smoothness_diagnostics(
        cls,
        field_2d: np.ndarray,
    ) -> SpatialSmoothnessDiagnostics:
        """
        Evaluate numerical and physical spatial smoothness diagnostics for a 2D rainfall field.
        Calculates Total Variation (TV), mean gradient step, Laplacian variance, and peak gradient.
        """
        arr = np.asarray(field_2d, dtype=np.float64)
        if arr.ndim != 2:
            raise ValueError(f"Expected 2D field, got shape {arr.shape}")

        # Finite differences
        diff_y = np.abs(np.diff(arr, axis=0))
        diff_x = np.abs(np.diff(arr, axis=1))

        # Total Variation (L1 norm of gradients)
        tv = float(np.sum(diff_y) + np.sum(diff_x))

        # Gradient field
        gy, gx = np.gradient(arr)
        g_mag = np.sqrt(gy**2 + gx**2)
        mean_grad = float(np.mean(g_mag))
        max_grad = float(np.max(g_mag))

        # Laplacian operator (2nd derivative / curvature)
        lap = laplace(arr, mode="nearest")
        lap_var = float(np.var(lap))

        return SpatialSmoothnessDiagnostics(
            total_variation=round(tv, 2),
            mean_gradient=round(mean_grad, 3),
            laplacian_variance=round(lap_var, 3),
            max_gradient=round(max_grad, 2),
        )
