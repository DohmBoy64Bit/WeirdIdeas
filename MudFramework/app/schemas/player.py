from pydantic import BaseModel
from typing import Dict, List, Optional

class PlayerBase(BaseModel):
    name: str
    race: str

class PlayerCreate(PlayerBase):
    pass

class PlayerResponse(PlayerBase):
    id: int
    level: int
    exp: int
    stats: Dict
    inventory: List
    current_map: str
    position: Dict

    class Config:
        from_attributes = True
