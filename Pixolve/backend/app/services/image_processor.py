"""Image processor module for converting images to pixel art.
Handles image loading, processing, and conversion logic.
"""

from typing import Tuple, Optional
import os
from PIL import Image, ImageFilter, ImageEnhance


class ImageProcessor:
    """Handles image processing operations for pixel art conversion."""
    
    def __init__(self):
        self.original_image: Optional[Image.Image] = None
        self.processed_image: Optional[Image.Image] = None
        self.has_transparency: bool = False
        self.background_color: Tuple[int, int, int] = (0, 0, 0)  # Black default for game
    
    def load_image(self, file_path: str) -> bool:
        """
        Load an image from file path with transparency support.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                return False
            self.original_image = Image.open(file_path)
            
            # Check if image has transparency
            self.has_transparency = self._has_transparency(self.original_image)
            
            # Convert to appropriate mode
            if self.has_transparency:
                # Keep transparency information in RGBA mode
                if self.original_image.mode != 'RGBA':
                    self.original_image = self.original_image.convert('RGBA')
            else:
                # Convert to RGB for non-transparent images
                if self.original_image.mode != 'RGB':
                    self.original_image = self.original_image.convert('RGB')
            
            return True
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
    
    def _has_transparency(self, image: Image.Image) -> bool:
        """
        Check if an image has transparency.
        
        Args:
            image: PIL Image object
            
        Returns:
            bool: True if image has transparency, False otherwise
        """
        return (
            image.mode in ('RGBA', 'LA') or
            (image.mode == 'P' and 'transparency' in image.info)
        )
    
    def _composite_with_background(self, image: Image.Image, background_color: Tuple[int, int, int]) -> Image.Image:
        """
        Composite RGBA image with a background color.
        
        Args:
            image: RGBA PIL Image object
            background_color: RGB tuple for background
            
        Returns:
            RGB PIL Image with background applied
        """
        # Create background
        background = Image.new('RGB', image.size, background_color)
        
        # Composite image onto background
        if image.mode == 'RGBA':
            background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
        else:
            background.paste(image)
        
        return background
    
    def quantize_colors_with_alpha(self, image: Image.Image, num_colors: int) -> Image.Image:
        """
        Quantize colors while preserving transparency.
        
        Args:
            image: PIL Image object (RGBA or RGB)
            num_colors: Number of colors to reduce to
            
        Returns:
            Color-quantized PIL Image with same mode as input
        """
        if image.mode == 'RGBA':
            # Separate RGB and alpha channels
            rgb_part = image.convert('RGB')
            alpha_part = image.split()[3]
            
            # Quantize RGB part
            quantized_rgb = rgb_part.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)
            quantized_rgb = quantized_rgb.convert('RGB')
            
            # Recombine with alpha
            quantized_rgba = Image.new('RGBA', image.size)
            quantized_rgba.paste(quantized_rgb)
            quantized_rgba.putalpha(alpha_part)
            
            return quantized_rgba
        else:
            # Standard quantization for RGB
            quantized = image.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)
            return quantized.convert('RGB')
    
    def apply_pixelation(self, pixel_size: int, num_colors: int = 16, 
                        contrast: float = 1.0, saturation: float = 1.0, 
                        preserve_transparency: bool = True) -> bool:
        """
        Apply pixelation effect to the loaded image with transparency support.
        
        Args:
            pixel_size: Size of each pixel block
            num_colors: Number of colors to use (default 16 for retro look)
            contrast: Contrast adjustment (1.0 = no change)
            saturation: Saturation adjustment (1.0 = no change)
            preserve_transparency: Whether to preserve transparency
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.original_image is None:
            return False
        
        try:
            # Start with original image
            img = self.original_image.copy()
            
            # Handle transparency
            if self.has_transparency and not preserve_transparency:
                # Composite with background if not preserving transparency
                img = self._composite_with_background(img, self.background_color)
            
            # Apply enhancements (works on both RGB and RGBA)
            if contrast != 1.0:
                if img.mode == 'RGBA':
                    # Apply to RGB channels only
                    rgb_part = Image.new('RGB', img.size)
                    rgb_part.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                    enhancer = ImageEnhance.Contrast(rgb_part)
                    enhanced_rgb = enhancer.enhance(contrast)
                    
                    # Recombine with alpha
                    enhanced = Image.new('RGBA', img.size)
                    enhanced.paste(enhanced_rgb)
                    if img.mode == 'RGBA':
                        enhanced.putalpha(img.split()[3])
                    img = enhanced
                else:
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(contrast)
            
            if saturation != 1.0:
                if img.mode == 'RGBA':
                    # Apply to RGB channels only
                    rgb_part = Image.new('RGB', img.size)
                    rgb_part.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                    enhancer = ImageEnhance.Color(rgb_part)
                    enhanced_rgb = enhancer.enhance(saturation)
                    
                    # Recombine with alpha
                    enhanced = Image.new('RGBA', img.size)
                    enhanced.paste(enhanced_rgb)
                    if img.mode == 'RGBA':
                        enhanced.putalpha(img.split()[3])
                    img = enhanced
                else:
                    enhancer = ImageEnhance.Color(img)
                    img = enhancer.enhance(saturation)
            
            # Get original dimensions
            width, height = img.size
            
            # Calculate new dimensions for pixelation
            new_width = width // pixel_size
            new_height = height // pixel_size
            
            if new_width == 0 or new_height == 0:
                return False
            
            # Resize down with nearest neighbor (preserves transparency)
            small_img = img.resize((new_width, new_height), Image.Resampling.NEAREST)
            
            # Quantize colors (with transparency support)
            small_img = self.quantize_colors_with_alpha(small_img, num_colors)
            
            # Resize back up to create pixel blocks
            self.processed_image = small_img.resize((width, height), Image.Resampling.NEAREST)
            
            return True
            
        except Exception as e:
            print(f"Error applying pixelation: {e}")
            return False
    
    def save_image(self, file_path: str, quality: int = 95) -> bool:
        """
        Save the processed image to file.
        
        Args:
            file_path: Output file path
            quality: JPEG quality (1-100)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.processed_image is None:
            return False
        
        try:
            # Determine format from file extension
            file_extension = file_path.lower().split('.')[-1]
            
            if file_extension in ['jpg', 'jpeg']:
                self.processed_image.save(file_path, 'JPEG', quality=quality, optimize=True)
            elif file_extension == 'png':
                self.processed_image.save(file_path, 'PNG', optimize=True)
            elif file_extension == 'bmp':
                self.processed_image.save(file_path, 'BMP')
            else:
                # Default to PNG
                self.processed_image.save(file_path, 'PNG', optimize=True)
            
            return True
            
        except Exception as e:
            print(f"Error saving image: {e}")
            return False
    
    def get_processed_image(self) -> Optional[Image.Image]:
        """Get the processed image."""
        return self.processed_image
    
    def get_original_image(self) -> Optional[Image.Image]:
        """Get the original image."""
        return self.original_image
    
    def set_background_color(self, color: Tuple[int, int, int]):
        """Set the background color for transparency compositing.
        
        Args:
            color: RGB tuple (r, g, b) with values 0-255
        """
        self.background_color = color
