"""Prediction & Regime-Aware Forecast Post-Processing API endpoints for PS26080."""

from datetime import datetime
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.core.errors import WeatherObservationValidationError
from backend.app.schemas.common import Coordinates
from backend.app.schemas.postprocess import (
    PostProcessingComparison,
    VerificationResponse,
)
from backend.app.schemas.prediction import (
    InundationPipelineRequest,
    InundationPipelineResponse,
    RainfallPipelineRequest,
    RainfallPipelineResponse,
)
from backend.app.schemas.regime import RegimeResponse
from backend.app.schemas.risk import (
    RiskAssessmentRequest,
    RiskAssessmentResponse,
)
from backend.app.schemas.unified import (
    UnifiedPredictionRequest,
    UnifiedPredictionResponse,
)
from backend.app.schemas.warning import (
    WarningAssessmentRequest,
    WarningDecisionResponse,
)
from backend.app.services.postprocessing_service import PostProcessingService
from backend.app.services.regime_service import WeatherRegimeService
from backend.app.services.risk_assessment_service import RiskAssessmentService
from backend.app.services.unified_prediction_service import UnifiedPredictionService
from backend.app.services.warning_service import WarningService
from backend.app.services.weather_service import WeatherObservationService

logger = logging.getLogger("rainfall_backend.api.v1.prediction")

router = APIRouter()


@router.post(
    "/regime",
    response_model=RegimeResponse,
    status_code=status.HTTP_200_OK,
    summary="Hierarchical Weather Regime Classification",
    description="Diagnose synoptic weather regimes (Active, Break, Monsoon Low, Coastal, Orographic) for target coordinates.",
)
async def classify_weather_regime(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    prediction_date: Optional[str] = Query(None),
    location_name: Optional[str] = Query(None),
) -> RegimeResponse:
    coords = Coordinates(latitude=latitude, longitude=longitude)
    month = 7
    if prediction_date:
        try:
            month = datetime.strptime(prediction_date, "%Y-%m-%d").month
        except Exception:
            month = 7

    service = WeatherRegimeService()
    return service.classify_regime(
        coordinates=coords,
        target_month=month,
        location_name=location_name,
    )


@router.get(
    "/verification",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Post-Processing Verification Benchmarks",
    description="Spatial skill benchmarks (RMSE, ETS, CSI, POD, FAR, FSS) comparing Raw NWP, EQM, Global ML, and Regime-Aware ML.",
)
async def get_verification_benchmarks() -> VerificationResponse:
    service = PostProcessingService()
    coords = Coordinates(latitude=19.0760, longitude=72.8777)
    regime = WeatherRegimeService().classify_regime(coords)
    _, _, _, verification = service.generate_products(
        raw_nwp_accumulated_mm=40.0,
        raw_peak_hourly_rate=8.0,
        raw_hourly_series=[2.0] * 24,
        regime=regime,
        coordinates=coords,
    )
    return verification


@router.post(
    "/rainfall",
    response_model=RainfallPipelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Real Next-Day Heavy Rainfall Prediction Pipeline",
    description=(
        "Fetch real meteorological observations from NASA POWER Daily API for the past 30+ days, "
        "construct the exact 37 Model 1 features without future leakage, and infer heavy rainfall "
        "probability using the trained XGBoost model."
    ),
)
async def predict_rainfall_pipeline(request: RainfallPipelineRequest) -> RainfallPipelineResponse:
    try:
        parsed_date = datetime.strptime(request.prediction_date, "%Y-%m-%d").date()
    except ValueError as err:
        raise WeatherObservationValidationError(
            f"Invalid prediction_date format: '{request.prediction_date}'. Expected 'YYYY-MM-DD'."
        ) from err

    coords = Coordinates(latitude=request.latitude, longitude=request.longitude)
    logger.info("Initiating rainfall prediction pipeline for (%f, %f) on date %s", coords.latitude, coords.longitude, parsed_date)
    weather_service = WeatherObservationService()
    return await weather_service.predict_rainfall(
        coordinates=coords,
        prediction_date=parsed_date,
        location_name=request.location_name,
    )


