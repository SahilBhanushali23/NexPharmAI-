from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    users,
    machines,
    readings,
    predictive_maintenance,
    anomaly,
    alerts,
    maintenance,
    products,
    inventory,
    production,
    scheduler,
    quality,
    forecasting,
    analytics,
    assistant
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health & System"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users & Access Control"])
api_router.include_router(machines.router, prefix="/machines", tags=["Machine Management"])
api_router.include_router(readings.router, prefix="/readings", tags=["Sensor Readings & Telemetry"])
api_router.include_router(predictive_maintenance.router, prefix="/predictive-maintenance", tags=["Predictive Maintenance ML"])
api_router.include_router(anomaly.router, prefix="/anomaly-detection", tags=["Anomaly Detection ML"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alert Center"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance Management"])
api_router.include_router(products.router, prefix="/products", tags=["Pharmaceutical Products"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory Management"])
api_router.include_router(production.router, prefix="/production", tags=["Production Management"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["AI Production Scheduler & Rescheduling"])
api_router.include_router(quality.router, prefix="/quality", tags=["Batch Quality Prediction"])
api_router.include_router(forecasting.router, prefix="/forecasting", tags=["Demand Forecasting"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Production Analytics & OEE"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["AI Decision Assistant"])



