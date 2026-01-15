import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.extensions import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.script import Script, ScriptComment  # Import to register
from app.models.notification import Notification  # Import to register
from passlib.hash import argon2
from sqlalchemy import select

async def create_admin():
    async with AsyncSessionLocal() as session:
        # Check if admin exists
        result = await session.execute(select(User).where(User.username == "admin"))
        existing_admin = result.scalars().first()
        
        if existing_admin:
            # Promote existing user
            existing_admin.is_admin = True
            existing_admin.role = UserRole.ADMIN
            await session.commit()
            print(f"✅ Promoted existing user '{existing_admin.username}' to admin")
        else:
            # Create new admin user
            admin = User(
                username="admin",
                password_hash=argon2.hash("admin123"),
                is_admin=True,
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )
            session.add(admin)
            await session.commit()
            print("✅ Created new admin account:")
            print("   Username: admin")
            print("   Password: admin123")
            print("   Role: ADMIN")

if __name__ == "__main__":
    asyncio.run(create_admin())
