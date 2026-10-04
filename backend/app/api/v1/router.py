from fastapi import APIRouter
from backend.app.api.v1.endpoints import case_studies, data, districts, health, models, operational, postprocess, prediction, regime, training, verification

api_v1_router = APIRouter()

# Register endpoint routers
api_v1_router.include_router(health.router, tags=["System Health"])
api_v1_router.include_router(models.router, prefix="/models", tags=["ML Model Inference"])
api_v1_router.include_router(prediction.router, prefix="/predict", tags=["Rainfall & Post-Processing Prediction"])
api_v1_router.include_router(regime.router, prefix="/regime", tags=["Weather Regime Intelligence"])
api_v1_router.include_router(postprocess.router, prefix="/postprocess", tags=["AI Post-Processing & Verification"])
api_v1_router.include_router(districts.router, prefix="/districts", tags=["District Decision Support & Warnings"])
api_v1_router.include_router(verification.router, prefix="/verification", tags=["Advanced Verification & Calibration"])
api_v1_router.include_router(operational.router, prefix="/operational", tags=["Operational Integration & NCMRWF Readiness"])
api_v1_router.include_router(data.router, prefix="/data", tags=["Meteorological & Radar Feeds"])
api_v1_router.include_router(case_studies.router, prefix="/case-studies", tags=["Historical Extreme-Event Case Studies"])
api_v1_router.include_router(training.router, tags=["Real Data Training & Model Registry"])





