from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from ..schemas.user import UserCreate, UserOut, Token
from ..services import auth_service

router = APIRouter()


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/register", response_model=UserOut)
def register(user: UserCreate):
    """Register a new user with username/password."""
    try:
        u = auth_service.create_user(user.username, user.password, user.display_name)
        return UserOut(id=u["id"], username=u["username"], display_name=u.get("display_name"), level=u.get("level", 1), xp=u.get("xp", 0))
    except ValueError:
        raise HTTPException(status_code=400, detail="Username already exists")


@router.post("/login", response_model=Token)
def login(creds: LoginIn):
    u = auth_service.authenticate(creds.username, creds.password)
    if not u:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth_service.create_token(u["id"])
    return Token(access_token=token)


def get_current_user(authorization: str = Header(None)):
    """Simple dependency to get a user from Authorization: Bearer <token> header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth header format")
    token = parts[1]
    user = auth_service.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    # return public user info
    return {"id": user.get("id"), "username": user.get("username"), "display_name": user.get("display_name"), "level": user.get("level",1), "xp": user.get("xp",0)}