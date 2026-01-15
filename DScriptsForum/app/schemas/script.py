from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.schemas.auth import UserResponse
from typing import Optional

class ScriptBase(BaseModel):
    title: str
    description: str
    code: str
    version: str = "1.0"

class ScriptCreate(ScriptBase):
    pass

class ScriptResponse(ScriptBase):
    id: int
    views: int
    downloads: int
    likes_count: int
    validated: bool
    uploader: UserResponse
    created_at: datetime
    updated_at: datetime
    
    # helper for checking like status in specific contexts, 
    # though usually handled in template via user relation check
    
    model_config = ConfigDict(from_attributes=True)
