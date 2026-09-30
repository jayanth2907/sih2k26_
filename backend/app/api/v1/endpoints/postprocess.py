"""AI Post-Processing API Endpoints for PS26080 (MoES / NCMRWF)."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Query, status

from backend.app.postprocessing.base import PostProcessingInput, PostProcessingOutput
from backend.app.postprocessing.comparison import ForecastComparisonSummary
from backend.app.postprocessing.inference import PostProcessingInferenceEngine
from backend.app.postprocessing.model_registry import ModelRegistryEntry, PostProcessingModelRegistry
from backend.app.schemas.postprocess import DistrictForecast, VerificationResponse

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
async def get_district_forecasts() -> List[DistrictForecast]:
    """Retrieve district-level post-processed rainfall products."""
    engine = PostProcessingInferenceEngine.get_instance()
    return engine.get_all_district_forecasts()


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
