from pydantic import BaseModel
from typing import List, Optional

class Category(BaseModel):
    id: str
    name: str
    description: Optional[str]
    difficulty: Optional[int] = 1
    images: List[str] = []  # list of image ids or paths
    active: bool = True