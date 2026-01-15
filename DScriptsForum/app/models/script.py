from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, Table, Column, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.extensions import Base
from datetime import datetime
# from app.models.user import User # explicit import REMOVED

script_likes = Table(
    "script_likes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("script_id", Integer, ForeignKey("scripts.id"), primary_key=True),
)

class ScriptComment(Base):
    __tablename__ = "script_comments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id"))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    author: Mapped["User"] = relationship("User")
    script: Mapped["Script"] = relationship("Script", back_populates="comments")

class Script(Base):
    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str] = mapped_column(Text) # changed to Text for longer descriptions
    code: Mapped[str] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    
    # Simple list storage for now, usually a separate table or JSON
    # SQLite doesn't have native array, so we store JSON string or use a relationship
    # For MVP simplicity: JSON string or just first image
    # Let's use JSON type if PG, but for SQLite compatibility in this demo, let's use a specialized TypeDecorator or just a relationship
    # Actually, for MVP: Let's assume input is list but we store as JSON encoded string or separate table.
    # To keep it simple and clean: Separate table OR simple string with delimiters.
    # Let's stick to simple: "image_urls" as JSON-compatible text.
    image_urls: Mapped[str] = mapped_column(Text, default="[]", nullable=True) # JSON Stored as Text
    validated: Mapped[bool] = mapped_column(Boolean, default=False)

    views: Mapped[int] = mapped_column(Integer, default=0)
    downloads: Mapped[int] = mapped_column(Integer, default=0)
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    
    uploader_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    uploader: Mapped["User"] = relationship("User", back_populates="scripts")
    comments: Mapped[list["ScriptComment"]] = relationship("ScriptComment", back_populates="script", cascade="all, delete-orphan", order_by="desc(ScriptComment.created_at)")
    
    # Relationships
    liked_by: Mapped[list["User"]] = relationship("User", secondary="script_likes", back_populates="liked_scripts")

    @property
    def image_list(self):
        import json
        try:
            # Handle if it's already a list (from some test mocks) or string
            if isinstance(self.image_urls, list):
                return [url for url in self.image_urls if url]  # Filter empty strings
            if not self.image_urls:
                return []
            # Check if it looks like a list
            if self.image_urls.startswith("["):
                 parsed = json.loads(self.image_urls)
                 return [url for url in parsed if url]  # Filter empty strings
            return [self.image_urls] if self.image_urls else []  # Fallback
        except:
            return []
            
    # Allow setting list
    @image_list.setter
    def image_list(self, value):
        import json
        self.image_urls = json.dumps(value)
