from sqlalchemy import String, Integer, Boolean, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.extensions import Base
import enum
from datetime import datetime

class UserRole(str, enum.Enum):
    USER = "user"
    SCRIPT_VALIDATOR = "script_validator"
    MODERATOR = "moderator"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    # Email removed per user request
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    recovery_code_hash: Mapped[str] = mapped_column(String(255), nullable=True)
    
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    reputation: Mapped[int] = mapped_column(Integer, default=0)
    
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)
    bio: Mapped[str] = mapped_column(String(500), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    ban_reason: Mapped[str] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    notifications: Mapped[list["Notification"]] = relationship("app.models.notification.Notification", back_populates="user", cascade="all, delete-orphan")
    scripts: Mapped[list["Script"]] = relationship("app.models.script.Script", back_populates="uploader")
    liked_scripts: Mapped[list["Script"]] = relationship("app.models.script.Script", secondary="script_likes", back_populates="liked_by")

    def __repr__(self):
        return f"<User {self.username}>"
