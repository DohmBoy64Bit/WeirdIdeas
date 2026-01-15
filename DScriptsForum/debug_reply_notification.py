import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.config import settings
from app.models.user import User
from app.models.forum import Category, Thread, Post
from app.models.script import Script
from app.models.notification import Notification, NotificationType
from app.services import forum_service
# We need to mimic the local import
# from app.services import notification_service 

# Setup DB
engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def debug_reply():
    async with SessionLocal() as db:
        print("--- Debugging Reply Notification ---")
        
        # 1. Get users
        users = (await db.execute(select(User).limit(2))).scalars().all()
        if len(users) < 2:
            print("Need at least 2 users to test reply notification.")
            return

        author = users[0]
        replier = users[1]
        print(f"Author: {author.username} ({author.id})")
        print(f"Replier: {replier.username} ({replier.id})")

        # 2. Create Thread
        print("Creating temp thread...")
        thread = await forum_service.create_thread(db, author, 1, "Debug Thread", "Content")
        print(f"Thread created: {thread.id}")

        # 3. Create Reply (Mimic Route)
        print("Creating reply...")
        content = "Test Reply"
        # route: post = await forum_service.create_post(db, user, thread_id, content)
        post = await forum_service.create_post(db, replier, thread.id, content)
        print(f"Post created: {post.id}")

        # 4. Run Notification Logic (COPY FROM ROUTE)
        print("Running notification logic...")
        try:
            # We must re-fetch thread as in route
            thread = await forum_service.get_thread_by_id(db, thread.id)
            
            # Mimic route variables
            user = replier # "user" in route is current_user (replier)

            if thread and thread.user_id != user.id:
                print("Condition met: Thread author != Replier")
                from app.services import notification_service
                from app.models.notification import NotificationType
                
                await notification_service.create_notification(
                    db, 
                    thread.user_id, 
                    f"{user.username} replied to your thread '{thread.title}'",
                    NotificationType.COMMENT,
                    f"/forum/thread/{thread.id}#post-{post.id}"
                )
                print("Notification created successfully!")
            else:
                print(f"Condition NOT met. Thread User ID: {thread.user_id}, Current User ID: {user.id}")

        except Exception as e:
            print("CAUGHT EXCEPTION:")
            print(e)
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_reply())
