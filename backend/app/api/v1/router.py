from fastapi import APIRouter
from backend.app.api.v1.endpoints import data, health, models, postprocess, prediction, regime

api_v1_router = APIRouter()

# Register endpoint routers
api_v1_router.include_router(health.router, tags=["System Health"])
api_v1_router.include_router(models.router, prefix="/models", tags=["ML Model Inference"])
api_v1_router.include_router(prediction.router, prefix="/predict", tags=["Rainfall & Post-Processing Prediction"])
api_v1_router.include_router(regime.router, prefix="/regime", tags=["Weather Regime Intelligence"])
api_v1_router.include_router(postprocess.router, prefix="/postprocess", tags=["AI Post-Processing & Verification"])
api_v1_router.include_router(data.router, prefix="/data", tags=["Meteorological & Radar Feeds"])




