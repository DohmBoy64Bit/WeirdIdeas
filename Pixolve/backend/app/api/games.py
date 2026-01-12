from fastapi import APIRouter, HTTPException, Depends
from ..services import auth_service
from .lobbies import _LOBBIES
from ..services import game_service
from .auth import get_current_user

router = APIRouter()


@router.post("/{lobby_id}/start")
def start_game(lobby_id: str, user: dict = Depends(get_current_user)):
    if lobby_id not in _LOBBIES:
        raise HTTPException(status_code=404, detail="Lobby not found")
    lobby = _LOBBIES[lobby_id]
    # host may be stored as username or user id; allow both for now
    if str(user.get("id")) != str(lobby.host_id) and str(user.get("username")) != str(lobby.host_id):
        raise HTTPException(status_code=403, detail="Only host can start the game")
    try:
        gs = game_service.start_game_for_lobby(lobby_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Unable to start game")
    return {"game_id": gs.id}
