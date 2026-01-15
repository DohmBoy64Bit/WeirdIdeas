from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.models.forum import Category, Thread, Post
from app.models.user import User
from app.utils.security import sanitize_html
from app.services.user_service import increment_user_rep

async def get_categories(db: AsyncSession) -> List[Category]:
    # We might want to load threads later, but for index we just need list
    stmt = select(Category).options(selectinload(Category.threads)).order_by(Category.display_order)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_category_by_slug(db: AsyncSession, slug: str) -> Optional[Category]:
    stmt = select(Category).where(Category.slug == slug).options(
        selectinload(Category.threads).selectinload(Thread.author)
    )
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_thread_by_id(db: AsyncSession, thread_id: int) -> Optional[Thread]:
    stmt = select(Thread).where(Thread.id == thread_id).options(
        selectinload(Thread.author),
        selectinload(Thread.category),
        selectinload(Thread.posts).selectinload(Post.author)
    )
    result = await db.execute(stmt)
    return result.scalars().first()

async def create_thread(
    db: AsyncSession, 
    user: User, 
    category_id: int, 
    title: str, 
    content: str
) -> Thread:
    # 1. Create Thread
    new_thread = Thread(
        title=title,
        category_id=category_id,
        author_id=user.id
    )
    db.add(new_thread)
    await db.flush() # flush to get thread ID

    # 2. Create Initial Post (OP)
    new_post = Post(
        content=sanitize_html(content),
        thread_id=new_thread.id,
        author_id=user.id
    )
    db.add(new_post)
    
    # Award Reputation (5 for thread)
    await increment_user_rep(db, user.id, 5)
    
    await db.commit()
    await db.refresh(new_thread)
    return new_thread

async def create_post(
    db: AsyncSession, 
    user: User, 
    thread_id: int, 
    content: str
) -> Post:
    new_post = Post(
        content=sanitize_html(content),
        thread_id=thread_id,
        author_id=user.id
    )
    db.add(new_post)
    
    # Award Reputation (2 for reply)
    await increment_user_rep(db, user.id, 2)
    
    await db.commit()
    await db.refresh(new_post)
    return new_post
