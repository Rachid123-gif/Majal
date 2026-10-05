from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import health, territories
from app.settings import get_settings


def create_app() -> FastAPI:
    app = FastAPI(title="MAJAL API", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(territories.router)
    return app


app = create_app()
