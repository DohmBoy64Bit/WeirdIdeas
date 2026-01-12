from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from ..services import category_service

router = APIRouter()


@router.post("/", status_code=201)
def create_category(payload: dict):
    name = payload.get('name')
    if not name:
        raise HTTPException(status_code=400, detail='name required')
    cat = category_service.create_category(name, payload.get('description'), payload.get('difficulty', 1), payload.get('active', True))
    return cat


@router.get("/")
def list_categories():
    return category_service.list_categories()


@router.get("/{category_id}")
def get_category(category_id: str):
    c = category_service.get_category(category_id)
    if not c:
        raise HTTPException(status_code=404, detail='not found')
    return c


@router.post("/{category_id}/import")
def import_images(category_id: str, folder_path: str):
    try:
        n = category_service.import_images_from_dir(category_id, folder_path)
        return {"imported": n}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{category_id}/upload")
def upload_image(category_id: str, file: UploadFile = File(...)):
    # Accept single file upload and save to data/images
    import os, uuid
    from ..services import category_service
    from ..services.category_service import DATA_DIR
    if category_id not in [c['id'] for c in category_service.list_categories()]:
        raise HTTPException(status_code=404, detail='category not found')
    images_store = os.path.join(DATA_DIR, 'images')
    os.makedirs(images_store, exist_ok=True)
    dst = os.path.join(images_store, f"{uuid.uuid4()}_{file.filename}")
    with open(dst, 'wb') as f:
        f.write(file.file.read())
    rel = os.path.relpath(dst, DATA_DIR)
    category = category_service.get_category(category_id)
    category['images'].append(rel)
    # persist
    category_service.save_categories()
    return {"path": rel}