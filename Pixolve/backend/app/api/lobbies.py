from fastapi import APIRouter, HTTPException
from ..schemas.lobby import LobbyCreate, LobbyOut, PlayerInLobby
from pydantic import BaseModel
from typing import Dict
import secrets

router = APIRouter()

# In-memory lobbies store for skeleton implementation
_LOBBIES: Dict[str, LobbyOut] = {}


@router.post("/", response_model=LobbyOut)
def create_lobby(spec: LobbyCreate):
    """Create a lobby; host_id should be provided (returned value includes a join_code)."""
    import uuid
    lobby_id = str(uuid.uuid4())
    join_code = "".join(secrets.choice("ABCDEFGHJKMNPQRSTUVWXYZ23456789") for _ in range(6))
    host = spec.host_id or "host-unknown"
    lobby = LobbyOut(id=lobby_id, host_id=host, max_players=spec.max_players, players=[], category=spec.category, rounds=spec.rounds, join_code=join_code)
    _LOBBIES[lobby_id] = lobby
    return lobby


class JoinByCode(BaseModel):
    join_code: str
    player: PlayerInLobby


@router.post("/join_by_code")
def join_by_code(req: JoinByCode):
    # find lobby by join_code
    for l in _LOBBIES.values():
        if l.join_code == req.join_code:
            if len(l.players) >= l.max_players:
                raise HTTPException(status_code=400, detail="Lobby full")
            l.players.append(req.player)
            return {"lobby": l, "players": l.players}
    raise HTTPException(status_code=404, detail="Lobby with that join code not found")


@router.post("/{lobby_id}/join")
def join_lobby(lobby_id: str, player: PlayerInLobby):
    if lobby_id not in _LOBBIES:
        raise HTTPException(status_code=404, detail="Lobby not found")
    lobby = _LOBBIES[lobby_id]
    if len(lobby.players) >= lobby.max_players:
        raise HTTPException(status_code=400, detail="Lobby full")
    # prevent duplicate player ids
    if any(p.id == player.id for p in lobby.players):
        raise HTTPException(status_code=400, detail="Player already in lobby")
    lobby.players.append(player)
    return {"lobby": lobby, "players": lobby.players}

@router.post("/{lobby_id}/leave")
def leave_lobby(lobby_id: str, player: PlayerInLobby):
    if lobby_id not in _LOBBIES:
        raise HTTPException(status_code=404, detail="Lobby not found")
    lobby = _LOBBIES[lobby_id]
    lobby.players = [p for p in lobby.players if p.id != player.id]
    return {"lobby": lobby}