#!/usr/bin/env python3
"""
Importiert einen einzelnen Artikel in die Datenbank
"""
import sys
import shutil
from pathlib import Path

# Pfad zum src-Ordner hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db_manager import DatabaseManager
from image_processor import ImageProcessor

def import_article(title: str, content: str, author: str = None,
                  published: bool = False, tags: list = None,
                  image_paths: list = None, logo_path: str = None,
                  add_watermark: bool = False, watermark_position: str = "bottom-right"):
    """
    Importiert einen Artikel mit optionalen Bildern
    
    Args:
        title: Artikel-Titel
        content: Markdown-Inhalt
        author: Autor
        published: Veröffentlicht?
        tags: Liste von Tags
        image_paths: Liste von Bild-Pfaden zum Importieren
        logo_path: Pfad zum Logo für Wasserzeichen
        add_watermark: Soll Wasserzeichen hinzugefügt werden?
        watermark_position: Position des Wasserzeichens
    """
    db = DatabaseManager()
    
    # ImageProcessor initialisieren wenn Wasserzeichen gewünscht
    img_processor = None
    if add_watermark and logo_path:
        img_processor = ImageProcessor(logo_path=logo_path)
    
    # Artikel hinzufügen
    article_id = db.add_article(
        title=title,
        content=content,
        author=author,
        published=published,
        tags=tags
    )
    
    print(f"✓ Artikel erstellt (ID: {article_id}): {title}")
    
    # Bilder importieren
    if image_paths:
        media_dir = Path(__file__).parent.parent / "media" / "images"
        media_dir.mkdir(parents=True, exist_ok=True)
        
        for img_path in image_paths:
            img_path = Path(img_path)
            if not img_path.exists():
                print(f"✗ Bild nicht gefunden: {img_path}")
                continue
            
            # Bild ins media-Verzeichnis kopieren
            new_filename = f"{article_id}_{img_path.name}"
            new_path = media_dir / new_filename
            shutil.copy2(img_path, new_path)
            
            # Wasserzeichen hinzufügen wenn gewünscht
            if img_processor:
                try:
                    img_processor.add_watermark(
                        image_path=str(new_path),
                        output_path=str(new_path),
                        position=watermark_position,
                        logo_size_ratio=0.15,
                        margin=20
                    )
                    print(f"  ✓ Bild mit Logo importiert: {new_filename}")
                except Exception as e:
                    print(f"  ⚠ Warnung: Logo konnte nicht hinzugefügt werden: {e}")
                    print(f"  ✓ Bild ohne Logo importiert: {new_filename}")
            else:
                print(f"  ✓ Bild importiert: {new_filename}")
            
            # In DB eintragen
            relative_path = f"media/images/{new_filename}"
            db.add_image(
                article_id=article_id,
                filename=new_filename,
                filepath=relative_path
            )
    
    return article_id

def main():
    """Beispiel-Import"""
    
    # Beispiel-Markdown-Content
    content = """# Willkommen bei FakeDaily

Dies ist ein **Beispiel-Artikel** mit Markdown-Formatierung.

## Features

- Markdown-Unterstützung
- Bild-Verwaltung
- Tags
- Veröffentlichungs-Status

### Code-Beispiel

```python
print("Hello, FakeDaily!")
```

Mehr Informationen folgen...
"""
    
    article_id = import_article(
        title="Erster Artikel",
        content=content,
        author="FakeDaily Team",
        published=True,
        tags=["test", "markdown", "beispiel"]
    )
    
    print(f"\n✓ Import abgeschlossen! Artikel-ID: {article_id}")

if __name__ == "__main__":
    main()
