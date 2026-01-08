from fastapi import FastAPI, WebSocket, WebSocketException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.api.api import api_router
from app.api.deps import get_user_from_token
from app.websockets.connection_manager import manager
from app.game.engine import GameEngine
from app.core.database import SessionLocal 
from app.models.player import Player
from app.core.constants import MAX_COMMAND_LENGTH
from app.core.messages import GameMessages
import logging
import json

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

# Set rate limiter for auth routes
from app.api.endpoints import auth
if hasattr(auth, 'set_limiter'):
    auth.set_limiter(limiter)

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

engine = GameEngine(manager)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """WebSocket endpoint with authentication. Token must be provided as query parameter."""
    if not token:
        logger.warning("WebSocket connection attempted without token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Authenticate user
    user = get_user_from_token(token)
    if not user:
        logger.warning(f"WebSocket connection failed: invalid token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Get player for this user
    with SessionLocal() as db:
        player = db.query(Player).filter(Player.user_id == user.id).first()
        if not player:
            logger.warning(f"WebSocket connection failed: no player for user {user.id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        player_id = player.id
    
    await manager.connect(websocket, player_id)
    logger.info(f"WebSocket connected: player_id={player_id}, user={user.username}")
    
    try:
        # Initial UI refresh
        with SessionLocal() as db:
            player = db.query(Player).filter(Player.id == player_id).first()
            if player:
                await engine.refresh_ui(player)

        # Reuse session for command processing to reduce overhead
        with SessionLocal() as db:
            while True:
                data = await websocket.receive_text()
                
                # Input validation
                if len(data) > MAX_COMMAND_LENGTH:
                    logger.warning(
                        f"Command too long from player {player_id}: {len(data)} chars"
                    )
                    await manager.send_personal_message(
                        {
                            "type": "chat",
                            "sender": "System",
                            "content": GameMessages.COMMAND_TOO_LONG.format(
                                max_length=MAX_COMMAND_LENGTH
                            ),
                            "channel": "channel-system",
                        },
                        player_id,
                    )
                    continue
                
                # Process command
                await engine.process_command(player_id, data, db)
                
    except WebSocketException:
        logger.info(f"WebSocket connection closed normally: player_id={player_id}")
        manager.disconnect(player_id)
    except Exception as e:
        logger.error(f"WebSocket error for player {player_id}: {e}", exc_info=True)
        manager.disconnect(player_id)

