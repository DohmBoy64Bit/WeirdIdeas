import asyncio
from app.extensions import AsyncSessionLocal, engine
from app.models.forum import Category
from app.models.user import User
from app.models.script import Script, ScriptComment
from app.models.notification import Notification # Register Notification
from sqlalchemy import select

async def seed_categories():
    async with AsyncSessionLocal() as session:
        # Check if exists
        result = await session.execute(select(Category))
        if result.scalars().first():
            print("Categories already exist. Skipping.")
            return

        categories = [
            Category(
                name="Announcements", 
                slug="announcements", 
                description="Official news and updates.", 
                icon="fas fa-bullhorn",
                display_order=1
            ),
            Category(
                name="General Discussion", 
                slug="general", 
                description="Chat about anything related to Roblox scripting.", 
                icon="fas fa-comments",
                display_order=2
            ),
            Category(
                name="Script Releases", 
                slug="releases", 
                description="Share your latest creations here.", 
                icon="fas fa-code",
                display_order=3
            ),
            Category(
                name="Help & Support", 
                slug="help", 
                description="Need help with a script? Ask here.", 
                icon="fas fa-question-circle",
                display_order=4
            ),
        ]
        
        session.add_all(categories)
        await session.commit()
        print("Seeded categories: Announcements, General, Releases, Help")

if __name__ == "__main__":
    asyncio.run(seed_categories())
