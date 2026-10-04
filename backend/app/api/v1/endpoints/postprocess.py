"""AI Post-Processing API Endpoints for PS26080 (MoES / NCMRWF)."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Query, status

from backend.app.postprocessing.base import PostProcessingInput, PostProcessingOutput
from backend.app.postprocessing.comparison import ForecastComparisonSummary
from backend.app.postprocessing.inference import PostProcessingInferenceEngine
from backend.app.postprocessing.model_registry import ModelRegistryEntry, PostProcessingModelRegistry
from backend.app.schemas.postprocess import DistrictForecast, VerificationResponse
from backend.app.schemas.spatial_postprocess import (
    SpatialPredictionOutput,
    SpatialRainfallSample,
    SpatialStatusResponse,
    SpatialVerificationSummary,
)

logger = logging.getLogger("rainfall_backend.api.v1.postprocess")

router = APIRouter()


@router.get(
    "/models",
    response_model=List[ModelRegistryEntry],
    status_code=status.HTTP_200_OK,
    summary="List Registered Post-Processing Models",
    description="Catalog of all 4 forecasting/post-processing models (Raw NWP, EQM, Global ML, Regime-Aware ML).",
)
async def get_registered_models() -> List[ModelRegistryEntry]:
    """Retrieve all models from the post-processing model registry."""
    return PostProcessingModelRegistry.get_all_models()


@router.post(
    "/correct",
    response_model=PostProcessingOutput,
    status_code=status.HTTP_200_OK,
    summary="Apply AI Forecast Correction",
    description="Execute residual error correction using selected model (Raw NWP, EQM, Global ML, or Regime-Aware ML).",
)
async def correct_nwp_forecast(
    sample: PostProcessingInput = Body(..., description="Forecast payload with NWP, atmospheric, and regime features"),
    model_id: str = Query(default="regime_aware_ml", description="'raw_nwp', 'quantile_mapping', 'global_ml', or 'regime_aware_ml'"),
) -> PostProcessingOutput:
    """Run model forecast error correction."""
    engine = PostProcessingInferenceEngine.get_instance()
    return engine.correct_forecast(sample, model_id=model_id)


@router.post(
    "/compare",
    response_model=ForecastComparisonSummary,
    status_code=status.HTTP_200_OK,
    summary="Compare 4 Post-Processing Models",
    description="Evaluate and compare Raw NWP, Empirical Quantile Mapping, Global ML, and Regime-Aware ML.",
)
async def compare_all_models(
    sample: PostProcessingInput = Body(..., description="Forecast payload for 4-product benchmark"),
) -> ForecastComparisonSummary:
    """Run concurrent 4-product model comparison."""
    engine = PostProcessingInferenceEngine.get_instance()
    return engine.compare_all(sample)


@router.get(
    "/compare",
    response_model=ForecastComparisonSummary,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def compare_all_models_get(
    raw_rainfall_mm: float = Query(default=40.0, ge=0.0),
    latitude: float = Query(default=19.0760, ge=-90.0, le=90.0),
    longitude: float = Query(default=72.8777, ge=-180.0, le=180.0),
    lead_time_hours: int = Query(default=24, ge=0),
    month: int = Query(default=7, ge=1, le=12),
) -> ForecastComparisonSummary:
    """Convenience GET route for 4-model comparison."""
    engine = PostProcessingInferenceEngine.get_instance()
    sample = PostProcessingInput(
        raw_nwp_rainfall=raw_rainfall_mm,
        lead_time_hours=lead_time_hours,
        latitude=latitude,
        longitude=longitude,
        month=month,
        day_of_year=200,
    )
    return engine.compare_all(sample)


@router.get(
    "/districts",
    response_model=List[DistrictForecast],
    status_code=status.HTTP_200_OK,
    summary="District-Level Post-Processed Monsoon Forecasts",
    description="Retrieve standardized district-level rainfall forecasts, regime conditioning, and uncertainty across administrative districts.",
)
async def get_district_forecasts(
    state: Optional[str] = Query(default=None, description="Filter by state / UT name (e.g. 'Maharashtra')"),
    regime: Optional[str] = Query(default=None, description="Filter by dominant regime (e.g. 'OROGRAPHIC_RAINFALL')"),
    category: Optional[str] = Query(default=None, description="Filter by decision support category (e.g. 'HEAVY_RAINFALL')"),
) -> List[DistrictForecast]:
    """Retrieve district-level post-processed rainfall products."""
    engine = PostProcessingInferenceEngine.get_instance()
    return engine.get_all_district_forecasts(
        state_filter=state,
        regime_filter=regime,
        category_filter=category,
    )



@router.get(
    "/verification",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Post-Processing Verification Benchmarks",
    description="Retrieve spatial and categorical verification metrics (RMSE, ETS, CSI, POD, FAR, FSS) on held-out test dataset.",
)
async def get_verification_benchmarks(
    regime: Optional[str] = Query(default=None, description="Optional regime filter (e.g. 'ACTIVE_MONSOON', 'OROGRAPHIC_RAINFALL')"),
    threshold_mm: float = Query(default=64.5, description="Rainfall threshold limit (64.5, 115.6, 204.5 mm)"),
) -> VerificationResponse:
    """Query prospective verification benchmarks."""
    engine = PostProcessingInferenceEngine.get_instance()
    return engine.get_verification_benchmarks(regime_filter=regime, threshold_mm=threshold_mm)


# ==========================================
# Phase 13 — Spatial Post-Processing Endpoints
# ==========================================

@router.post(
    "/spatial",
    response_model=SpatialPredictionOutput,
    status_code=status.HTTP_200_OK,
    summary="Apply 2D Spatial AI Post-Processing",
    description="Execute spatially coherent 2D residual error correction, spatial quantiles (P10/P50/P90), and exceedance probability fields.",
)
async def postprocess_spatial_grid(
    sample: Optional[SpatialRainfallSample] = Body(default=None, description="2D meteorological grid sample payload"),
    model_id: str = Query(default="SPATIAL_REGIME_AWARE_V1", description="'SPATIAL_RESIDUAL_BASELINE_V1', 'SPATIAL_REGIME_AWARE_V1', or 'SPATIAL_REGIME_TEMPORAL_V1'"),
) -> SpatialPredictionOutput:
    """Execute 2D spatial rainfall post-processing."""
    from backend.app.postprocessing.spatial_pipeline import SpatialPostProcessingPipeline
    pipeline = SpatialPostProcessingPipeline.get_instance()
    if sample is None:
        sample = pipeline.generate_demo_sample(patch_size=16)
    return pipeline.execute_spatial_postprocessing(sample, model_id=model_id)


@router.get(
    "/spatial/status",
    response_model=SpatialStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Spatial Post-Processing Operational Status",
    description="Retrieve spatial target grid parameters, registered models, and data availability status.",
)
async def get_spatial_status() -> SpatialStatusResponse:
    """Query spatial engine status."""
    from backend.app.postprocessing.spatial_pipeline import SpatialPostProcessingPipeline
    return SpatialPostProcessingPipeline.get_instance().get_operational_status()


@router.get(
    "/spatial/models",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="List Registered Spatial Models",
    description="Retrieve list of registered 2D spatial meteorological post-processing models.",
)
async def get_spatial_models() -> List[str]:
    """List 2D spatial models."""
    from backend.app.postprocessing.spatial_pipeline import SpatialPostProcessingPipeline
    return SpatialPostProcessingPipeline.get_instance().registered_models


@router.get(
    "/spatial/verification",
    response_model=SpatialVerificationSummary,
    status_code=status.HTTP_200_OK,
    summary="Spatial Post-Processing Verification Summary",
    description="Retrieve multi-scale Fractions Skill Score (25km, 50km, 100km), pattern correlation, and gradient RMSE on held-out grids.",
)
async def get_spatial_verification(
    model_id: str = Query(default="SPATIAL_REGIME_AWARE_V1", description="Spatial model identifier"),
    threshold_mm: float = Query(default=64.5, description="Heavy rainfall threshold in mm"),
) -> SpatialVerificationSummary:
    """Retrieve spatial verification benchmark."""
    from backend.app.postprocessing.spatial_pipeline import SpatialPostProcessingPipeline
    from backend.app.postprocessing.spatial_verification import SpatialVerificationEngine
    pipeline = SpatialPostProcessingPipeline.get_instance()
    
    # Evaluate over representative deterministic evaluation test batch
    test_samples = [pipeline.generate_demo_sample(patch_size=16, dominant_regime=r) for r in ["ACTIVE_MONSOON", "OROGRAPHIC_RAINFALL", "MONSOON_LOW_LPS", "BREAK_MONSOON"]]
    preds = [pipeline.execute_spatial_postprocessing(s, model_id=model_id).corrected_grid for s in test_samples]
    obs = [s.observed_grid for s in test_samples]
    
    import numpy as np
    f_grids = [np.array(p) for p in preds]
    o_grids = [np.array(o) for o in obs]
    
    return SpatialVerificationEngine.evaluate_spatial_model(
        model_id=model_id,
        model_name="Spatial Regime-Aware Post-Processing Model (Phase 13)",
        forecast_grids=f_grids,
        observed_grids=o_grids,
        threshold_mm=threshold_mm,
    )

