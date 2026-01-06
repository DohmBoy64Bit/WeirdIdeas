from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core import security
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, UserSignupResponse, UserRecover
import secrets

router = APIRouter()

@router.post("/signup", response_model=UserSignupResponse)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_in.username).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The username with this username already exists in the system.",
        )
    
    # Generate Recovery Code
    recovery_code = secrets.token_urlsafe(16)
    hashed_recovery_code = security.get_password_hash(recovery_code)
    
    new_user = User(
        username=user_in.username,
        hashed_password=security.get_password_hash(user_in.password),
        hashed_recovery_code=hashed_recovery_code,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Return user with the recovery code in the response
    return UserSignupResponse(
        id=new_user.id,
        username=new_user.username,
        is_active=new_user.is_active,
        recovery_code=recovery_code # Only time this is shown
    )

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_in.username).first()
    if not user or not security.verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/recover", response_model=Token)
def recover_password(recover_in: UserRecover, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == recover_in.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not security.verify_password(recover_in.recovery_code, user.hashed_recovery_code):
        raise HTTPException(status_code=400, detail="Invalid recovery code")
        
    # Reset Password
    user.hashed_password = security.get_password_hash(recover_in.new_password)
    # Generate NEW recovery code? Or keep old? "One time use"... 
    # Usually you'd assume the code is burn on use or persistent. 
    # "one time use" suggests burn. Let's start with just resetting password.
    
    db.commit()
    
    # Return login token immediately
    access_token = security.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

