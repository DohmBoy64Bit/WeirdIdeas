from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from jose import jwt
from app.config import settings
from app.extensions import get_db
from app.models.user import User, UserRole
from app.services import auth_service

async def get_current_user_opt(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[User]:
    """Optional authentication dependency. Returns User or None."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        scheme, _, token_str = token.partition(" ")
        # Support both 'Bearer <token>' and plain '<token>'
        if not token_str:
            token_str = scheme
            
        payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if not username:
            return None
        user = await auth_service.get_user_by_username(db, username)
        # Check if user is banned
        if user and not user.is_active:
            return None
        return user
    except Exception as e:
        return None

async def get_current_admin(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Strict admin authorization dependency. Raises 401/403 if not authorized."""
    user = await get_current_user_opt(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if not user.is_admin and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return user
