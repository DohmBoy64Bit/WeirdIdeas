from pydantic import BaseModel
from typing import Dict, List

class RaceBase(BaseModel):
    name: str
    description: str
    base_stats: Dict

class RaceResponse(BaseModel):
    id: int
    name: str
    description: str
    base_stats: dict
    scaling_stats: dict
    transformations: list
    base_flux: int = 100  # Default value if not present

    class Config:
        from_attributes = True
