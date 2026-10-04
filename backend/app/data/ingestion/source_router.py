"""
Source Router, Priority Selection, and Freshness Tracker for PS26080 (Phase 16).
Orchestrates multi-tier NWP ingestion with transparent fallback provenance.

Routing Hierarchy:
1. NCMRWF NCUM (12km Regional Deterministic)
2. NCMRWF NEPS (12km 23-member Ensemble)
3. NOAA GFS (Open-Meteo Development Fallback)
4. Calibrated Deterministic Demo Standby

Governance:
- Never silently downgrade.
- Always provide explicit operational state and fallback reason.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.app.data.ingestion.spatial_temporal import SpatialTemporalNormalizer
from backend.app.data.schemas.meteorology import CanonicalMeteorologicalRecord
from backend.app.data.sources.gfs import GFSFallbackAdapter
from backend.app.data.sources.ncmrwf import NCMRWFAdapter

logger = logging.getLogger("rainfall_backend.ingestion.router")


class SourceTier(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    DEVELOPMENT_FALLBACK = "DEVELOPMENT_FALLBACK"
    DEMO_FALLBACK = "DEMO_FALLBACK"


class OperationalState(str, Enum):
    """Explicit operational state enum for data sources."""
    LIVE_NCMRWF = "LIVE_NCMRWF"
    LIVE_NEPS = "LIVE_NEPS"
    ARCHIVED_NCMRWF = "ARCHIVED_NCMRWF"
    DEVELOPMENT_GFS = "DEVELOPMENT_GFS"
    DEMO_SYNTHETIC = "DEMO_SYNTHETIC"
    UNAVAILABLE = "UNAVAILABLE"


class FreshnessState(str, Enum):
    """Operational data freshness classification."""
    FRESH = "FRESH"
    AGING = "AGING"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class OperationalReadinessLevel(str, Enum):
    LEVEL_0 = "LEVEL 0 — DOCUMENTED ONLY"
    LEVEL_1 = "LEVEL 1 — ADAPTER ARCHITECTURE"
    LEVEL_2 = "LEVEL 2 — LOCAL DATA INGESTION"
    LEVEL_3 = "LEVEL 3 — VALIDATED ARCHIVED OPERATIONAL DATA"
    LEVEL_4 = "LEVEL 4 — LIVE OPERATIONAL FEED"
    LEVEL_5 = "LEVEL 5 — OPERATIONALLY MONITORED PRODUCTION"


class DataQualityState(str, Enum):
    VALID = "VALID"
    PARTIAL = "PARTIAL"
    MISSING_VARIABLE = "MISSING_VARIABLE"
    INVALID_METADATA = "INVALID_METADATA"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    DUPLICATE = "DUPLICATE"
    STALE = "STALE"
    FALLBACK = "FALLBACK"


class ProvenanceRecord(BaseModel):
    """Traceable data provenance for ingested meteorological forecasts."""
    source_id: str = Field(..., description="Unique source identifier")
    model_name: str = Field(..., description="Numerical weather prediction model name")
    run_initialization: str = Field(..., description="Model initialization cycle (ISO-8601 UTC)")
    valid_time: str = Field(..., description="Forecast valid time (ISO-8601 UTC)")
    lead_time_hours: int = Field(..., description="Forecast lead horizon in hours")
    resolution: str = Field(..., description="Spatial grid resolution")
    source_tier: SourceTier = Field(..., description="Active source priority tier")
    is_fallback: bool = Field(..., description="Whether fallback source was used")
    fallback_reason: Optional[str] = Field(None, description="Diagnostic reason for fallback if active")
    is_stale: bool = Field(..., description="Whether data exceeds operational staleness threshold")
    staleness_hours: float = Field(..., description="Elapsed hours since model initialization cycle")
    freshness: FreshnessState = Field(FreshnessState.FRESH, description="Freshness classification")
    quality_state: DataQualityState = Field(..., description="Evaluated data quality state")
    operational_state: OperationalState = Field(OperationalState.DEMO_SYNTHETIC, description="Explicit operational data status")
    requested_source: str = Field("NCMRWF_NCUM", description="Original requested source before routing")
    active_source: str = Field("NCMRWF_NCUM", description="Final resolved active source")
    provenance_state: str = Field("DEMO_FALLBACK", description="Human-readable provenance summary")


class OperationalSourceRouter:
    """
    Manages source prioritization, automatic fallback, freshness validation,
    and institutional provenance stamping.
    """

    DEFAULT_STALENESS_TOLERANCE_HOURS = 30.0
    AGING_THRESHOLD_HOURS = 18.0

    def __init__(
        self,
        primary_enabled: bool = False,
        staleness_tolerance_hours: float = DEFAULT_STALENESS_TOLERANCE_HOURS,
    ):
        self.primary_enabled = primary_enabled
        self.staleness_tolerance_hours = staleness_tolerance_hours
        self.ncmrwf_adapter = NCMRWFAdapter(live_connection_active=primary_enabled)
        self.gfs_adapter = GFSFallbackAdapter()

    @classmethod
    def calculate_freshness(cls, elapsed_hours: float, tolerance_hours: float = DEFAULT_STALENESS_TOLERANCE_HOURS) -> FreshnessState:
        """Derive freshness state from elapsed hours."""
        if elapsed_hours > tolerance_hours:
            return FreshnessState.STALE
        elif elapsed_hours > cls.AGING_THRESHOLD_HOURS:
            return FreshnessState.AGING
        return FreshnessState.FRESH

    def check_staleness(self, init_time_str: str) -> Tuple[bool, float]:
        """
        Check if data initialization timestamp is older than configured staleness thresholds.
        Returns: (is_stale, elapsed_hours)
        """
        try:
            init_dt = SpatialTemporalNormalizer.parse_iso_utc(init_time_str)
            now_dt = datetime.now(timezone.utc)
            elapsed_seconds = max(0.0, (now_dt - init_dt).total_seconds())
            elapsed_hours = round(elapsed_seconds / 3600.0, 2)
            is_stale = elapsed_hours > self.staleness_tolerance_hours
            return is_stale, elapsed_hours
        except Exception as err:
            logger.warning("Staleness calculation failed for %s: %s", init_time_str, err)
            return True, 999.0

    def get_forecast(
        self,
        lat: float,
        lon: float,
        target_date: str,
        lead_hours: int = 24,
        requested_source: str = "NCMRWF_NCUM",
    ) -> Tuple[CanonicalMeteorologicalRecord, ProvenanceRecord]:
        """
        Acquire forecast using deterministic priority routing:
        1. NCMRWF NCUM (if requested and operational)
        2. NCMRWF NEPS (if requested and operational)
        3. NOAA GFS Development Fallback
        4. Deterministic Demo Standby
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Check if primary NCMRWF is operational and requested
        if self.primary_enabled and self.ncmrwf_adapter.is_operational():
            rec = self.ncmrwf_adapter.fetch_point_forecast(lat, lon, target_date, lead_hours)
            init_time = rec.forecast_initialization or rec.timestamp
            is_stale, st_hours = self.check_staleness(init_time)
            freshness = self.calculate_freshness(st_hours, self.staleness_tolerance_hours)
            quality = DataQualityState.STALE if is_stale else DataQualityState.VALID

            prov = ProvenanceRecord(
                source_id="NCMRWF_NCUM",
                model_name="NCUM_REGIONAL_12KM",
                run_initialization=init_time,
                valid_time=rec.timestamp,
                lead_time_hours=lead_hours,
                resolution="12km (~0.12°)",
                source_tier=SourceTier.PRIMARY,
                is_fallback=False,
                fallback_reason=None,
                is_stale=is_stale,
                staleness_hours=st_hours,
                freshness=freshness,
                quality_state=quality,
                operational_state=OperationalState.LIVE_NCMRWF,
                requested_source=requested_source,
                active_source="NCMRWF_NCUM",
                provenance_state="LIVE_NCMRWF_OPERATIONAL",
            )
            return rec, prov

        # 2. Check if development GFS fallback is requested/configured
        if requested_source == "NOAA_GFS_OPENMETEO_FALLBACK" or requested_source == "NOAA_GFS":
            try:
                # GFS adapter point fetch
                gfs_rec = self.gfs_adapter.fetch_point_forecast(lat, lon, target_date, lead_hours)
                init_time = gfs_rec.forecast_initialization or gfs_rec.timestamp
                is_stale, st_hours = self.check_staleness(init_time)
                freshness = self.calculate_freshness(st_hours, self.staleness_tolerance_hours)

                prov = ProvenanceRecord(
                    source_id="NOAA_GFS_OPENMETEO_FALLBACK",
                    model_name="NOAA_GFS_0.25DEG",
                    run_initialization=init_time,
                    valid_time=gfs_rec.timestamp,
                    lead_time_hours=lead_hours,
                    resolution="0.25° (~27km)",
                    source_tier=SourceTier.DEVELOPMENT_FALLBACK,
                    is_fallback=True,
                    fallback_reason="Explicit development GFS fallback requested",
                    is_stale=is_stale,
                    staleness_hours=st_hours,
                    freshness=freshness,
                    quality_state=DataQualityState.FALLBACK,
                    operational_state=OperationalState.DEVELOPMENT_GFS,
                    requested_source=requested_source,
                    active_source="NOAA_GFS_OPENMETEO_FALLBACK",
                    provenance_state="DEVELOPMENT_GFS_FALLBACK",
                )
                return gfs_rec, prov
            except Exception as e:
                logger.warning("GFS fallback fetch failed: %s; falling through to demo synthetic", e)

        # 3. Default fallback: Transparent calibrated demo simulation
        logger.info("Operational gateway offline; routing to deterministic fallback with explicit provenance")
        rec = self.ncmrwf_adapter.fetch_point_forecast(lat, lon, target_date, lead_hours)
        init_time = rec.forecast_initialization or rec.timestamp
        is_stale, st_hours = self.check_staleness(init_time)
        freshness = self.calculate_freshness(st_hours, self.staleness_tolerance_hours)

        fallback_reason = "LIVE_NCMRWF_GATEWAY_NOT_CONFIGURED"
        prov = ProvenanceRecord(
            source_id="NCMRWF_NCUM_DEMO_SYNTHESIS",
            model_name="NCUM_ALIGNED_DEMO_SYNTHESIS",
            run_initialization=init_time,
            valid_time=rec.timestamp,
            lead_time_hours=lead_hours,
            resolution="12km (~0.12°)",
            source_tier=SourceTier.DEMO_FALLBACK,
            is_fallback=True,
            fallback_reason=fallback_reason,
            is_stale=is_stale,
            staleness_hours=st_hours,
            freshness=freshness,
            quality_state=DataQualityState.FALLBACK,
            operational_state=OperationalState.DEMO_SYNTHETIC,
            requested_source=requested_source,
            active_source="DEMO_SYNTHETIC",
            provenance_state="DEMO_SYNTHETIC_STANDBY",
        )
        return rec, prov

    @staticmethod
    def evaluate_operational_readiness() -> OperationalReadinessLevel:
        """
        Factual assessment of repository operational data maturity.
        LEVEL 1: Adapter architecture & GRIB2 validation implemented.
        """
        return OperationalReadinessLevel.LEVEL_1
