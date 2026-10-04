"""
API Endpoints for Historical Extreme-Event Case Studies (Phase 9 - MoES / NCMRWF PS26080).
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Path, status

from backend.app.case_studies.registry import CaseStudyRegistry
from backend.app.case_studies.schemas import CaseStudyDetail, CaseStudySummary

logger = logging.getLogger("rainfall_backend.api.v1.case_studies")

router = APIRouter()


@router.get(
    "",
    response_model=List[CaseStudySummary],
    status_code=status.HTTP_200_OK,
    summary="List Historical Extreme-Event Case Studies",
    description="Retrieve catalog of registered historical monsoon rainfall case studies (Kerala 2018, Mumbai 2005, Cyclone Biparjoy 2023).",
)
async def list_case_studies() -> List[CaseStudySummary]:
    """List all registered historical case studies."""
    return CaseStudyRegistry.list_case_studies()


@router.get(
    "/{case_id}",
    response_model=CaseStudyDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Historical Case Study Detail",
    description="Retrieve complete meteorological case study profile, observations, 4-model forecast comparison, uncertainty quantiles, and provenance.",
)
async def get_case_study_detail(
    case_id: str = Path(..., description="Case study ID (e.g. 'KERALA_2018', 'MUMBAI_2005', 'BIPARJOY_2023')"),
) -> CaseStudyDetail:
    """Retrieve detailed case study by case_id."""
    detail = CaseStudyRegistry.get_case_study(case_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Historical case study '{case_id}' not found. Available cases: {list(CaseStudyRegistry._CASES.keys())}",
        )
    return detail