@router.post(
    "/inundation",
    response_model=InundationPipelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Sentinel-2 Inundation Pipeline (Backward Compatibility)",
)
async def predict_inundation_pipeline(request: InundationPipelineRequest) -> InundationPipelineResponse:
    from backend.app.services.satellite_imagery_service import SatelliteImageryService

    parsed_date = None
    if request.date:
        try:
            parsed_date = datetime.strptime(request.date, "%Y-%m-%d").date()
        except ValueError as err:
            raise WeatherObservationValidationError(f"Invalid date format: '{request.date}'. Expected 'YYYY-MM-DD'.") from err

    satellite_service = SatelliteImageryService()
    return await satellite_service.predict_inundation(
        latitude=request.latitude,
        longitude=request.longitude,
        target_date=parsed_date,
        max_cloud_percentage=request.max_cloud_percentage,
        min_polygon_area_sq_m=request.min_polygon_area_sq_m,
        location_name=request.location_name,
    )


@router.post(
    "/risk",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Multi-Source Risk Assessment & Fusion",
)
async def assess_multi_source_risk(request: RiskAssessmentRequest) -> RiskAssessmentResponse:
    parsed_date = None
    if request.prediction_date:
        try:
            parsed_date = datetime.strptime(request.prediction_date, "%Y-%m-%d").date()
        except ValueError as err:
            raise WeatherObservationValidationError(f"Invalid prediction_date format: '{request.prediction_date}'. Expected 'YYYY-MM-DD'.") from err

    risk_service = RiskAssessmentService()
    return await risk_service.assess_risk(
        latitude=request.latitude,
        longitude=request.longitude,
        prediction_date=parsed_date,
        nwp_horizon_hours=request.nwp_horizon_hours or 24,
        satellite_max_cloud=request.satellite_max_cloud if request.satellite_max_cloud is not None else 25.0,
        location_name=request.location_name,
    )


@router.post(
    "/warning",
    response_model=WarningDecisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Deterministic Severe Weather Warning Decision",
)
async def evaluate_warning_decision(request: WarningAssessmentRequest) -> WarningDecisionResponse:
    parsed_date = None
    if request.prediction_date:
        try:
            parsed_date = datetime.strptime(request.prediction_date, "%Y-%m-%d").date()
        except ValueError as err:
            raise WeatherObservationValidationError(f"Invalid prediction_date format: '{request.prediction_date}'. Expected 'YYYY-MM-DD'.") from err

    risk_service = RiskAssessmentService()
    risk_response = await risk_service.assess_risk(
        latitude=request.latitude,
        longitude=request.longitude,
        prediction_date=parsed_date,
        nwp_horizon_hours=request.nwp_horizon_hours or 24,
        satellite_max_cloud=request.satellite_max_cloud if request.satellite_max_cloud is not None else 25.0,
        location_name=request.location_name,
    )

    warning_service = WarningService()
    return warning_service.evaluate_warning(risk_response)


@router.post(
    "",
    response_model=UnifiedPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Unified Regime-Aware Monsoon Forecast & Post-Processing Pipeline",
    description=(
        "Unified orchestrator endpoint for PS26080 (MoES / NCMRWF). Concurrently collects observational "
        "and numerical atmospheric fields, identifies the active synoptic weather regime, executes 4-product "
        "post-processing (Raw NWP vs EQM vs Global ML vs Regime-Aware ML), computes heavy rainfall probabilities, "
        "district aggregations, spatial skill benchmarks, and GeoJSON precipitation isohyets for 3D visualization."
    ),
)
@router.post(
    "/",
    response_model=UnifiedPredictionResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def unified_prediction_pipeline(request: UnifiedPredictionRequest) -> UnifiedPredictionResponse:
    logger.info("Serving unified prediction request for (%f, %f)", request.latitude, request.longitude)
    unified_service = UnifiedPredictionService()
    return await unified_service.predict(request)
