from fastapi import APIRouter, Depends, Query, Request, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.extensions import get_db
from app.services import forum_service, auth_service
from app.models.user import User
from app.dependencies import get_current_user_opt

router = APIRouter(prefix="/forum", tags=["forum"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def forum_index(request: Request, db: AsyncSession = Depends(get_db)):
    categories = await forum_service.get_categories(db)
    user = await get_current_user_opt(request, db)
    return templates.TemplateResponse("forum/index.html", {
        "request": request, 
        "categories": categories,
        "user": user
    })

@router.get("/cat/{slug}", response_class=HTMLResponse)
async def category_view(slug: str, request: Request, db: AsyncSession = Depends(get_db)):
    category = await forum_service.get_category_by_slug(db, slug)
    if not category:
        raise HTTPException(404, "Category not found")
    user = await get_current_user_opt(request, db)
    return templates.TemplateResponse("forum/category.html", {
        "request": request,
        "category": category,
        "user": user
    })

@router.get("/thread/{thread_id}", response_class=HTMLResponse)
async def thread_view(thread_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    thread = await forum_service.get_thread_by_id(db, thread_id)
    if not thread:
        raise HTTPException(404, "Thread not found")
    user = await get_current_user_opt(request, db)
    return templates.TemplateResponse("forum/thread.html", {
        "request": request,
        "thread": thread,
        "user": user
    })

@router.post("/create_thread")
async def create_thread(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    category_id: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_opt(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    thread = await forum_service.create_thread(db, user, category_id, title, content)
    return RedirectResponse(f"/forum/thread/{thread.id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/reply")
async def reply_to_thread(
    request: Request,
    thread_id: int = Form(...),
    content: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_opt(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    post = await forum_service.create_post(db, user, thread_id, content)
    
    # Notify thread author (safely)
    try:
        thread = await forum_service.get_thread_by_id(db, thread_id)
        if thread and thread.author_id != user.id:
            from app.services import notification_service
            from app.models.notification import NotificationType
            await notification_service.create_notification(
                db, 
                thread.author_id, 
                f"{user.username} replied to your thread '{thread.title}'",
                NotificationType.COMMENT,
                f"/forum/thread/{thread.id}#post-{post.id}"
            )
    except Exception as e:
        print(f"Error creating notification: {e}")

    return RedirectResponse(f"/forum/thread/{thread_id}", status_code=status.HTTP_303_SEE_OTHER)
