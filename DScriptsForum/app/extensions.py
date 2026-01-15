from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
import redis.asyncio as redis

# SQLAlchemy
connect_args = {"check_same_thread": False} if settings.USE_SQLITE else {}
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=False, 
    future=True,
    connect_args=connect_args
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Redis
try:
    redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
except Exception as e:
    print(f"Warning: Redis connection failed. {e}")
    redis_client = None

async def get_redis():
    return redis_client
