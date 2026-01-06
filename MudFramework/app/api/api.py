from fastapi import APIRouter
from app.api.endpoints import auth, players, races

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(players.router, prefix="/players", tags=["players"])
api_router.include_router(races.router, prefix="/races", tags=["races"])
