from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.utils.logger import logger

from contextlib import asynccontextmanager
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        f"Starting {settings.PROJECT_NAME} "
        f"v{settings.VERSION} "
        f"[{settings.ENVIRONMENT}]"
    )

    init_db()

    logger.info("Database schema initialized and verified.")

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME}")


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "AI-Powered Pharmaceutical Smart Manufacturing, "
            "Production Scheduling, Predictive Maintenance "
            "and Factory Optimization Platform"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # ============================================================
    # CORS CONFIGURATION
    # ============================================================

    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                str(origin) for origin in settings.CORS_ORIGINS
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # ============================================================
    # ROOT ROUTE
    # ============================================================

    @app.get("/")
    async def root():
        return {
            "message": "NexPharmAI API is running",
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "docs": "/docs",
            "redoc": "/redoc",
            "api": settings.API_V1_STR,
            "status": "online",
        }

    # ============================================================
    # API V1 ROUTES
    # ============================================================

    app.include_router(
        api_router,
        prefix=settings.API_V1_STR
    )

    return app


# ================================================================
# CREATE APPLICATION
# ================================================================

app = create_application()


# ================================================================
# RUN DIRECTLY
# ================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )