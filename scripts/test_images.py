#!/usr/bin/env python3
"""
Test-Script für Bildverarbeitung
Demonstriert Logo-Overlay-Funktionalität
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from image_processor import ImageProcessor

def test_watermark():
    """Testet das Wasserzeichen-Feature"""
    
    print("=== FakeDaily Bildverarbeitung Test ===\n")
    
    # Hinweis für Benutzer
    print("Für den Test benötigst du:")
    print("  1. Ein Test-Bild (z.B. test_image.jpg)")
    print("  2. Ein Logo (z.B. logo.png - am besten mit Transparenz)")
    print("\nBeispiel-Code:\n")
    
    example_code = """
from src.image_processor import ImageProcessor

# ImageProcessor initialisieren
processor = ImageProcessor(logo_path="logo.png")

# Logo auf Bild platzieren
processor.add_watermark(
    image_path="test_image.jpg",
    output_path="output_with_logo.jpg",
    position="bottom-right",      # Optionen: bottom-right, bottom-left, 
                                  #          top-right, top-left, center
    logo_size_ratio=0.15,         # Logo = 15% der Bildbreite
    opacity=255,                  # 0-255 (255 = voll sichtbar)
    margin=20                     # Abstand vom Rand in Pixeln
)

# Oder: Bild verkleinern
processor.resize_image(
    image_path="large_image.jpg",
    output_path="resized.jpg",
    max_width=1920,
    max_height=1080
)

# Oder: Thumbnail erstellen
processor.create_thumbnail(
    image_path="image.jpg",
    output_path="thumb.jpg",
    size=(300, 300)
)
"""
    
    print(example_code)
    
    # Interaktiver Test wenn Dateien vorhanden
    test_image = Path("test_image.jpg")
    logo_file = Path("logo.png")
    
    if test_image.exists() and logo_file.exists():
        print("\n✓ Test-Dateien gefunden! Führe Test aus...\n")
        
        processor = ImageProcessor(logo_path=str(logo_file))
        
        output_file = processor.add_watermark(
            image_path=str(test_image),
            output_path="output_with_logo.jpg",
            position="bottom-right",
            logo_size_ratio=0.15,
            margin=20
        )
        
        print(f"✓ Bild mit Logo erstellt: {output_file}")
    else:
        print(f"\n⚠ Für automatischen Test bitte erstellen:")
        if not test_image.exists():
            print(f"  - {test_image}")
        if not logo_file.exists():
            print(f"  - {logo_file}")

if __name__ == "__main__":
    test_watermark()
