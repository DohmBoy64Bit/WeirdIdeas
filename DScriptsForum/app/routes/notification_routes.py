from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.extensions import get_db
from app.models.user import User
from app.dependencies import get_current_user_opt
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/")
async def get_notifications(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_opt)
):
    if not user:
        return []
    return await notification_service.get_user_notifications(db, user.id, limit)

@router.get("/unread")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_opt)
):
    if not user:
        return {"count": 0}
    try:
        return {"count": await notification_service.get_unread_count(db, user.id)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error getting unread count for user {user.id}: {e}")
        return {"count": 0}

@router.post("/read-all")
async def mark_read_all(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_opt)
):
    if user:
        await notification_service.mark_all_read(db, user.id)
    return {"status": "ok"}
