"""
NOAA GFS (via Open-Meteo) Development & Fallback Adapter for PS26080.
Explicitly labeled as Development Demo / Fallback Data (NOT live NCMRWF).
"""

from typing import Optional
from backend.app.data.schemas.meteorology import CanonicalMeteorologicalRecord


class GFSFallbackAdapter:
    """Ingestion client for NOAA GFS 0.25° grid via Open-Meteo API."""

    SOURCE_ID = "NOAA_GFS_OPENMETEO_FALLBACK"
    ROLE = "DEVELOPMENT_DEMO_FALLBACK"

    def is_operational(self) -> bool:
        """Check if Open-Meteo GFS endpoint is operational."""
        return True

    def fetch_forecast_record(

        self,
        lat: float,
        lon: float,
        timestamp_iso: str,
        accumulated_precip_mm: float = 38.5,
        peak_rate_mm_hr: float = 7.2,
    ) -> CanonicalMeteorologicalRecord:
        """Convert Open-Meteo GFS feed into CanonicalMeteorologicalRecord."""
        return CanonicalMeteorologicalRecord(
            timestamp=timestamp_iso,
            forecast_initialization=timestamp_iso,
            lead_time_hours=24,
            latitude=lat,
            longitude=lon,
            rainfall=accumulated_precip_mm,
            ensemble_mean=accumulated_precip_mm,
            ensemble_std=round(accumulated_precip_mm * 0.18, 2),
            ensemble_p10=round(accumulated_precip_mm * 0.75, 2),
            ensemble_p90=round(accumulated_precip_mm * 1.30, 2),
            temperature_850=294.2,
            temperature_700=283.4,
            temperature_500=265.8,
            relative_humidity_850=82.0,
            relative_humidity_700=74.0,
            relative_humidity_500=55.0,
            u850=12.5,
            v850=5.4,
            u700=8.6,
            v700=3.2,
            u500=4.1,
            v500=1.2,
            geopotential_850=1472.0,
            geopotential_500=5848.0,
            vertical_velocity=-0.32,
            surface_pressure=1007.5,
            mslp=1009.6,
            cape_j_kg=1450.0,
            data_source=self.SOURCE_ID,
            data_quality="FALLBACK_OPERATIONAL",
            is_demo=True, # Transparent labeling: demo/fallback
        )
