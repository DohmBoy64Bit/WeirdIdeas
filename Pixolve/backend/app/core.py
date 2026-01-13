# backend/app/core.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Import application routers here so they are registered via `create_app()`
try:
    from .api import api_router
except Exception:
    api_router = None


def create_app():
    app = FastAPI()
    
    # Add CORS middleware to allow frontend requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Serve static files (category images)
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    if os.path.exists(data_dir):
        app.mount("/data", StaticFiles(directory=data_dir), name="data")
    
    # Register routes here
    if api_router is not None:
        app.include_router(api_router)
    return app