from fastapi import APIRouter, Depends, Form, Request, status, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.extensions import get_db
from app.services import script_service
from app.dependencies import get_current_user_opt
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/script", tags=["script"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user_opt(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("script/upload.html", {"request": request, "user": user})

@router.post("/upload")
@limiter.limit("10/hour")
async def handle_upload(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    code: str = Form(...),
    version: str = Form("1.0"),
    images: List[UploadFile] = File(default=None),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_opt(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    script_data = {
        "title": title,
        "description": description,
        "code": code,
        "version": version
    }
    
    script = await script_service.create_script(db, user, script_data, images=images)
    return RedirectResponse(f"/script/{script.id}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{script_id}", response_class=HTMLResponse)
async def view_script(script_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    script = await script_service.get_script_by_id(db, script_id)
    if not script:
        raise HTTPException(404, "Script not found")
        
    await script_service.increment_views(db, script)
    
    user = await get_current_user_opt(request, db)
    return templates.TemplateResponse("script/view.html", {
        "request": request,
        "script": script,
        "user": user
    })

@router.get("/{script_id}/download")
@limiter.limit("5/minute") # Added rate limit
async def download_script(script_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    script = await script_service.get_script_by_id(db, script_id)
    if not script:
        raise HTTPException(404, "Script not found")
        
    await script_service.increment_downloads(db, script)
    
    return PlainTextResponse(script.code, media_type="text/plain", headers={
        "Content-Disposition": f'attachment; filename="{script.title.replace(" ", "_")}.lua"'
    })

@router.post("/{script_id}/like")
@limiter.limit("30/minute")
async def like_script(script_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user_opt(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    script = await script_service.get_script_by_id(db, script_id)
    if not script:
        raise HTTPException(404, "Script not found")

    # Prevent self-likes
    if script.uploader_id == user.id:
        referer = request.headers.get("referer")
        return RedirectResponse(referer or f"/script/{script_id}", status_code=status.HTTP_303_SEE_OTHER)
        
    liked = await script_service.toggle_like(db, user, script_id)
    
    # Trigger notification if liked (and not self-like, which is now impossible but safe to keep logic)
    if liked:
        from app.services import notification_service
        from app.models.notification import NotificationType
        await notification_service.create_notification(
            db, 
            script.uploader_id, 
            f"{user.username} liked your script '{script.title}'",
            NotificationType.LIKE,
            f"/script/{script.id}"
        )
    
    referer = request.headers.get("referer")
    return RedirectResponse(referer or f"/script/{script_id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/{script_id}/comment")
async def comment_script(
    script_id: int, 
    request: Request, 
    content: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user_opt(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    script = await script_service.get_script_by_id(db, script_id)
    if not script:
        raise HTTPException(404, "Script not found")
        
    # Create comment with sanitization
    from app.utils.security import sanitize_html
    from app.models.script import ScriptComment
    
    comment = ScriptComment(
        content=sanitize_html(content),
        user_id=user.id,
        script_id=script_id
    )
    db.add(comment)
    await db.commit()
    
    # Notify author
    if script.uploader_id != user.id:
        from app.services import notification_service
        from app.models.notification import NotificationType
        await notification_service.create_notification(
            db, 
            script.uploader_id, 
            f"{user.username} commented on your script '{script.title}'",
            NotificationType.COMMENT,
            f"/script/{script.id}#comment-{comment.id}"
        )

    return RedirectResponse(f"/script/{script_id}", status_code=status.HTTP_303_SEE_OTHER)
