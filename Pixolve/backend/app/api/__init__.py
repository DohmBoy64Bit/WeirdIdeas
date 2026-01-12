from fastapi import APIRouter

api_router = APIRouter()

# Import and include sub-routers here
from . import lobbies, auth, ws, games, categories

api_router.include_router(auth.router, prefix="/auth", tags=["auth"]) 
api_router.include_router(lobbies.router, prefix="/lobbies", tags=["lobbies"])
api_router.include_router(games.router, prefix="/games", tags=["games"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
# Note: WebSocket route is `/ws`
api_router.include_router(ws.router)