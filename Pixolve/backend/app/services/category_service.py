"""Category service: manage categories and images for Pixolve.
Simple file-backed implementation: categories stored in-memory with optional persistence to JSON in `backend/data/categories.json`.
Importing images copies/records paths from a directory.
"""
import os
import json
import uuid
from typing import Dict, List, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
CATEGORIES_FILE = os.path.join(DATA_DIR, 'categories.json')

CATEGORIES: Dict[str, dict] = {}


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_categories():
    _ensure_data_dir()
    if os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            CATEGORIES.clear()
            for c in data:
                CATEGORIES[c['id']] = c


def save_categories():
    _ensure_data_dir()
    with open(CATEGORIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(CATEGORIES.values()), f, indent=2)


def create_category(name: str, description: Optional[str] = None, difficulty: int = 1, active: bool = True) -> dict:
    """Create a new category. Raises ValueError if a category with the same name already exists."""
    # Check for duplicate names (case-insensitive)
    name_lower = name.lower().strip()
    for existing_cat in CATEGORIES.values():
        if existing_cat.get('name', '').lower().strip() == name_lower:
            raise ValueError(f"Category with name '{name}' already exists")
    
    cid = str(uuid.uuid4())
    cat = {"id": cid, "name": name, "description": description, "difficulty": difficulty, "images": [], "active": active}
    CATEGORIES[cid] = cat
    save_categories()
    return cat


def list_categories() -> List[dict]:
    """List all categories, deduplicating by name (keeping the first occurrence of each unique name)."""
    seen_names = set()
    unique_categories = []
    for cat in CATEGORIES.values():
        if cat.get('name') not in seen_names:
            seen_names.add(cat.get('name'))
            unique_categories.append(cat)
    return unique_categories


def get_category(cid: str) -> Optional[dict]:
    return CATEGORIES.get(cid)


def import_images_from_dir(category_id: str, images_dir: str) -> int:
    """Scan `images_dir` for image files (png/jpg) and add to category's images list.
    Returns the number of images added.
    Images are referenced by relative paths under `data/images/`.
    """
    if category_id not in CATEGORIES:
        raise ValueError('category_not_found')
    images_store = os.path.join(DATA_DIR, 'images')
    os.makedirs(images_store, exist_ok=True)

    added = 0
    for fname in os.listdir(images_dir):
        if not fname.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        src = os.path.join(images_dir, fname)
        dst = os.path.join(images_store, f"{uuid.uuid4()}_{fname}")
        with open(src, 'rb') as sf, open(dst, 'wb') as df:
            df.write(sf.read())
        rel = os.path.relpath(dst, DATA_DIR)
        CATEGORIES[category_id]['images'].append(rel)
        added += 1
    save_categories()
    return added


# load categories at import time if present
try:
    load_categories()
except Exception:
    pass