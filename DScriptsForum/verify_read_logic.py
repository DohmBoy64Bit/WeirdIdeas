import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.notification import Notification, NotificationType
from app.models.script import Script
from app.services import notification_service
from app.config import settings

# Setup DB
engine = create_async_engine(settings.DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def test_logic():
    async with SessionLocal() as db:
        print("--- Testing Notification Logic ---")
        
        # 1. Get a test user (admin)
        result = await db.execute(select(User).limit(1))
        user = result.scalars().first()
        if not user:
            print("No user found to test with.")
            return

        print(f"Testing with user: {user.username} (ID: {user.id})")

        # 2. Check initial count
        initial_count = await notification_service.get_unread_count(db, user.id)
        print(f"Initial Unread Count: {initial_count}")

        # 3. Create a new notification
        print("Creating new notification...")
        await notification_service.create_notification(
            db, user.id, "Test Notification", NotificationType.SYSTEM
        )
        
        # 4. Check count again
        mid_count = await notification_service.get_unread_count(db, user.id)
        print(f"Count after creation: {mid_count} (Expected: {initial_count + 1})")

        # 5. Mark all read
        print("Marking all as read...")
        await notification_service.mark_all_read(db, user.id)

        # 6. Check final count
        final_count = await notification_service.get_unread_count(db, user.id)
        print(f"Final Count: {final_count} (Expected: 0)")
        
        if final_count == 0:
            print("SUCCESS: Notifications marked as read.")
        else:
            print("FAILURE: Notifications still unread.")
            # Print their status
            result = await db.execute(select(Notification).where(Notification.user_id == user.id))
            all_notifs = result.scalars().all()
            for n in all_notifs:
                print(f" - ID: {n.id}, Read: {n.read}")

from sqlalchemy import select

if __name__ == "__main__":
    asyncio.run(test_logic())
