from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.extensions import Base
from datetime import datetime
from typing import List

class Category(Base):
    __tablename__ = "forum_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    icon: Mapped[str] = mapped_column(String(50), nullable=True) # FontAwesome class or URL
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    threads: Mapped[List["Thread"]] = relationship("Thread", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category {self.name}>"

class Thread(Base):
    __tablename__ = "forum_threads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    
    category_id: Mapped[int] = mapped_column(ForeignKey("forum_categories.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    views: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="threads")
    author: Mapped["User"] = relationship("User")
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="thread", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Thread {self.id}: {self.title}>"

class Post(Base):
    __tablename__ = "forum_posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    thread_id: Mapped[int] = mapped_column(ForeignKey("forum_threads.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    thread: Mapped["Thread"] = relationship("Thread", back_populates="posts")
    author: Mapped["User"] = relationship("User")

    def __repr__(self):
        return f"<Post {self.id} by {self.author_id}>"
