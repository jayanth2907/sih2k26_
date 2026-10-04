"""
Spatial Post-Processing Pipeline Coordinator (Phase 13).
Integrates 2D spatial models, probabilistic exceedance mapping, quantile uncertainty,
spatial smoothness diagnostics, and forensic metadata provenance.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from backend.app.postprocessing.spatial_grid import SpatialGridManager
from backend.app.postprocessing.spatial_models import SpatialRegimeAwareUNet, SpatialResidualBaseline
from backend.app.postprocessing.spatial_neighborhood import SpatialNeighborhoodEngine
from backend.app.postprocessing.spatial_probability import SpatialProbabilityEngine
from backend.app.postprocessing.spatial_verification import SpatialVerificationEngine
from backend.app.schemas.spatial_postprocess import (
    SpatialGridDefinition,
    SpatialPredictionOutput,
    SpatialRainfallSample,
    SpatialSmoothnessDiagnostics,
    SpatialStatusResponse,
    SpatialVerificationSummary,
)

logger = logging.getLogger("rainfall_backend.postprocessing.spatial_pipeline")


class SpatialPostProcessingPipeline:
    """
    Coordinator for 2D spatial meteorological post-processing and uncertainty fields.
    """

    _INSTANCE: Optional["SpatialPostProcessingPipeline"] = None

    def __init__(self):
        self.baseline_model = SpatialResidualBaseline()
        self.regime_conv_model = SpatialRegimeAwareUNet()
        self.registered_models = [
            "SPATIAL_RESIDUAL_BASELINE_V1",
            "SPATIAL_REGIME_AWARE_V1",
            "SPATIAL_REGIME_TEMPORAL_V1",
        ]

    @classmethod
    def get_instance(cls) -> "SpatialPostProcessingPipeline":
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    def execute_spatial_postprocessing(
        self,
        sample: SpatialRainfallSample,
        model_id: str = "SPATIAL_REGIME_AWARE_V1",
    ) -> SpatialPredictionOutput:
        """
        Execute full spatial post-processing on a 2D meteorological sample.
        """
        raw_nwp = np.asarray(sample.raw_nwp_grid, dtype=np.float64)
        if raw_nwp.ndim != 2:
            raise ValueError(f"Expected 2D raw NWP grid, got shape {raw_nwp.shape}")

        # 1. Execute Selected Spatial Model
        if model_id == "SPATIAL_RESIDUAL_BASELINE_V1":
            corrected_grid, residual_grid = self.baseline_model.predict_corrected_grid(sample)
            version_str = self.baseline_model.version
        else:
            corrected_grid, residual_grid = self.regime_conv_model.predict_corrected_grid(sample)
            version_str = self.regime_conv_model.version

        # 2. Determine Dominant Regime
        dominant_regime = max(sample.regime_probabilities.items(), key=lambda x: x[1])[0]

        # 3. Generate Calibrated Spatial Quantiles (0 <= P10 <= P50 <= P90)
        p10, p50, p90 = SpatialProbabilityEngine.generate_spatial_quantiles(
            corrected_grid=corrected_grid,
            dominant_regime=dominant_regime,
        )

        # 4. Generate Calibrated Heavy Rainfall Exceedance Fields (P64.5 >= P115.6 >= P204.5)
        p64, p115, p204 = SpatialProbabilityEngine.generate_exceedance_probabilities(
            corrected_grid=corrected_grid,
            dominant_regime=dominant_regime,
        )

        # 5. Compute Spatial Field Smoothness Diagnostics
        smoothness = SpatialNeighborhoodEngine.compute_smoothness_diagnostics(corrected_grid)

        # 6. Forensic Provenance Metadata
        provenance = {
            "dataset_id": "IMD_ERA5_JJAS_2010_2023_0.25deg",
            "model_id": model_id,
            "model_version": version_str,
            "grid_definition": sample.grid.grid_name,
            "resolution_deg": sample.grid.resolution_deg,
            "training_period": "2010–2019 JJAS",
            "validation_period": "2020–2021 JJAS",
            "evaluation_period": "2022–2023 JJAS",
            "uncertainty_status": "CALIBRATED_EMPIRICAL_RESIDUALS",
            "probability_method": "RESIDUAL_DISTRIBUTION_LOGISTIC_MAPPING",
            "is_fallback": sample.is_fallback,
            "leakage_controls": "CHRONOLOGICAL_SPLIT_AND_NO_FUTURE_OR_OBSERVATIONAL_NEIGHBORHOOD_LEAKAGE",
        }

        return SpatialPredictionOutput(
            grid=sample.grid,
            raw_nwp_grid=raw_nwp.tolist(),
            corrected_grid=corrected_grid.tolist(),
            residual_delta_grid=residual_grid.tolist(),
            p10_grid=p10.tolist(),
            p50_grid=p50.tolist(),
            p90_grid=p90.tolist(),
            prob_heavy_ge_64_5_grid=p64.tolist(),
            prob_very_heavy_ge_115_6_grid=p115.tolist(),
            prob_extreme_ge_204_5_grid=p204.tolist(),
            dominant_regime=dominant_regime,
            regime_probabilities=sample.regime_probabilities,
            smoothness_diagnostics=smoothness,
            model_id=model_id,
            model_version=version_str,
            uncertainty_status="CALIBRATED_EMPIRICAL_RESIDUALS",
            probability_method="RESIDUAL_DISTRIBUTION_LOGISTIC_MAPPING",
            provenance=provenance,
        )

    def get_operational_status(self) -> SpatialStatusResponse:
        """Query operational status of the spatial post-processing engine."""
        canonical_grid = SpatialGridManager.create_regional_patch_grid()
        return SpatialStatusResponse(
            status="OPERATIONAL_READY",
            phase="PHASE_13_SPATIAL_INTELLIGENCE",
            registered_spatial_models=self.registered_models,
            active_dashboard_model="RegimeML_v2.0_SoftConditionedMoE",
            production_model_replaced=False,
            canonical_grid=canonical_grid,
            deep_spatial_model_status="EXPERIMENTAL_SUPPORTED",
            mode="SPATIAL_NWP_POSTPROCESSING",
        )

    def generate_demo_sample(
        self,
        patch_size: int = 16,
        dominant_regime: str = "ACTIVE_MONSOON",
    ) -> SpatialRainfallSample:
        """
        Generate deterministic 2D synthetic spatial test fixture for unit tests and offline demos.
        """
        grid = SpatialGridManager.create_regional_patch_grid(
            center_lat=18.5,
            center_lon=73.5,
            size_cells=patch_size,
            resolution_deg=0.25,
            grid_name="Demo_WesternGhats_Patch",
        )
        h, w = grid.grid_shape

        # Synthetic 2D Gaussian rainfall pattern centered on terrain
        y_indices, x_indices = np.indices((h, w))
        dist_sq = (y_indices - h / 2.0) ** 2 + (x_indices - w / 2.0) ** 2
        raw_rain = 45.0 * np.exp(-dist_sq / (2.0 * (patch_size / 3.0) ** 2)) + 15.0

        # Elevation and orographic lift proxy
        elev = 200.0 + 800.0 * np.exp(-(x_indices - w / 3.0) ** 2 / 10.0)
        oro_lift = np.gradient(elev, axis=1) * 0.15

        obs_rain = raw_rain + 0.3 * oro_lift + np.sin(x_indices / 2.0) * 5.0

        regime_probs = {
            "ACTIVE_MONSOON": 0.65 if dominant_regime == "ACTIVE_MONSOON" else 0.1,
            "BREAK_MONSOON": 0.65 if dominant_regime == "BREAK_MONSOON" else 0.05,
            "MONSOON_LOW_LPS": 0.65 if dominant_regime == "MONSOON_LOW_LPS" else 0.1,
            "COASTAL_CONVERGENCE": 0.15,
            "OROGRAPHIC_RAINFALL": 0.70 if dominant_regime == "OROGRAPHIC_RAINFALL" else 0.15,
            "WESTERN_DISTURBANCE": 0.02,
            "NEUTRAL": 0.03,
        }

        return SpatialRainfallSample(
            timestamp="2024-07-15T00:00:00Z",
            valid_time="2024-07-16T00:00:00Z",
            lead_time_hours=24,
            grid=grid,
            raw_nwp_grid=np.round(raw_rain, 2).tolist(),
            observed_grid=np.round(obs_rain, 2).tolist(),
            atmospheric_channels={
                "ivt": np.round(350.0 + 100.0 * np.sin(y_indices / 3.0), 1).tolist(),
                "cape": np.round(1200.0 + 300.0 * np.cos(x_indices / 3.0), 1).tolist(),
                "rh850": np.round(85.0 + 5.0 * np.sin(y_indices / 2.0), 1).tolist(),
            },
            terrain_channels={
                "elevation": np.round(elev, 1).tolist(),
                "orographic_lift": np.round(oro_lift, 2).tolist(),
                "coastal_convergence": np.round(np.maximum(0.0, 5.0 - x_indices * 0.5), 2).tolist(),
            },
            regime_probabilities=regime_probs,
            temporal_regime_features={
                "day1_regime_prob": 0.65,
                "day2_regime_prob": 0.60,
                "persistence_prob": 0.61,
                "transition_prob": 0.39,
                "forecast_horizon_days": 1.0,
            },
            provenance_source="TEST_SYNTHETIC_LOCAL_FIXTURE",
            is_fallback=True,
        )
