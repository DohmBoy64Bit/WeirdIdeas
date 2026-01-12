# backend/app/core.py
from fastapi import FastAPI

# Import application routers here so they are registered via `create_app()`
try:
    from .api import api_router
except Exception:
    api_router = None


def create_app():
    app = FastAPI()
    # Register routes here
    if api_router is not None:
        app.include_router(api_router)
    return app