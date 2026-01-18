#!/usr/bin/env python3
"""
Korrigiert die created_at Timestamps der importierten Artikel
"""
import re
import requests
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from db_manager import DatabaseManager

# Konfiguration
API_BASE = "http://stage:5001/cms/admin/api"
HISTORY_FILE = "/home/richard/workspaces/FakeDaily/Artikel_History.md"
DB_PATH = Path(__file__).parent / "database" / "articles.db"

def parse_whatsapp_timestamp(timestamp_str):
    """Konvertiert WhatsApp Timestamp (DD.MM.YY, HH:MM) zu ISO format"""
    try:
        dt = datetime.strptime(timestamp_str, "%d.%m.%y, %H:%M")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Fehler beim Parsen des Timestamps '{timestamp_str}': {e}")
        return None

def parse_history_articles():
    """Parst die Artikel_History.md"""
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    articles = {}
    
    # Pattern für jeden Artikel
    pattern = r'\*\*Titel:\*\* (.*?)\n\n\*\*Datum/Uhrzeit:\*\* (.*?)\n'
    
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        title = match.group(1).strip()
        timestamp = match.group(2).strip()
        created_at = parse_whatsapp_timestamp(timestamp)
        
        if created_at:
            # Bereinige Titel für Matching
            title_clean = re.sub(r'\*', '', title).strip()
            articles[title_clean.lower()] = {
                'title': title,
                'timestamp': timestamp,
                'created_at': created_at
            }
    
    return articles

def main():
    print("=" * 80)
    print("Korrektur der created_at Timestamps")
    print("=" * 80)
    print()
    
    # Parse History
    print("📖 Parse Artikel_History.md...")
    history_articles = parse_history_articles()
    print(f"   {len(history_articles)} Artikel mit Timestamps gefunden")
    print()
    
    # Hole alle Artikel aus DB
    print("📥 Lade Artikel aus Datenbank...")
    db = DatabaseManager(str(DB_PATH))
    db_articles = db.get_all_articles()
    print(f"   {len(db_articles)} Artikel in DB gefunden")
    print()
    
    # Aktualisiere Timestamps
    print("🔄 Aktualisiere Timestamps...")
    print()
    
    updated_count = 0
    not_found_count = 0
    
    for db_art in db_articles:
        title_clean = re.sub(r'\*', '', db_art['title']).strip().lower()
        
        # Suche in History
        if title_clean in history_articles:
            hist_art = history_articles[title_clean]
            
            # Prüfe ob Timestamp unterschiedlich ist
            current_created_at = db_art['created_at']
            correct_created_at = hist_art['created_at']
            
            if current_created_at != correct_created_at:
                print(f"  🔧 Aktualisiere: {db_art['title'][:70]}")
                print(f"     Alt: {current_created_at}")
                print(f"     Neu: {correct_created_at}")
                
                # Update
                db.update_article(
                    db_art['id'],
                    created_at=correct_created_at
                )
                
                updated_count += 1
            else:
                print(f"  ✓  OK: {db_art['title'][:70]}")
        else:
            print(f"  ⚠️  Nicht in History gefunden: {db_art['title'][:70]}")
            not_found_count += 1
    
    # Zusammenfassung
    print()
    print("=" * 80)
    print("Korrektur abgeschlossen!")
    print("=" * 80)
    print(f"✅ Aktualisiert: {updated_count}")
    print(f"⏭️  Bereits korrekt: {len(db_articles) - updated_count - not_found_count}")
    print(f"⚠️  Nicht in History: {not_found_count}")
    print()

if __name__ == '__main__':
    main()
