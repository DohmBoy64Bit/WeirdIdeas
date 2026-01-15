from fastapi import APIRouter, Depends, status, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.extensions import get_db
from app.models.user import User, UserRole
from app.models.script import Script
from app.dependencies import get_current_admin
from app.services import script_service

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    # Stats
    user_count = await db.scalar(select(func.count(User.id)))
    script_count = await db.scalar(select(func.count(Script.id)))
    
    # Recent Users
    recent_users = await db.execute(select(User).order_by(desc(User.created_at)).limit(5))
    recent_users = recent_users.scalars().all()
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "user": current_user,
        "user_count": user_count,
        "script_count": script_count,
        "recent_users": recent_users
    })

@router.get("/users", response_class=HTMLResponse)
async def manage_users(
    request: Request,
    q: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    query = select(User).order_by(desc(User.created_at))
    if q:
        query = query.where(User.username.ilike(f"%{q}%"))
        
    result = await db.execute(query)
    users = result.scalars().all()
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "user": current_user,
        "users": users,
        "q": q
    })

@router.post("/users/{user_id}/ban")
async def ban_user(
    user_id: int,
    request: Request,
    reason: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    # Prevent self-ban
    if user_id == current_user.id:
        return RedirectResponse(url="/admin/users", status_code=status.HTTP_303_SEE_OTHER)
        
    user = await db.get(User, user_id)
    if user:
        user.is_active = not user.is_active
        if not user.is_active:
            user.ban_reason = reason or "No reason provided"
        else:
            user.ban_reason = None
        await db.commit()
    return RedirectResponse(url="/admin/users", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/users/{user_id}/toggle_admin")
async def toggle_admin(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    if user_id == current_user.id:
         return RedirectResponse(url="/admin/users", status_code=status.HTTP_303_SEE_OTHER)

    user = await db.get(User, user_id)
    if user:
        user.is_admin = not user.is_admin
        if user.is_admin:
            user.role = UserRole.ADMIN
        else:
            user.role = UserRole.USER
        await db.commit()
    return RedirectResponse(url="/admin/users", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/scripts", response_class=HTMLResponse)
async def manage_scripts(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(
        select(Script)
        .options(selectinload(Script.uploader))
        .order_by(desc(Script.created_at))
    )
    scripts = result.scalars().all()
    
    return templates.TemplateResponse("admin/scripts.html", {
        "request": request,
        "user": current_user,
        "scripts": scripts
    })

@router.post("/scripts/{script_id}/validate")
async def validate_script(
    script_id: int,
    validation_status: bool = Form(..., alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    new_status_str = "verified" if validation_status else "unverified"
    script = await script_service.set_validation_status(db, script_id, validation_status)
    
    # Notify author if validated (safely)
    try:
        if script and validation_status:
            from app.services import notification_service
            from app.models.notification import NotificationType
            await notification_service.create_notification(
                db, 
                script.uploader_id, 
                f"Your script '{script.title}' has been verified by an admin!",
                NotificationType.SYSTEM,
                f"/script/{script.id}"
            )
    except Exception as e:
        print(f"Error creating notification: {e}")
        
    return RedirectResponse(url="/admin/scripts", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/scripts/{script_id}/delete")
async def delete_script_admin(
    script_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    success = await script_service.delete_script(db, script_id)
    if not success:
        raise HTTPException(status_code=404, detail="Script not found")
    return RedirectResponse(url="/admin/scripts", status_code=status.HTTP_303_SEE_OTHER)
