"""Weather Regime Intelligence API Endpoints for PS26080 (MoES / NCMRWF)."""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, Query, status

from backend.app.data.schemas.meteorology import CanonicalMeteorologicalRecord
from backend.app.data.sources.ncmrwf import NCMRWFAdapter
from backend.app.regime.regime_classifier import WeatherRegimeClassifier
from backend.app.schemas.common import Coordinates
from backend.app.schemas.regime import RegimeResponse
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
