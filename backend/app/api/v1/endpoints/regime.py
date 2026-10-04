"""Weather Regime Intelligence API Endpoints for PS26080 (MoES / NCMRWF)."""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, Query, status

from backend.app.data.schemas.meteorology import CanonicalMeteorologicalRecord
from backend.app.data.sources.ncmrwf import NCMRWFAdapter
from backend.app.regime.regime_classifier import WeatherRegimeClassifier
from backend.app.regime.temporal_pipeline import TemporalRegimePipeline
from backend.app.schemas.common import Coordinates
from backend.app.schemas.regime import RegimeResponse, WeatherRegimeType
from backend.app.schemas.regime_temporal import (
    Day10RegimeForecastResponse,
    RegimeForecastMode,
    RegimePersistenceReport,
    RegimeSequence,
    RegimeTransitionExplanation,
    RegimeTransitionMatrix,
)
from backend.app.services.regime_service import WeatherRegimeService

logger = logging.getLogger("rainfall_backend.api.v1.regime")

router = APIRouter()


@router.get(
    "",
    response_model=RegimeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Weather Regime Classification",
    description="Retrieve real-time or simulated synoptic weather regime classification for target coordinates.",
)
@router.get(
    "/",
    response_model=RegimeResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_weather_regime(
    latitude: float = Query(default=19.0760, ge=-90.0, le=90.0, description="Target latitude (°N)"),
    longitude: float = Query(default=72.8777, ge=-180.0, le=180.0, description="Target longitude (°E)"),
    prediction_date: Optional[str] = Query(default=None, description="Target date (YYYY-MM-DD)"),
    location_name: Optional[str] = Query(default=None, description="Optional geographical location label"),
) -> RegimeResponse:
    """Diagnose weather regime and atmospheric drivers for target coordinates."""
    coords = Coordinates(latitude=latitude, longitude=longitude)
    service = WeatherRegimeService()
    target_month = 7
    if prediction_date:
        try:
            target_month = datetime.strptime(prediction_date, "%Y-%m-%d").month
        except Exception:
            target_month = 7

    return service.classify_regime(
        coordinates=coords,
        target_month=target_month,
        location_name=location_name,
    )


@router.post(
    "/classify",
    response_model=RegimeResponse,
    status_code=status.HTTP_200_OK,
    summary="Classify Meteorological Record Weather Regime",
    description="Ingest a canonical meteorological record and return full multi-label regime probabilities and grounded XAI drivers.",
)
async def classify_record_regime(
    record: CanonicalMeteorologicalRecord = Body(..., description="Canonical meteorological record with multi-level NWP parameters"),
) -> RegimeResponse:
    """Classify regime directly from a standardized meteorological record."""
    logger.info("Executing regime classification for source=%s at (%f, %f)", record.data_source, record.latitude, record.longitude)
    return WeatherRegimeClassifier.classify(record)


@router.get(
    "/sequence",
    response_model=RegimeSequence,
    status_code=status.HTTP_200_OK,
    summary="Temporal Weather Regime Sequence",
    description="Retrieve chronological multi-day regime state trajectory over a target date window.",
)
async def get_regime_sequence(
    start_date: str = Query(default="2024-07-01", description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(default="2024-07-07", description="End date (YYYY-MM-DD)"),
    latitude: float = Query(default=18.5204, description="Target latitude"),
    longitude: float = Query(default=73.8567, description="Target longitude"),
) -> RegimeSequence:
    """Extract temporal sequence of weather regimes."""
    coords = Coordinates(latitude=latitude, longitude=longitude)
    pipeline = TemporalRegimePipeline()
    return pipeline.get_regime_sequence(start_date=start_date, end_date=end_date, coordinates=coords)


@router.get(
    "/transitions",
    response_model=RegimeTransitionMatrix,
    status_code=status.HTTP_200_OK,
    summary="Markov Weather Regime Transition Matrix",
    description="Retrieve empirical 7x7 Markov transition probability matrix fitted on 10-year training partition.",
)
async def get_regime_transitions() -> RegimeTransitionMatrix:
    """Query empirical Markov regime transition matrix."""
    pipeline = TemporalRegimePipeline()
    return pipeline.get_transition_matrix()


@router.get(
    "/persistence",
    response_model=RegimePersistenceReport,
    status_code=status.HTTP_200_OK,
    summary="Regime Persistence & Duration Profile",
    description="Query empirical retention probabilities and mean/median durations across all 7 SASM regimes.",
)
async def get_regime_persistence() -> RegimePersistenceReport:
    """Query regime persistence and duration statistics."""
    pipeline = TemporalRegimePipeline()
    return pipeline.get_persistence_report()


@router.post(
    "/forecast",
    response_model=Day10RegimeForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Day 1–10 Temporal Regime Probability Projection",
    description="Project multi-day regime probability propagation using Markov transition operators.",
)
async def forecast_regime_day_1_10(
    current_regime: WeatherRegimeType = Body(default=WeatherRegimeType.ACTIVE_MONSOON, description="Current primary regime"),
    current_probabilities: Optional[Dict[str, float]] = Body(default=None, description="Optional current probability vector"),
    mode: RegimeForecastMode = Body(default=RegimeForecastMode.TRANSITION_BASED_PROJECTION, description="Forecasting mode"),
) -> Day10RegimeForecastResponse:
    """Project Day 1–10 regime evolution."""
    pipeline = TemporalRegimePipeline()
    return pipeline.forecast_day_1_10(
        current_regime=current_regime,
        current_probabilities=current_probabilities,
        mode=mode,
    )


@router.post(
    "/explain",
    response_model=RegimeTransitionExplanation,
    status_code=status.HTTP_200_OK,
    summary="Explainable Regime Transition Analysis",
    description="Synthesize physically grounded meteorological explanation and feature deltas for a regime shift.",
)
async def explain_regime_transition(
    from_regime: WeatherRegimeType = Body(default=WeatherRegimeType.ACTIVE_MONSOON, description="Originating regime"),
    to_regime: WeatherRegimeType = Body(default=WeatherRegimeType.OROGRAPHIC_RAINFALL, description="Destination regime"),
    initial_features: Optional[Dict[str, float]] = Body(default=None, description="Initial feature snapshot"),
    target_features: Optional[Dict[str, float]] = Body(default=None, description="Target feature snapshot"),
) -> RegimeTransitionExplanation:
    """Synthesize explanation for regime transition."""
    pipeline = TemporalRegimePipeline()
    return pipeline.explain_transition(
        from_regime=from_regime,
        to_regime=to_regime,
        initial_features=initial_features,
        target_features=target_features,
    )
