from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update
from app.models.notification import Notification, NotificationType
from app.models.user import User

async def create_notification(
    db: AsyncSession, 
    user_id: int, 
    message: str, 
    type: NotificationType = NotificationType.SYSTEM, 
    link: str = None
):
    notification = Notification(
        user_id=user_id,
        message=message,
        type=type,
        link=link
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification

async def get_user_notifications(db: AsyncSession, user_id: int, limit: int = 10):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(desc(Notification.created_at))
        .limit(limit)
    )
    return result.scalars().all()

async def get_unread_count(db: AsyncSession, user_id: int) -> int:
    return await db.scalar(
        select(func.count(Notification.id))
        .where(Notification.user_id == user_id, Notification.read == False)
    ) or 0

async def mark_all_read(db: AsyncSession, user_id: int):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read == False)
        .values(read=True)
    )
    await db.commit()
