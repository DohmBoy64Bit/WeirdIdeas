from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import UserCreate
from app.utils.security import get_password_hash, verify_password
import secrets
import string

async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate) -> tuple[User, str]:
    # Check if user exists
    if await get_user_by_username(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Username already taken"
        )
        
    hashed_password = get_password_hash(user_in.password)
    
    # Generate Recovery Code
    recovery_code = '-'.join([''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4)) for _ in range(4)])
    recovery_code_hash = get_password_hash(recovery_code) # Store hash of it
    
    new_user = User(
        username=user_in.username,
        # email=user_in.email, # Removed
        password_hash=hashed_password,
        recovery_code_hash=recovery_code_hash
    )
    
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
        return new_user, recovery_code # Return plain code to show user once
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Database error during registration"
        )

async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    user = await get_user_by_username(db, username)
        
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
        
    return user
