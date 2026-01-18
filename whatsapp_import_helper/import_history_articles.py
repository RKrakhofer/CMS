#!/usr/bin/env python3
"""
Importiert Artikel aus Artikel_History.md in die Datenbank
"""
import re
import json
import requests
from datetime import datetime
from pathlib import Path
import shutil

# Konfiguration
API_BASE = "http://stage:5001/cms/admin/api"
HISTORY_FILE = "/home/richard/workspaces/FakeDaily/Artikel_History.md"
IMAGE_SOURCE_DIR = "/mnt/nas-synology-1/home/Downloads/WhatsApp-Chat mit +43 676 3518170"
TEMP_DIR = Path("/tmp/fakedaily_import")
TEMP_DIR.mkdir(exist_ok=True)

# Batch-Limit: Maximale Anzahl Artikel pro Import-Lauf
# Setze auf None für unbegrenzten Import
BATCH_LIMIT = 10

# Tag-Kategorien mit Keywords
TAG_RULES = {
    'Politik Österreich': [
        'österreich', 'wien', 'fpö', 'övp', 'spö', 'neos', 'grüne', 'kickl', 
        'nehammer', 'babler', 'meinl-reisinger', 'bundeskanzler', 'koalition',
        'nationalrat', 'regierung österreich', 'steiermark', 'bruck an der leitha'
    ],
    'Politik Deutschland': [
        'deutschland', 'berlin', 'afd', 'cdu', 'spd', 'grüne deutschland', 
        'scholz', 'merz', 'lindner', 'weidel', 'bundestag', 'bundesregierung'
    ],
    'Politik USA': [
        'trump', 'usa', 'amerika', 'washington', 'weißes haus', 'white house',
        'präsident trump', 'republikaner', 'demokraten'
    ],
    'Politik EU': [
        'eu ', 'europa', 'europäisch', 'brüssel', 'eu-kommission', 'europaparlament',
        'eu-', 'europäische union'
    ],
    'Satire': [
        'fake daily', 'chefredakteur', 'kaiser', 'in eigener sache'
    ],
    'Technologie': [
        'ki ', 'künstliche intelligenz', 'elon musk', 'spacex', 'tesla', 'google',
        'gemini', 'chatgpt', 'technologie', 'software', 'hardware', 'internet',
        'digital', 'computer', 'smartphone'
    ],
    'Wirtschaft': [
        'wirtschaft', 'börse', 'aktien', 'unternehmen', 'firma', 'insolvenz',
        'pleite', 'geld', 'euro', 'inflation', 'steuer', 'benko'
    ],
    'Wissenschaft': [
        'wissenschaft', 'forschung', 'studie', 'experte', 'professor', 'universität',
        'klima', 'erderwärmung', 'physik', 'chemie', 'biologie'
    ],
    'Energie': [
        'energie', 'strom', 'solar', 'photovoltaik', 'windkraft', 'atomkraft',
        'akw', 'kernkraft', 'erneuerbare', 'stromausfall'
    ],
    'Medien': [
        'medien', 'presse', 'zeitung', 'fernsehen', 'orf', 'journalis', 
        'nachrichten', 'fake news'
    ],
    'Gesellschaft': [
        'gesellschaft', 'sozial', 'integration', 'migration', 'ausländer',
        'flüchtling', 'demo', 'protest'
    ],
    'Gesundheit': [
        'gesundheit', 'medizin', 'arzt', 'krankenhaus', 'pflege', 'gesundheitssystem',
        'patient', 'behandlung', 'therapie'
    ],
    'Justiz': [
        'gericht', 'richter', 'justiz', 'anwalt', 'klage', 'urteil', 'prozess',
        'staatsanwalt', 'verhaftung'
    ],
    'Militär': [
        'militär', 'armee', 'soldat', 'waffe', 'krieg', 'ukraine', 'russland',
        'putin', 'nato', 'verteidigung'
    ],
    'Lebensmittel': [
        'lebensmittel', 'essen', 'nahrung', 'schnitzel', 'fleisch', 'laborfleisch',
        'vegetarisch', 'vegan', 'nahrung', 'schokolade', 'restaurant'
    ]
}

