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


@router.delete("/{category_id}")
def delete_category(category_id: str):
    """Delete a category."""
    deleted = category_service.delete_category(category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='category not found')
    return {"deleted": True}


@router.put("/{category_id}")
def update_category(category_id: str, payload: dict):
    """Update a category."""
    try:
        updated = category_service.update_category(
            category_id,
            name=payload.get('name'),
            description=payload.get('description'),
            difficulty=payload.get('difficulty'),
            active=payload.get('active')
        )
        if not updated:
            raise HTTPException(status_code=404, detail='category not found')
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{category_id}/images/{image_path:path}")
def delete_image_from_category(category_id: str, image_path: str):
    """Delete an image from a category."""
    deleted = category_service.remove_image_from_category(category_id, image_path)
    if not deleted:
        raise HTTPException(status_code=404, detail='Image not found in category')
    return {"deleted": True, "image_path": image_path}


@router.get("/images/pixelated")
def get_pixelated_image(image_path: str, pixel_size: int = 32, num_colors: int = 16):
    """
    Get a pixelated version of an image.
    
    Query params:
        image_path: Relative path to image (e.g., 'images/abc123_photo.jpg')
        pixel_size: Size of pixel blocks (default 32)
        num_colors: Number of colors to quantize to (default 16)
    """
    from fastapi.responses import StreamingResponse
    from ..services.image_processor import ImageProcessor
    from ..services.category_service import DATA_DIR
    import os
    import io
    
    # Construct full path - image_path is relative to DATA_DIR
    full_path = os.path.join(DATA_DIR, image_path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail='Image not found')
    
    try:
        # Load and process image
        processor = ImageProcessor()
        if not processor.load_image(full_path):
            raise HTTPException(status_code=400, detail='Failed to load image')
        
        # Apply pixelation
        if not processor.apply_pixelation(pixel_size=pixel_size, num_colors=num_colors):
            raise HTTPException(status_code=400, detail='Failed to process image')
        
        # Get processed image
        processed_img = processor.get_processed_image()
        if not processed_img:
            raise HTTPException(status_code=400, detail='No processed image')
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        file_ext = os.path.splitext(full_path)[1].lower()
        if file_ext in ['.jpg', '.jpeg']:
            processed_img.save(img_bytes, 'JPEG', quality=90, optimize=True)
            media_type = 'image/jpeg'
        else:
            processed_img.save(img_bytes, 'PNG', optimize=True)
            media_type = 'image/png'
        
        img_bytes.seek(0)
        
        return StreamingResponse(io.BytesIO(img_bytes.read()), media_type=media_type)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Image processing error: {str(e)}')


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
    # Accept single file upload and save to data/images with pixelation processing
    import os, uuid
    from ..services import category_service
    from ..services.category_service import DATA_DIR
    from ..services.image_processor import ImageProcessor
    from PIL import Image
    import io
    
    if category_id not in [c['id'] for c in category_service.list_categories()]:
        raise HTTPException(status_code=404, detail='category not found')
    
    images_store = os.path.join(DATA_DIR, 'images')
    os.makedirs(images_store, exist_ok=True)
    
    # Read uploaded file
    file_content = file.file.read()
    
    # Process image for pixel art effect
    try:
        # Load image from bytes
        img = Image.open(io.BytesIO(file_content))
        
        # Process with pixelation (light pixelation for storage, heavy pixelation happens client-side)
        processor = ImageProcessor()
        processor.original_image = img
        processor.has_transparency = processor._has_transparency(img)
        
        # Apply light pixelation and color quantization for retro look
        if processor.has_transparency:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
        else:
            if img.mode != 'RGB':
                img = img.convert('RGB')
        
        # Light pixelation (2px blocks) and color quantization (16 colors for retro look)
        width, height = img.size
        new_width = max(1, width // 2)
        new_height = max(1, height // 2)
        small_img = img.resize((new_width, new_height), Image.Resampling.NEAREST)
        
        # Quantize to 16 colors for retro pixel art look
        if small_img.mode == 'RGBA':
            rgb_part = small_img.convert('RGB')
            alpha_part = small_img.split()[3]
            quantized_rgb = rgb_part.quantize(colors=16, method=Image.Quantize.MEDIANCUT).convert('RGB')
            quantized_rgba = Image.new('RGBA', small_img.size)
            quantized_rgba.paste(quantized_rgb)
            quantized_rgba.putalpha(alpha_part)
            processed_img = quantized_rgba.resize((width, height), Image.Resampling.NEAREST)
        else:
            quantized = small_img.quantize(colors=16, method=Image.Quantize.MEDIANCUT)
            processed_img = quantized.convert('RGB').resize((width, height), Image.Resampling.NEAREST)
        
        # Save processed image
        file_ext = os.path.splitext(file.filename)[1].lower()
        dst = os.path.join(images_store, f"{uuid.uuid4()}_{file.filename}")
        if file_ext in ['.jpg', '.jpeg']:
            processed_img.save(dst, 'JPEG', quality=90, optimize=True)
        else:
            processed_img.save(dst, 'PNG', optimize=True)
        
    except Exception as e:
        # Fallback: save original if processing fails
        print(f"Image processing failed, saving original: {e}")
        dst = os.path.join(images_store, f"{uuid.uuid4()}_{file.filename}")
        with open(dst, 'wb') as f:
            f.write(file_content)
    
    rel = os.path.relpath(dst, DATA_DIR)
    category = category_service.get_category(category_id)
    category['images'].append(rel)
    # persist
    category_service.save_categories()
    return {"path": rel}