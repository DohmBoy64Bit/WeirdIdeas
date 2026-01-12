from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    username: str
    display_name: Optional[str] = None

class UserCreate(UserBase):
    # For registration, password is required
    password: str

class UserOut(UserBase):
    id: str
    level: int = 1
    xp: int = 0

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"