def parse_whatsapp_timestamp(timestamp_str):
    """Konvertiert WhatsApp Timestamp (DD.MM.YY, HH:MM) zu ISO format"""
    try:
        # Format: 19.08.24, 14:10
        dt = datetime.strptime(timestamp_str, "%d.%m.%y, %H:%M")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Fehler beim Parsen des Timestamps '{timestamp_str}': {e}")
        return None

def convert_whatsapp_to_markdown(text):
    """Konvertiert WhatsApp-Formatierung zu Markdown
    
    WhatsApp:
    - *text* = fett
    - _text_ = kursiv
    - ~text~ = durchgestrichen
    
    Markdown:
    - **text** = fett
    - *text* = kursiv
    - ~~text~~ = durchgestrichen
    """
    if not text:
        return text
    
    # Schritt 1: Durchgestrichen (~text~ -> ~~text~~)
    text = re.sub(r'~([^~]+)~', r'~~\1~~', text)
    
    # Schritt 2: Fett (*text* -> **text**)
    # Nur umwandeln wenn nicht bereits ** ist
    text = re.sub(r'(?<!\*)\*(?!\*)([^\*]+)\*(?!\*)', r'**\1**', text)
    
    # Schritt 3: Kursiv (_text_ -> *text*)
    text = re.sub(r'_([^_]+)_', r'*\1*', text)
    
    return text

def remove_formatting(text):
    """Entfernt alle Formatierung aus Text
    
    Entfernt sowohl WhatsApp- als auch Markdown-Formatierung.
    Nützlich für Titel in Metadaten, da diese bereits durch CSS formatiert werden.
    """
    if not text:
        return text
    
    # Entferne Markdown-Formatierung
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)  # Markdown fett
    text = re.sub(r'~~([^~]+)~~', r'\1', text)  # Markdown durchgestrichen
    
    # Entferne WhatsApp-Formatierung
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)  # WhatsApp fett
    text = re.sub(r'_([^_]+)_', r'\1', text)  # WhatsApp kursiv
    text = re.sub(r'~([^~]+)~', r'\1', text)  # WhatsApp durchgestrichen
    
    return text.strip()

def generate_tags(title, content):
    """Generiert Tags basierend auf Titel und Inhalt"""
    text_lower = (title + ' ' + content).lower()
    matched_tags = []
    
    for tag, keywords in TAG_RULES.items():
        for keyword in keywords:
            if keyword in text_lower:
                matched_tags.append(tag)
                break  # Ein Match pro Tag-Kategorie reicht
    
    # Entferne Duplikate und sortiere
    return sorted(list(set(matched_tags)))

def remove_title_from_content(title, content):
    """Entfernt Titel aus Content, falls er als erste Zeile vorkommt
    
    Wenn die erste Zeile (ggf. fett formatiert) dem Titel entspricht,
    wird sie aus dem Content entfernt, da der Titel bereits in Metadaten steht.
    """
    if not content or not title:
        return content
    
    # Normalisiere Titel (entferne Formatierung für Vergleich)
    title_normalized = re.sub(r'\*\*([^\*]+)\*\*', r'\1', title)  # Markdown fett
    title_normalized = re.sub(r'\*([^\*]+)\*', r'\1', title_normalized)  # WhatsApp fett
    title_normalized = title_normalized.strip()
    
    # Hole erste Zeile aus Content
    lines = content.split('\n')
    if not lines:
        return content
    
    first_line = lines[0].strip()
    
    # Normalisiere erste Zeile
    first_line_normalized = re.sub(r'\*\*([^\*]+)\*\*', r'\1', first_line)  # Markdown fett
    first_line_normalized = re.sub(r'\*([^\*]+)\*', r'\1', first_line_normalized)  # WhatsApp fett
    first_line_normalized = first_line_normalized.strip()
    
    # Vergleiche normalisierte Versionen
    if first_line_normalized == title_normalized:
        # Entferne erste Zeile (und ggf. folgende Leerzeilen)
        remaining_lines = lines[1:]
        
        # Entferne führende Leerzeilen
        while remaining_lines and not remaining_lines[0].strip():
            remaining_lines = remaining_lines[1:]
        
        return '\n'.join(remaining_lines)
    
    return content

