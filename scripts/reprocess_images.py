#!/usr/bin/env python3
"""
Verarbeitet alle Bilder in der Datenbank neu mit aktuellem Logo
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db_manager import DatabaseManager
from image_processor import ImageProcessor

def reprocess_all_images(logo_path: str):
    """
    Verarbeitet alle Bilder neu mit Logo
    
    Args:
        logo_path: Pfad zum Logo
    """
    db = DatabaseManager()
    processor = ImageProcessor(logo_path=logo_path)
    
    base_dir = Path(__file__).parent.parent
    
    # Alle Bilder aus DB holen
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filepath, article_id FROM images")
    images = cursor.fetchall()
    conn.close()
    
    if not images:
        print("Keine Bilder gefunden.")
        return
    
    print(f"Gefunden: {len(images)} Bild(er)\n")
    
    processed = 0
    errors = 0
    
    for image in images:
        image_id = image['id']
        filepath = image['filepath']
        article_id = image['article_id']
        
        full_path = base_dir / filepath
        
        if not full_path.exists():
            print(f"✗ Bild nicht gefunden: {filepath}")
            errors += 1
            continue
        
        try:
            # Logo hinzufügen (überschreibt)
            processor.add_watermark(
                image_path=str(full_path),
                output_path=str(full_path),
                position="bottom-right",
                logo_size_ratio=0.15,
                margin=20,
                circular=True
            )
            print(f"✓ Verarbeitet: {filepath} (Artikel {article_id})")
            processed += 1
        except Exception as e:
            print(f"✗ Fehler bei {filepath}: {e}")
            errors += 1
    
    print(f"\n{'='*60}")
    print(f"Fertig!")
    print(f"  Erfolgreich: {processed}")
    print(f"  Fehler: {errors}")
    print(f"{'='*60}")

def main():
    import sys
    
    # Check für --yes Flag
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv
    
    logo_path = Path(__file__).parent.parent / "logo.png"
    
    if not logo_path.exists():
        print(f"✗ Logo nicht gefunden: {logo_path}")
        print("\nBitte lege eine logo.png im Projektordner ab:")
        print(f"  {Path(__file__).parent.parent}")
        return
    
    print("="*60)
    print("🔄 Bilder neu verarbeiten")
    print("="*60)
    print(f"\nLogo: {logo_path}")
    print("\n⚠ ACHTUNG: Dieser Vorgang überschreibt alle Bilder!")
    
    if auto_confirm:
        print("\nAuto-confirm aktiviert, starte Verarbeitung...\n")
        reprocess_all_images(str(logo_path))
    else:
        confirm = input("\nFortfahren? (ja/nein): ").strip().lower()
        
        if confirm in ['ja', 'j', 'yes', 'y']:
            print("\nStarte Verarbeitung...\n")
            reprocess_all_images(str(logo_path))
        else:
            print("Abgebrochen.")

if __name__ == "__main__":
    main()
