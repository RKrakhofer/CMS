"""
Unit Tests for ImageProcessor
Tests image manipulation: watermarks, resizing, thumbnails
NOTE: ImageProcessor uses logo_path in __init__, not watermark_path in methods
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from PIL import Image, ImageDraw
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.image_processor import ImageProcessor


class TestImageProcessor:
    """Unit tests for ImageProcessor class"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Create temporary directory and test images"""
        # Create temp directory
        self.test_dir = tempfile.mkdtemp()
        self.test_images_dir = Path(self.test_dir) / 'images'
        self.test_images_dir.mkdir()
        
        # Create test images
        self.create_test_image('test_image.jpg', (800, 600), 'RGB')
        self.create_test_image('test_logo.png', (200, 200), 'RGBA')
        
        # Initialize ImageProcessor with logo
        logo_path = str(self.test_images_dir / 'test_logo.png')
        self.processor = ImageProcessor(logo_path=logo_path)
        
        yield
        
        # Cleanup
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_image(self, filename, size, mode):
        """Helper: Create a test image with colored rectangle"""
        img = Image.new(mode, size, color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw colored rectangle for visual reference
        draw.rectangle(
            [(size[0]//4, size[1]//4), (3*size[0]//4, 3*size[1]//4)],
            fill=(0, 0, 255, 255) if mode == 'RGBA' else 'blue',
            outline=(255, 0, 0, 255) if mode == 'RGBA' else 'red',
            width=3
        )
        
        # Save
        img.save(self.test_images_dir / filename)
    
    # ===== add_watermark() Tests =====
    
    def test_add_watermark_basic(self):
        """Test: Add watermark with logo from init"""
        image_path = str(self.test_images_dir / 'test_image.jpg')
        output_path = str(self.test_images_dir / 'watermarked.jpg')
        
        result = self.processor.add_watermark(
            image_path=image_path,
            output_path=output_path
        )
        
        # Verify output exists
        assert Path(result).exists()
        assert Path(output_path).exists()
        
        # Verify it's a valid image
        img = Image.open(output_path)
        assert img.size == (800, 600)
        img.close()
    
    def test_add_watermark_no_logo_fails(self):
        """Test: add_watermark without logo raises error"""
        processor_no_logo = ImageProcessor()  # No logo
        image_path = str(self.test_images_dir / 'test_image.jpg')
        
        with pytest.raises(ValueError, match="Kein Logo geladen"):
            processor_no_logo.add_watermark(
                image_path=image_path,
                output_path=str(self.test_images_dir / 'out.jpg')
            )
    
    def test_add_watermark_positions(self):
        """Test: Different watermark positions"""
        image_path = str(self.test_images_dir / 'test_image.jpg')
        
        for position in ['bottom-right', 'bottom-left', 'top-right', 'top-left', 'center']:
            output_path = str(self.test_images_dir / f'watermarked_{position}.jpg')
            self.processor.add_watermark(
                image_path=image_path,
                output_path=output_path,
                position=position
            )
            assert Path(output_path).exists()
    
    def test_add_watermark_opacity(self):
        """Test: Watermark with different opacity"""
        image_path = str(self.test_images_dir / 'test_image.jpg')
        
        for opacity in [255, 200, 128, 50]:
            output_path = str(self.test_images_dir / f'watermarked_opacity_{opacity}.jpg')
            self.processor.add_watermark(
                image_path=image_path,
                output_path=output_path,
                opacity=opacity
            )
            assert Path(output_path).exists()
    
    def test_add_watermark_size_ratio(self):
        """Test: Different logo size ratios"""
        image_path = str(self.test_images_dir / 'test_image.jpg')
        
        for ratio in [0.1, 0.2, 0.3]:
            output_path = str(self.test_images_dir / f'watermarked_ratio_{int(ratio*100)}.jpg')
            self.processor.add_watermark(
                image_path=image_path,
                output_path=output_path,
                logo_size_ratio=ratio
            )
            assert Path(output_path).exists()
    
    def test_add_watermark_circular_vs_square(self):
        """Test: Circular vs square logo"""
        image_path = str(self.test_images_dir / 'test_image.jpg')
        
        # Circular
        output_circular = str(self.test_images_dir / 'watermarked_circular.jpg')
        self.processor.add_watermark(
            image_path=image_path,
            output_path=output_circular,
            circular=True
        )
        assert Path(output_circular).exists()
        
        # Square
        output_square = str(self.test_images_dir / 'watermarked_square.jpg')
        self.processor.add_watermark(
            image_path=image_path,
            output_path=output_square,
            circular=False
        )
        assert Path(output_square).exists()
    
    # ===== Edge Cases & Error Handling =====
    
    def test_add_watermark_nonexistent_image(self):
        """Test: add_watermark with nonexistent image raises error"""
        with pytest.raises(Exception):  # FileNotFoundError or similar
            self.processor.add_watermark(
                image_path='nonexistent.jpg',
                output_path='output.jpg'
            )


if __name__ == '__main__':
    print("ImageProcessor Unit Tests")
    print("-" * 70)
    pytest.main([__file__, '-v', '--tb=short'])