def get_existing_articles():
    """Holt alle existierenden Artikel von der API"""
    try:
        response = requests.get(f"{API_BASE}/export/articles")
        response.raise_for_status()
        data = response.json()
        return data.get('articles', [])
    except Exception as e:
        print(f"Fehler beim Abrufen existierender Artikel: {e}")
        return []

def is_article_in_db(title, db_articles):
    """Prüft ob Artikel bereits in DB ist (Fuzzy Match)"""
    title_clean = re.sub(r'\*', '', title).strip().lower()
    title_words = set(title_clean.split())
    
    for db_art in db_articles:
        db_title_clean = db_art['title'].strip().lower()
        db_words = set(db_title_clean.split())
        
        if title_words and db_words:
            overlap = len(title_words & db_words) / max(len(title_words), len(db_words))
            if overlap > 0.5 or title_clean in db_title_clean or db_title_clean in title_clean:
                return True
    
    return False

def parse_history_articles():
    """Parst die Artikel_History.md und extrahiert alle Artikel"""
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    articles = []
    
    # Pattern für jeden Artikel
    pattern = r'## Artikel \d+\n\n\*\*Titel:\*\* (.*?)\n\n\*\*Datum/Uhrzeit:\*\* (.*?)\n\n\*\*Bild:\*\* `(.*?)`\n\n\*\*Bildpfad:\*\* `(.*?)`\n\n(?:\*\*Text:\*\*\n\n(.*?)\n\n)?---'
    
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        title = match.group(1).strip()
        timestamp = match.group(2).strip()
        image_name = match.group(3).strip()
        image_path = match.group(4).strip()
        text = match.group(5).strip() if match.group(5) else ""
        
        # Kombiniere Titel und Text für Content
        content_text = f"{title}\n\n{text}" if text else title
        
        articles.append({
            'title': title,
            'timestamp': timestamp,
            'image_name': image_name,
            'image_path': image_path,
            'content': content_text
        })
    
    return articles

def process_image(image_path, output_path):
    """Verarbeitet Bild mit Logo"""
    try:
        # Logo-Pfad (anpassen falls nötig)
        logo_path = Path(__file__).parent / "media" / "logo.png"
        if not logo_path.exists():
            # Kein Logo verfügbar, kopiere einfach
            return False
        
        processor = ImageProcessor(str(logo_path))
        processor.add_watermark(
            str(image_path), 
            str(output_path),
            position="bottom-right",
            logo_size_ratio=0.12,
            margin=30
        )
        return True
    except Exception as e:
        print(f"Fehler beim Verarbeiten des Bildes {image_path}: {e}")
        return False

