from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import auth, health, territories
from app.settings import get_settings

INSECURE_SECRET = "dev-only-insecure-secret"


def create_app() -> FastAPI:
    settings = get_settings()
    if settings.app_env == "production" and settings.session_secret == INSECURE_SECRET:
        raise RuntimeError("SESSION_SECRET must be set to a long random value in production")
    app = FastAPI(title="MAJAL API", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(territories.router)
    app.include_router(auth.router)
    return app


app = create_app()
