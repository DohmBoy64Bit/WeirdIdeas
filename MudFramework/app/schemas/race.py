from pydantic import BaseModel
from typing import Dict, List

class RaceBase(BaseModel):
    name: str
    description: str
    base_stats: Dict

class RaceResponse(RaceBase):
    id: int
    transformations: List[str]

    class Config:
        from_attributes = True
