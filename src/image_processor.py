#!/usr/bin/env python3
"""
Bildverarbeitung für CMS
Fügt Logo/Wasserzeichen zu Bildern hinzu
"""
from PIL import Image
from pathlib import Path
from typing import Tuple, Optional

class ImageProcessor:
    """Verarbeitet Bilder und fügt Wasserzeichen hinzu"""
    
    def __init__(self, logo_path: str = None):
        """
        Args:
            logo_path: Pfad zum Logo-Bild (PNG mit Transparenz empfohlen)
        """
        self.logo_path = Path(logo_path) if logo_path else None
        self.logo = None
        
        if self.logo_path and self.logo_path.exists():
            self.logo = Image.open(self.logo_path)
    
    def add_watermark(self, 
                     image_path: str,
                     output_path: str = None,
                     position: str = "bottom-right",
                     logo_size_ratio: float = 0.15,
                     opacity: int = 255,
                     margin: int = 20,
                     circular: bool = True) -> str:
        """
        Fügt Wasserzeichen/Logo zu einem Bild hinzu
        
        Args:
            image_path: Pfad zum Originalbild
            output_path: Pfad für Ausgabebild (None = überschreibt Original)
            position: Position des Logos ("bottom-right", "bottom-left", 
                     "top-right", "top-left", "center")
            logo_size_ratio: Logo-Größe relativ zur Bildbreite (0.0-1.0)
            opacity: Transparenz des Logos (0-255, 255 = voll sichtbar)
            margin: Abstand vom Rand in Pixeln
            circular: Logo kreisförmig zuschneiden
        
        Returns:
            Pfad zum bearbeiteten Bild
        """
        if not self.logo:
            raise ValueError("Kein Logo geladen! Bitte logo_path beim Init angeben.")
        
        # Bild öffnen
        image = Image.open(image_path)
        
        # Logo-Größe berechnen (relativ zur Bildbreite, halbiert)
        logo_width = int(image.width * logo_size_ratio * 0.5)  # Halbiert!
        logo_height = logo_width  # Quadratisch für Kreis
        
        # Logo skalieren
        logo_resized = self.logo.copy()
        logo_resized = logo_resized.resize((logo_width, logo_height), Image.LANCZOS)
        
        # Kreisförmig zuschneiden wenn gewünscht
        if circular:
            logo_resized = self._make_circular(logo_resized)
        
        # Transparenz anpassen wenn gewünscht
        if opacity < 255 and logo_resized.mode in ('RGBA', 'LA'):
            alpha = logo_resized.split()[3]
            alpha = alpha.point(lambda p: int(p * (opacity / 255)))
            logo_resized.putalpha(alpha)
        
        # Position berechnen
        x, y = self._calculate_position(
            image.size, 
            (logo_width, logo_height), 
            position, 
            margin
        )
        
        # Bild muss RGBA sein für Transparenz
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Logo einfügen
        if logo_resized.mode == 'RGBA':
            image.paste(logo_resized, (x, y), logo_resized)
        else:
            image.paste(logo_resized, (x, y))
        
        # Speichern
        if output_path is None:
            output_path = image_path
        
        # Zurück zu RGB wenn Original kein Alpha hatte
        original_mode = Image.open(image_path).mode
        if original_mode == 'RGB':
            image = image.convert('RGB')
        
        image.save(output_path, quality=95)
        
        return output_path
    
    def _make_circular(self, image):
        """
        Macht ein Bild kreisförmig mit transparentem Hintergrund
        
        Args:
            image: PIL Image
            
        Returns:
            Kreisförmiges PIL Image mit RGBA
        """
        # Zu RGBA konvertieren
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Quadratische Größe sicherstellen
        size = min(image.size)
        
        # Zentriert auf quadratisch zuschneiden
        left = (image.width - size) // 2
        top = (image.height - size) // 2
        right = left + size
        bottom = top + size
        image = image.crop((left, top, right, bottom))
        
        # Alpha-Maske erstellen (Kreis)
        from PIL import ImageDraw
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        
        # Alpha-Kanal anwenden
        output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        output.paste(image, (0, 0))
        output.putalpha(mask)
        
        return output
    
    def _calculate_position(self, 
                           image_size: Tuple[int, int],
                           logo_size: Tuple[int, int],
                           position: str,
                           margin: int) -> Tuple[int, int]:
        """Berechnet die Logo-Position"""
        img_width, img_height = image_size
        logo_width, logo_height = logo_size
        
        positions = {
            "bottom-right": (
                img_width - logo_width - margin,
                img_height - logo_height - margin
            ),
            "bottom-left": (
                margin,
                img_height - logo_height - margin
            ),
            "top-right": (
                img_width - logo_width - margin,
                margin
            ),
            "top-left": (
                margin,
                margin
            ),
            "center": (
                (img_width - logo_width) // 2,
                (img_height - logo_height) // 2
            )
        }
        
        return positions.get(position, positions["bottom-right"])
    
    def resize_image(self,
                    image_path: str,
                    output_path: str = None,
                    max_width: int = None,
                    max_height: int = None,
                    quality: int = 95) -> str:
        """
        Skaliert ein Bild unter Beibehaltung des Seitenverhältnisses
        
        Args:
            image_path: Pfad zum Originalbild
            output_path: Pfad für Ausgabebild
            max_width: Maximale Breite
            max_height: Maximale Höhe
            quality: JPEG-Qualität (1-100)
        
        Returns:
            Pfad zum skalierten Bild
        """
        image = Image.open(image_path)
        
        if max_width or max_height:
            image.thumbnail((max_width or 10000, max_height or 10000), Image.LANCZOS)
        
        if output_path is None:
            output_path = image_path
        
        image.save(output_path, quality=quality, optimize=True)
        
        return output_path
    
    def create_thumbnail(self,
                        image_path: str,
                        output_path: str,
                        size: Tuple[int, int] = (300, 300)) -> str:
        """
        Erstellt ein Thumbnail
        
        Args:
            image_path: Pfad zum Originalbild
            output_path: Pfad für Thumbnail
            size: Thumbnail-Größe (Breite, Höhe)
        
        Returns:
            Pfad zum Thumbnail
        """
        image = Image.open(image_path)
        image.thumbnail(size, Image.LANCZOS)
        image.save(output_path, quality=85, optimize=True)
        
        return output_path


def main():
    """Beispiel-Nutzung"""
    
    # Beispiel: Logo auf Bild platzieren
    # processor = ImageProcessor(logo_path="path/to/logo.png")
    # processor.add_watermark(
    #     image_path="path/to/image.jpg",
    #     output_path="path/to/output.jpg",
    #     position="bottom-right",
    #     logo_size_ratio=0.15,  # Logo = 15% der Bildbreite
    #     margin=20
    # )
    
    print("ImageProcessor bereit!")
    print("\nBeispiel-Nutzung:")
    print("  from src.image_processor import ImageProcessor")
    print("  processor = ImageProcessor('logo.png')")
    print("  processor.add_watermark('bild.jpg', position='bottom-right', logo_size_ratio=0.15)")

if __name__ == "__main__":
    main()
