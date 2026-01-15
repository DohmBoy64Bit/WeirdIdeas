from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.models.script import Script, script_likes
from app.models.user import User
from app.utils.security import sanitize_html

import os
import uuid
import shutil
import json
from typing import List

UPLOAD_DIR = "app/static/uploads"

async def save_upload_files(images: list) -> List[str]:
    """Helper to save uploaded images and return their relative paths."""
    if not images:
        return []
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    image_paths = []
    
    for image in images:
        if not image.filename or not image.content_type.startswith("image/"):
            continue
            
        # File size validation (Max 2MB)
        image.file.seek(0, 2)
        file_size = image.file.tell()
        image.file.seek(0)
        
        if file_size > 2 * 1024 * 1024:
            continue

        filename = f"{uuid.uuid4()}_{image.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        image_paths.append(f"/static/uploads/{filename}")
        if len(image_paths) >= 3:
            break
            
    return image_paths

async def create_script(db: AsyncSession, user: User, script_in: dict, images: list = None) -> Script:
    image_paths = await save_upload_files(images) if images else []
    
    new_script = Script(
        title=script_in["title"],
        description=sanitize_html(script_in["description"]),
        code=script_in["code"],
        version=script_in.get("version", "1.0"),
        image_urls=json.dumps(image_paths),
        uploader_id=user.id
    )
    db.add(new_script)
    await db.commit()
    await db.refresh(new_script)
    return new_script

async def set_validation_status(db: AsyncSession, script_id: int, status: bool) -> Optional[Script]:
    script = await get_script_by_id(db, script_id)
    if script:
        script.validated = status
        await db.commit()
        await db.refresh(script)
    return script

async def delete_script(db: AsyncSession, script_id: int) -> bool:
    script = await get_script_by_id(db, script_id)
    if not script:
        return False
    await db.delete(script)
    await db.commit()
    return True

async def get_script_by_id(db: AsyncSession, script_id: int) -> Optional[Script]:
    stmt = select(Script).where(Script.id == script_id).options(
        selectinload(Script.uploader),
        selectinload(Script.comments).selectinload(Script.comments.property.mapper.class_.author)
    )
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_recent_scripts(db: AsyncSession, limit: int = 10) -> List[Script]:
    stmt = select(Script).order_by(desc(Script.created_at)).limit(limit).options(
        selectinload(Script.uploader)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_trending_scripts(db: AsyncSession, limit: int = 6) -> List[Script]:
    # Simple trending algo: most views + likes (weighted)
    # For now, just sort by views desc
    stmt = select(Script).order_by(desc(Script.views)).limit(limit).options(
        selectinload(Script.uploader)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def increment_views(db: AsyncSession, script: Script):
    script.views += 1
    await db.commit()

async def increment_downloads(db: AsyncSession, script: Script):
    script.downloads += 1
    await db.commit()

async def toggle_like(db: AsyncSession, user: User, script_id: int) -> bool:
    # Check if liked
    stmt = select(script_likes).where(
        script_likes.c.user_id == user.id, 
        script_likes.c.script_id == script_id
    )
    result = await db.execute(stmt)
    existing = result.first()
    
    script = await get_script_by_id(db, script_id)
    if not script:
        return False
        
    if existing:
        # Unlike
        stmt = delete(script_likes).where(
            script_likes.c.user_id == user.id, 
            script_likes.c.script_id == script_id
        )
        await db.execute(stmt)
        script.likes_count = max(0, script.likes_count - 1)
        
        # Decrement reputation (only if it wasn't a self-like, though self-likes are now blocked)
        if script.uploader_id != user.id:
            from sqlalchemy import update
            stmt = update(User).where(User.id == script.uploader_id).values(reputation=User.reputation - 10)
            await db.execute(stmt)

        await db.commit()
        return False

    else:
        # Like
        stmt = script_likes.insert().values(user_id=user.id, script_id=script_id)
        await db.execute(stmt)
        script.likes_count += 1
        
        # Increment reputation
        if script.uploader_id != user.id:
            from sqlalchemy import update
            stmt = update(User).where(User.id == script.uploader_id).values(reputation=User.reputation + 10)
            await db.execute(stmt)
        
        await db.commit()
        return True
