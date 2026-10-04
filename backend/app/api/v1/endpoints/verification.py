"""
Advanced Verification, Calibration & Reliability API Endpoints (Phase 15).
Provides forensic scorecards across continuous, categorical, regime-stratified,
probabilistic calibration, spatial FSS, and historical case-study benchmarks.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query, status

from backend.app.postprocessing.advanced_verification_engine import AdvancedVerificationEngine
from backend.app.schemas.advanced_verification import (
    AdvancedVerificationSummary,
    CaseStudyVerificationEntry,
    ModelTradeOffEntry,
    ProbabilisticCalibrationReport,
    RegimeStratifiedEntry,
    ReliabilityBinData,
    SpatialFieldVerificationReport,
    TemporalRegimeVerificationReport,
    UncertaintyIntervalReport,
)

logger = logging.getLogger("rainfall_backend.api.v1.verification")

router = APIRouter()


@router.get(
    "/summary",
    response_model=AdvancedVerificationSummary,
    status_code=status.HTTP_200_OK,
    summary="Advanced Verification & Reliability Executive Summary",
    description="Retrieve complete comprehensive verification benchmark summary across all 6 models, regimes, and calibration metrics.",
)
async def get_advanced_verification_summary() -> AdvancedVerificationSummary:
    """Retrieve full advanced verification summary."""
    return AdvancedVerificationEngine.generate_advanced_verification_summary()


@router.get(
    "/trade-offs",
    response_model=List[ModelTradeOffEntry],
    status_code=status.HTTP_200_OK,
    summary="Multi-Model Verification Trade-Off Matrix",
    description="Compare models across continuous, categorical, spatial, and probabilistic metrics without universal scores or ranking.",
)
async def get_model_trade_offs() -> List[ModelTradeOffEntry]:
    """Retrieve multi-model trade-off matrix."""
    summary = AdvancedVerificationEngine.generate_advanced_verification_summary()
    return summary.model_trade_offs


@router.get(
    "/thresholds",
    response_model=List[ProbabilisticCalibrationReport],
    status_code=status.HTTP_200_OK,
    summary="Threshold-Specific Verification & Calibration",
    description="Retrieve calibration scores, Brier score, and BSS stratified across 64.5mm, 115.6mm, and 204.5mm.",
)
async def get_threshold_verification(
    threshold_mm: Optional[float] = Query(default=None, description="Optional threshold filter (64.5, 115.6, 204.5 mm)"),
) -> List[ProbabilisticCalibrationReport]:
    """Retrieve threshold-specific calibration reports."""
    summary = AdvancedVerificationEngine.generate_advanced_verification_summary()
    reports = summary.probabilistic_calibration
    if threshold_mm is not None:
        reports = [r for r in reports if abs(r.threshold_mm - threshold_mm) < 1.0]
    return reports


@router.get(
    "/regimes",
    response_model=List[RegimeStratifiedEntry],
    status_code=status.HTTP_200_OK,
    summary="Regime-Stratified & Multi-Label Verification",
    description="Retrieve continuous and categorical verification scores partitioned by primary synoptic weather regime.",
)
async def get_regime_verification(
    regime: Optional[str] = Query(default=None, description="Optional regime name filter"),
    multi_label_only: Optional[bool] = Query(default=False, description="Filter for multi-label regime subsets"),
) -> List[RegimeStratifiedEntry]:
    """Retrieve regime-stratified verification entries."""
    summary = AdvancedVerificationEngine.generate_advanced_verification_summary()
    entries = summary.regime_breakdown

    if regime:
        r_lower = regime.strip().lower()
        entries = [e for e in entries if r_lower in e.regime_name.lower()]

    if multi_label_only:
        entries = [e for e in entries if e.is_multi_label]

    return entries


@router.get(
    "/probabilistic",
    response_model=List[ProbabilisticCalibrationReport],
    status_code=status.HTTP_200_OK,
    summary="Probabilistic Heavy Rainfall Calibration Scores",
    description="Query Brier Score, Brier Skill Score (BSS), ECE, MCE, and sharpness distributions.",
)
async def get_probabilistic_calibration() -> List[ProbabilisticCalibrationReport]:
    """Query probabilistic calibration reports."""
    summary = AdvancedVerificationEngine.generate_advanced_verification_summary()
    return summary.probabilistic_calibration


@router.get(
    "/reliability",
    response_model=List[ReliabilityBinData],
    status_code=status.HTTP_200_OK,
    summary="10-Bin Reliability Diagram Data",
    description="Retrieve mean forecast probability vs observed event frequency across 10 probability bins.",
)
async def get_reliability_diagram_data(
    threshold_mm: float = Query(default=64.5, description="Rainfall threshold in mm"),
) -> List[ReliabilityBinData]:
    """Retrieve reliability diagram bin data."""
    summary = AdvancedVerificationEngine.generate_advanced_verification_summary()
    match = next(
        (r for r in summary.probabilistic_calibration if abs(r.threshold_mm - threshold_mm) < 1.0),
        summary.probabilistic_calibration[0],
    )
    return match.reliability_bins


@router.get(
    "/spatial",
    response_model=SpatialFieldVerificationReport,
    status_code=status.HTTP_200_OK,
    summary="2D Spatial Verification & Audited Multi-Scale FSS",
    description="Retrieve 2D pattern correlation, spatial gradient RMSE, and physical neighborhood geometry audited FSS.",
)
async def get_spatial_verification() -> SpatialFieldVerificationReport:
    """Retrieve spatial field verification diagnostics."""
    summary = AdvancedVerificationEngine.generate_advanced_verification_summary()
    return summary.spatial_diagnostics


@router.get(
    "/uncertainty",
    response_model=UncertaintyIntervalReport,
    status_code=status.HTTP_200_OK,
    summary="Uncertainty Quantile Interval Coverage & Reliability",
    description="Query empirical 80% quantile coverage ([P10, P90]), interval widths, and quantile crossing diagnostics.",
)
async def get_uncertainty_verification() -> UncertaintyIntervalReport:
    """Query uncertainty interval verification report."""
    summary = AdvancedVerificationEngine.generate_advanced_verification_summary()
    return summary.uncertainty_verification


@router.get(
    "/case-studies",
    response_model=List[CaseStudyVerificationEntry],
    status_code=status.HTTP_200_OK,
    summary="Historical Extreme-Event Case Study Benchmarks",
    description="Retrieve verification scores and peak precipitation comparisons for Kerala 2018, Mumbai 2005, and Biparjoy 2023.",
)
async def get_case_study_verification() -> List[CaseStudyVerificationEntry]:
    """Retrieve historical case study benchmarks."""
    summary = AdvancedVerificationEngine.generate_advanced_verification_summary()
    return summary.case_studies
