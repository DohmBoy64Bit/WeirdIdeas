import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import settings

async def check_alembic_version():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT * FROM alembic_version;"))
        version = result.scalars().first()
        print("Alembic Version in DB:", version)

if __name__ == "__main__":
    asyncio.run(check_alembic_version())
