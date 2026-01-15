from fastapi import APIRouter, Depends, status, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.extensions import get_db
from app.services.auth_service import authenticate_user, create_user
from app.schemas.auth import UserCreate
from app.utils.security import create_access_token
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": "Invalid username or password"
        })
    
    if not user.is_active:
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": f"You have been banned. Reason: {user.ban_reason or 'No reason provided'}"
        })
    
    # Create token (Subject is username now since email is gone)
    access_token = create_access_token(subject=user.username)
    
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True, 
        samesite="lax"
    )
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse)
@limiter.limit("3/hour")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        user_in = UserCreate(username=username, password=password)
        user, recovery_code = await create_user(db, user_in)
        
        # Render Success Page with Recovery Code
        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "success": True,
            "recovery_code": recovery_code,
            "username": username
        })
    except Exception as e:
        print(f"Registration Error: {e}") 
        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "error": str(e.detail) if hasattr(e, "detail") else str(e)
        })

@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response
