from fastapi import APIRouter, Depends, HTTPException, status, Request, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.extensions import get_db
from app.models.script import Script
from app.dependencies import get_current_user_opt
from app.services import auth_service, user_service

router = APIRouter(tags=["user"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/user/{username}", response_class=HTMLResponse)
async def user_profile(username: str, request: Request, db: AsyncSession = Depends(get_db)):
    # Get target user
    db_user = await auth_service.get_user_by_username(db, username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Get current user (for navbar)
    current_user = await get_current_user_opt(request, db)
    
    # Get Script Count
    result = await db.execute(select(func.count(Script.id)).where(Script.uploader_id == db_user.id))
    script_count = result.scalar() or 0
    
    # Get Users Scripts
    result_scripts = await db.execute(
        select(Script)
        .where(Script.uploader_id == db_user.id)
        .order_by(Script.created_at.desc())
        .options(selectinload(Script.liked_by)) 
    )
    scripts = result_scripts.scalars().all()
    
    # Calculate Badges
    badges = user_service.calculate_badges(db_user, script_count)
    
    # Get flash message from query params if present
    error_msg = request.query_params.get('error')
    success_msg = request.query_params.get('success')
    
    return templates.TemplateResponse("user/profile.html", {
        "request": request,
        "user": current_user, # Logged in user
        "profile_user": db_user, # User being viewed
        "script_count": script_count,
        "scripts": scripts,
        "badges": badges,
        "error": error_msg,
        "success": success_msg
    })

@router.get("/cp")
async def control_panel(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user_opt(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(f"/user/{user.username}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/cp/avatar")
async def upload_avatar(
    request: Request,
    avatar: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_opt(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Save avatar
    avatar_url, error = await user_service.save_avatar(avatar, user.id)
    
    if error:
        return RedirectResponse(
            f"/user/{user.username}?error={error}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    # Update user's avatar_url
    user.avatar_url = avatar_url
    await db.commit()
    
    return RedirectResponse(
        f"/user/{user.username}?success=Avatar updated successfully!",
        status_code=status.HTTP_303_SEE_OTHER
    )
