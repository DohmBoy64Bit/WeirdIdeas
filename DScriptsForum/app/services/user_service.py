from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from PIL import Image
import os
import uuid
from typing import Optional

AVATAR_DIR = "app/static/avatars"
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB
TARGET_SIZE = (200, 200)
MIN_ASPECT_RATIO = 0.8
MAX_ASPECT_RATIO = 1.25

os.makedirs(AVATAR_DIR, exist_ok=True)

async def save_avatar(image_file, user_id: int) -> tuple[Optional[str], Optional[str]]:
    """
    Save and validate user avatar.
    Returns: (avatar_url, error_message)
    """
    try:
        # Read file content
        content = await image_file.read()
        
        # Check file size
        if len(content) > MAX_AVATAR_SIZE:
            return None, "Avatar file size must be less than 2MB"
        
        # Validate image with Pillow
        from io import BytesIO
        img = Image.open(BytesIO(content))
        
        # Check aspect ratio
        width, height = img.size
        aspect_ratio = width / height
        if aspect_ratio < MIN_ASPECT_RATIO or aspect_ratio > MAX_ASPECT_RATIO:
            return None, f"Avatar must be nearly square (aspect ratio between {MIN_ASPECT_RATIO} and {MAX_ASPECT_RATIO})"
        
        # Resize if needed
        if img.size != TARGET_SIZE:
            img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed (for PNG with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Save with unique filename
        ext = image_file.filename.split('.')[-1].lower()
        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            return None, "Avatar must be JPG, PNG, GIF, or WebP format"
        
        filename = f"{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(AVATAR_DIR, filename)
        img.save(filepath, quality=85, optimize=True)
        
        return f"/static/avatars/{filename}", None
        
    except Exception as e:
        return None, f"Failed to process avatar: {str(e)}"

async def increment_user_rep(db: AsyncSession, user_id: int, amount: int):
    stmt = update(User).where(User.id == user_id).values(reputation=User.reputation + amount)
    await db.execute(stmt)

def calculate_badges(user: User, script_count: int) -> list:
    badges = []
    
    # Basic Badge
    badges.append({"name": "Member", "icon": "😊", "color": "bg-gray-600"})
    
    # Role Badge
    if user.is_admin:
        badges.append({"name": "Admin", "icon": "🛡️", "color": "bg-red-600"})
        
    # Script Badges
    if script_count >= 1:
        badges.append({"name": "Scripter", "icon": "📜", "color": "bg-blue-600"})
    if script_count >= 5:
        badges.append({"name": "Master Scripter", "icon": "🧙‍♂️", "color": "bg-purple-600"})
        
    # Reputation Badges
    if user.reputation >= 10:
        badges.append({"name": "Rising Star", "icon": "⭐", "color": "bg-yellow-500"})
    if user.reputation >= 50:
        badges.append({"name": "Legend", "icon": "👑", "color": "bg-yellow-600"})
        
    return badges
