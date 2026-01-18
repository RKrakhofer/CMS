#!/usr/bin/env python3
"""
Lädt alle Bilder aus Artikel_History.md über API zu Stage hoch.
Matched Artikel nach Titel und uploaded entsprechende Bilder vom NAS.
"""
import re
import requests
import shutil
from pathlib import Path
from datetime import datetime

# Konfiguration
API_BASE = "http://stage:5001/cms/admin/api"
HISTORY_FILE = "/home/richard/workspaces/FakeDaily/Artikel_History.md"
IMAGE_SOURCE_DIR = "/mnt/nas-synology-1/home/Downloads/WhatsApp-Chat mit +43 676 3518170"
TEMP_DIR = Path("/tmp/fakedaily_images")
TEMP_DIR.mkdir(exist_ok=True)

def parse_history_articles():
    """Parst Artikel_History.md"""
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    articles = []
    pattern = r'## Artikel \d+\n\n\*\*Titel:\*\* (.*?)\n\n\*\*Datum/Uhrzeit:\*\* (.*?)\n\n\*\*Bild:\*\* `(.*?)`\n\n\*\*Bildpfad:\*\* `(.*?)`'
    
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        title = match.group(1).strip()
        timestamp_str = match.group(2).strip()
        image_name = match.group(3).strip()
        image_path = match.group(4).strip()
        
        # Normalisiere Titel
        title_normalized = re.sub(r'\*\*([^\*]+)\*\*', r'\1', title)
        title_normalized = re.sub(r'\*([^\*]+)\*', r'\1', title_normalized).strip()
        
        # Parse Timestamp
        try:
            dt = datetime.strptime(timestamp_str, '%d.%m.%y, %H:%M')
            timestamp_iso = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            timestamp_iso = None
        
        articles.append({
            'title': title_normalized,
            'timestamp': timestamp_iso,
            'image_name': image_name,
            'image_path': image_path
        })
    
    return articles

def get_stage_articles():
    """Holt alle Artikel von Stage"""
    response = requests.get(f"{API_BASE}/export/articles")
    data = response.json()
    return data['articles']

def match_article(stage_article, history_articles):
    """Matched Stage-Artikel zu History"""
    title = stage_article['title']
    created_at = stage_article.get('created_at', '')
    
    # Normalisiere Titel
    title_normalized = re.sub(r'\*\*([^\*]+)\*\*', r'\1', title)
    title_normalized = re.sub(r'\*([^\*]+)\*', r'\1', title_normalized).strip()
    
    # Exakter Match über Titel + Zeitstempel
    if created_at:
        for hist in history_articles:
            if hist['title'] == title_normalized and hist['timestamp']:
                if created_at[:16] == hist['timestamp'][:16]:
                    return hist
    
    # Exakter Titel-Match
    for hist in history_articles:
        if hist['title'] == title_normalized:
            return hist
    
    # Fuzzy Match (erste 80 Zeichen)
    title_short = title_normalized[:80]
    for hist in history_articles:
        if hist['title'][:80] == title_short:
            return hist
    
    return None

def upload_image(article_id, image_path, image_name):
    """Lädt ein Bild über API hoch"""
    source_image = Path(image_path)
    
    if not source_image.exists():
        return False, f"Datei nicht gefunden: {image_path}"
    
    try:
        # Kopiere Bild zu Temp-Verzeichnis
        temp_image = TEMP_DIR / image_name
        shutil.copy(source_image, temp_image)
        
        # Upload via API
        with open(temp_image, 'rb') as img_file:
            files = {'images': (image_name, img_file, 'image/jpeg')}
            data = {'add_watermark': 'true'}
            response = requests.post(
                f"{API_BASE}/upload/images/{article_id}",
                files=files,
                data=data
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                # Lösche temporäres Bild
                temp_image.unlink(missing_ok=True)
                return True, "OK"
            else:
                return False, result.get('error', 'Unknown error')
    
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 80)
    print("Upload aller Bilder zu Stage")
    print("=" * 80)
    print()
    
    # Parse History
    print("📖 Parse Artikel_History.md...")
    history_articles = parse_history_articles()
    print(f"   {len(history_articles)} Artikel in History gefunden")
    print()
    
    # Hole Stage-Artikel
    print("📥 Lade Artikel von Stage...")
    stage_articles = get_stage_articles()
    print(f"   {len(stage_articles)} Artikel auf Stage gefunden")
    print()
    
    print("🚀 Starte Bild-Upload...")
    print()
    
    uploaded = 0
    skipped = 0
    not_found = 0
    errors = 0
    
    for i, article in enumerate(stage_articles, 1):
        article_id = article['id']
        title = article['title']
        has_images = article.get('images') and len(article['images']) > 0
        
        # Überspringe wenn bereits Bilder vorhanden
        if has_images:
            continue
        
        # Finde History-Match
        hist = match_article(article, history_articles)
        
        if not hist:
            not_found += 1
            continue
        
        print(f"[{i}/{len(stage_articles)}] ID {article_id}: {title[:60]}...")
        
        # Upload Bild
        success, message = upload_image(article_id, hist['image_path'], hist['image_name'])
        
        if success:
            print(f"  ✅ Bild hochgeladen: {hist['image_name']}")
            uploaded += 1
        else:
            print(f"  ❌ Fehler: {message}")
            errors += 1
        
        print()
    
    # Zusammenfassung
    print("=" * 80)
    print("Upload abgeschlossen!")
    print("=" * 80)
    print(f"✅ Hochgeladen: {uploaded}")
    print(f"⏭️  Bereits vorhanden: {skipped}")
    print(f"⚠️  Kein History-Match: {not_found}")
    print(f"❌ Fehler: {errors}")
    print()

if __name__ == '__main__':
    main()
