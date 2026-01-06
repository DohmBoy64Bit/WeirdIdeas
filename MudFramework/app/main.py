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

@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: int):
    # In a real app, validate token here!
    await manager.connect(websocket, player_id)
    try:
        # Send initial welcome
        await manager.send_personal_message({
            "type": "chat",
            "sender": "System",
            "content": "Connected to Z-MUD Server.",
            "channel": "channel-system"
        }, player_id)
        
        while True:
            data = await websocket.receive_text()
            # Process command (simple echo/chat for now)
            
            # Broadcast to all
            await manager.broadcast({
                "type": "chat",
                "sender": f"Player {player_id}",
                "content": data,
                "channel": "channel-say"
            })
            
    except Exception as e:
        manager.disconnect(player_id)