def import_article(article, db_articles):
    """Importiert einen Artikel"""
    # Prüfe ob bereits in DB
    if is_article_in_db(article['title'], db_articles):
        print(f"  ⏭️  Übersprungen (bereits in DB): {article['title'][:80]}")
        return False
    
    # Konvertiere Timestamp
    created_at = parse_whatsapp_timestamp(article['timestamp'])
    if not created_at:
        print(f"  ❌ Übersprungen (ungültiger Timestamp): {article['title'][:80]}")
        return False
    
    print(f"  📝 Importiere: {article['title'][:80]}")
    
    # Titel: Entferne Formatierung, da Titel in Metadaten durch CSS formatiert wird
    title_clean = remove_formatting(article['title'])
    
    # Content: Konvertiere WhatsApp zu Markdown Formatierung
    content_md = convert_whatsapp_to_markdown(article['content'])
    
    # Entferne Titel aus Content, falls er als erste Zeile vorkommt
    content_md = remove_title_from_content(title_clean, content_md)
    
    # Generiere Tags
    tags = generate_tags(title_clean, content_md)
    
    # Erstelle Artikel via API
    article_data = {
        'articles': [{
            'title': title_clean,
            'content': content_md,
            'author': None,
            'published': False,
            'created_at': created_at,
            'updated_at': created_at,
            'tags': tags  # Als Liste senden, nicht als String
        }]
    }
    
    try:
        # Importiere Artikel
        response = requests.post(f"{API_BASE}/import/articles", json=article_data)
        response.raise_for_status()
        result = response.json()
        
        if not result.get('success'):
            print(f"    ❌ Import fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
            return False
        
        print(f"    ✅ Artikel importiert")
        
        # Hole die Artikel-ID (neu abfragen)
        new_articles = get_existing_articles()
        article_id = None
        
        for art in new_articles:
            if art['title'] == article['title']:
                article_id = art['id']
                break
        
        if not article_id:
            print(f"    ⚠️  Artikel importiert, aber ID nicht gefunden")
            return True
        
        # Verarbeite und lade Bild hoch
        source_image = Path(article['image_path'])
        
        if not source_image.exists():
            print(f"    ⚠️  Bild nicht gefunden: {source_image}")
            return True
        
        # Verarbeite Bild mit Logo
        processed_image = TEMP_DIR / f"processed_{article['image_name']}"
        
        print(f"    🖼️  Verarbeite Bild...")
        if not process_image(str(source_image), processed_image):
            print(f"    ⚠️  Bildverarbeitung fehlgeschlagen, verwende Original")
            shutil.copy(source_image, processed_image)
        
        # Lade Bild hoch
        print(f"    ⬆️  Lade Bild hoch...")
        with open(processed_image, 'rb') as img_file:
            files = {'images': (article['image_name'], img_file, 'image/jpeg')}
            data = {'add_watermark': 'false'}  # Wir haben bereits ein Logo hinzugefügt
            upload_response = requests.post(
                f"{API_BASE}/upload/images/{article_id}",
                files=files,
                data=data
            )
            upload_response.raise_for_status()
            upload_result = upload_response.json()
            
            if upload_result.get('success'):
                print(f"    ✅ Bild hochgeladen")
            else:
                print(f"    ⚠️  Bild-Upload fehlgeschlagen: {upload_result.get('error')}")
        
        # Lösche temporäres Bild
        processed_image.unlink(missing_ok=True)
        
        return True
        
    except Exception as e:
        print(f"    ❌ Fehler: {e}")
        return False

def main():
    print("=" * 80)
    print("Import von Artikeln aus Artikel_History.md")
    print("=" * 80)
    print()
    
    if BATCH_LIMIT:
        print(f"⚠️  Batch-Limit: Maximal {BATCH_LIMIT} Artikel pro Lauf")
        print()
    
    # Hole existierende Artikel
    print("📥 Lade existierende Artikel aus DB...")
    db_articles = get_existing_articles()
    print(f"   {len(db_articles)} Artikel in DB gefunden")
    print()
    
    # Parse History
    print("📖 Parse Artikel_History.md...")
    history_articles = parse_history_articles()
    print(f"   {len(history_articles)} Artikel in History gefunden")
    print()
    
    # Importiere Artikel
    imported_count = 0
    skipped_count = 0
    
    print("🚀 Starte Import...")
    print()
    
    for i, article in enumerate(history_articles, 1):
        # Prüfe Batch-Limit
        if BATCH_LIMIT and imported_count >= BATCH_LIMIT:
            print()
            print(f"⏸️  Batch-Limit von {BATCH_LIMIT} Artikeln erreicht")
            print(f"   Noch {len(history_articles) - i + 1} Artikel übrig")
            print(f"   Führe das Skript erneut aus um weitere Artikel zu importieren")
            break
        
        print(f"[{i}/{len(history_articles)}]")
        
        if import_article(article, db_articles):
            imported_count += 1
            # Aktualisiere DB-Liste für nächste Prüfung
            db_articles = get_existing_articles()
        else:
            skipped_count += 1
        
        print()
    
    # Zusammenfassung
    print("=" * 80)
    print("Import abgeschlossen!")
    print("=" * 80)
    print(f"✅ Importiert: {imported_count}")
    print(f"⏭️  Übersprungen: {skipped_count}")
    print(f"📊 Gesamt verarbeitet: {min(i, len(history_articles))}")
    if BATCH_LIMIT and imported_count >= BATCH_LIMIT:
        print(f"💡 Noch {len(history_articles) - i + 1} Artikel übrig - Skript erneut ausführen")
    print()

if __name__ == '__main__':
    main()
