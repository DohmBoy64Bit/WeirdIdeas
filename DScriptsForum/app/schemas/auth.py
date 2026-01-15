from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    # email: EmailStr # Removed
    role: "UserRole" # Forward ref or Enum? Need to handle import carefully to avoid circulars
    reputation: int
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True

# Helper for Role enum in schema if needed, or stick to simple str for now if Enum triggers issues
from app.models.user import UserRole
UserResponse.model_rebuild()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
