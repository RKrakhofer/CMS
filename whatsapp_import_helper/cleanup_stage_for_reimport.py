#!/usr/bin/env python3
"""
Bereitet Stage DB für Re-Import vor:
- Löscht alle Artikel mit ID > 1
- Löscht alle Bilder außer 1_*
"""
import sqlite3
from pathlib import Path

DB_PATH = "database/articles.db"
IMAGES_DIR = Path("media/images")

def main():
    print("=" * 80)
    print("Cleanup Stage für Re-Import")
    print("=" * 80)
    print()
    
    # Verbinde mit DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Zähle aktuelle Artikel
    cursor.execute("SELECT COUNT(*) FROM articles WHERE id > 1")
    article_count = cursor.fetchone()[0]
    print(f"📊 {article_count} Artikel mit ID > 1 gefunden")
    
    # Zähle aktuelle Bilder
    cursor.execute("SELECT COUNT(*) FROM images WHERE article_id > 1")
    image_count = cursor.fetchone()[0]
    print(f"🖼️  {image_count} Bild-Einträge mit article_id > 1 gefunden")
    
    # Zähle Bilddateien
    all_images = list(IMAGES_DIR.glob("*.jpg")) + list(IMAGES_DIR.glob("*.png"))
    images_to_delete = [img for img in all_images if not img.name.startswith("1_")]
    print(f"📁 {len(images_to_delete)} Bilddateien (außer 1_*) gefunden")
    print()
    
    # Lösche Artikel
    print("🗑️  Lösche Artikel mit ID > 1...")
    cursor.execute("DELETE FROM articles WHERE id > 1")
    deleted_articles = cursor.rowcount
    print(f"   ✅ {deleted_articles} Artikel gelöscht")
    
    # Lösche Bild-Einträge
    print("🗑️  Lösche Bild-Einträge mit article_id > 1...")
    cursor.execute("DELETE FROM images WHERE article_id > 1")
    deleted_image_entries = cursor.rowcount
    print(f"   ✅ {deleted_image_entries} Bild-Einträge gelöscht")
    
    # Commit DB
    conn.commit()
    conn.close()
    
    # Lösche Bilddateien
    print("🗑️  Lösche Bilddateien (außer 1_*)...")
    deleted_files = 0
    for img_file in images_to_delete:
        img_file.unlink()
        deleted_files += 1
    print(f"   ✅ {deleted_files} Dateien gelöscht")
    
    print()
    print("=" * 80)
    print("Cleanup abgeschlossen!")
    print("=" * 80)
    print("Stage ist bereit für Re-Import")
    print()

if __name__ == '__main__':
    main()
