"""
SafeGround — FastAPI application factory.
Zero-identity community safety platform.
"""
import os
import logging

from fastapi import FastAPI
from dotenv import load_dotenv, find_dotenv
from fastapi.middleware.cors import CORSMiddleware

from api.feedback.router import router as feedback_router
from api.incidents.router import router as incidents_router
from api.resources.router import router as resources_router
from api.scout.router import router as scout_router
from infrastructure.config.container import Container
from infrastructure.middleware.privacy import PrivacyMiddleware

logging.basicConfig(level=logging.INFO)
from utils.logger import get_logger

logger = get_logger()

from utils.logger import get_logger

logger = get_logger()

#  Load .env and pick the right Settings class
load_dotenv(find_dotenv())
FASTAPI_ENV = os.getenv("APP_ENV", "development").lower()

# API root used when FastAPI is behind a reverse proxy such as Nginx.
# Empty/missing value means the API is served from "/".
API_ROOT = os.getenv("API_ROOT", "").strip().rstrip("/")

# Ensure root_path is either "" or starts with "/"
if API_ROOT and not API_ROOT.startswith("/"):
    API_ROOT = f"/{API_ROOT}"


def create_app() -> FastAPI:
    container = Container()
    container.wire(
        modules=[
            "api.incidents.router",
            "api.scout.router",
            "api.resources.router",
            "api.feedback.router",
        ]
    )

    app = FastAPI(
        title="SafeGround API",
        description="Community safety intelligence — zero identity, zero tracking.",
        version="0.1.0",
        root_path=API_ROOT,
        docs_url="/api/v1/docs",
    )

    # Privacy middleware FIRST — before anything else touches the request
    app.add_middleware(PrivacyMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten for production
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(incidents_router, prefix="/api/v1")
    app.include_router(scout_router, prefix="/api/v1")
    app.include_router(resources_router, prefix="/api/v1")
    app.include_router(feedback_router, prefix="/api/v1")

    app.container = container

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "safeground"}

    return app


app = create_app()


# Uvicorn entrypoint
if __name__ == "__main__":
    import uvicorn
    logger.info("About to start API")
    is_dev = FASTAPI_ENV == "development"

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        # port=int(settings.PORT),
        port=8000,
        reload=(FASTAPI_ENV == "development"),
        # log_level=settings.LOG_LEVEL.lower(),
        workers=None if is_dev else 2,   # use 2 workers in non-dev
    )
