from pydantic import BaseModel
from typing import List, Optional

class PlayerInLobby(BaseModel):
    id: str
    username: str
    display_name: Optional[str]
    ready: bool = False

class LobbyCreate(BaseModel):
    max_players: int = 5
    category: Optional[str] = None
    rounds: int = 5
    host_id: Optional[str] = None

class LobbyOut(BaseModel):
    id: str
    host_id: str
    max_players: int
    players: List[PlayerInLobby]
    category: Optional[str]
    rounds: int
    join_code: Optional[str] = None