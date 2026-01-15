from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.schemas.auth import UserResponse

class PostBase(BaseModel):
    content: str = Field(..., min_length=1)

class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    id: int
    thread_id: int
    author_id: int
    created_at: datetime
    updated_at: datetime
    author: UserResponse

    model_config = ConfigDict(from_attributes=True)

class ThreadBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)

class ThreadCreate(ThreadBase):
    content: str = Field(..., min_length=1) # Initial post content
    category_id: int

class ThreadResponse(ThreadBase):
    id: int
    category_id: int
    author_id: int
    pinned: bool
    locked: bool
    views: int
    created_at: datetime
    updated_at: datetime
    author: UserResponse
    posts: List[PostResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ThreadList(ThreadResponse):
    # Lighter version for lists, maybe without all posts
    reply_count: int = 0 
    last_post_at: Optional[datetime] = None

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int
    slug: str
    display_order: int
    threads: List[ThreadList] = []

    model_config = ConfigDict(from_attributes=True)
