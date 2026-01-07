from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.config import settings
from app.api.api import api_router
from app.websockets.connection_manager import manager
import json

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router, prefix=settings.API_V1_STR)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/create-character", response_class=HTMLResponse)
async def create_character_view(request: Request):
    return templates.TemplateResponse("create_character.html", {"request": request})

@app.get("/game", response_class=HTMLResponse)
async def game_view(request: Request):
    return templates.TemplateResponse("game.html", {"request": request})

from app.game.engine import GameEngine
from app.core.database import SessionLocal 
from app.models.player import Player

engine = GameEngine(manager)

@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: int):
    # In a real app, validate token here!
    await manager.connect(websocket, player_id)
    try:
        # Initial Look with its own session
        with SessionLocal() as db:
            player = db.query(Player).filter(Player.id == player_id).first()
            if player:
                await engine.cmd_look(player, [])

        while True:
            data = await websocket.receive_text()
            # Process command via Engine with a FRESH session/context
            # We open a NEW session for each command to ensure data freshness and avoid stale state
            with SessionLocal() as db:
                await engine.process_command(player_id, data, db)
                
    except Exception as e:
        print(f"WS Error: {e}")
        manager.disconnect(player_id)

