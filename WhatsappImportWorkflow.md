# WhatsApp Import Workflow

Komplette Anleitung zum Import von Fake-Daily-Artikeln aus WhatsApp-Chat-Exporten.

## Übersicht

Dieser Workflow beschreibt den kompletten Prozess vom WhatsApp-Chat-Export bis zum vollständigen Import aller Artikel mit Bildern, Tags und korrekter Formatierung in die FakeDaily CMS-Datenbank.

## Voraussetzungen

- WhatsApp-Chat-Export als TXT-Datei
- Bilder aus dem WhatsApp-Export (IMG-*.jpg)
- Zugriff auf Stage-Server (uu@stage)
- NAS-Zugriff für Quelldateien
- Python 3 mit virtualenv
- Laufender FakeDaily CMS auf Stage (Port 5001)

## Workflow-Schritte

### 1. WhatsApp-Chat analysieren und parsen

**Script:** `whatsapp_import_helper/parse_whatsapp_articles.py`

Analysiert den WhatsApp-Chat-Export und extrahiert alle Artikel-ähnlichen Beiträge.

**Konfiguration:**
```python
WHATSAPP_FILE = "/mnt/nas-synology-1/home/Downloads/WhatsApp-Chat mit +43 676 3518170/WhatsApp-Chat mit +43 676 3518170.txt"
OUTPUT_FILE = "Artikel_History.md"
```

**Ausführung:**
```bash
cd /home/richard/workspaces/FakeDaily
source .venv/bin/activate
python3 whatsapp_import_helper/parse_whatsapp_articles.py
```

**Output:**
- `Artikel_History.md` mit strukturierten Artikeldaten (Titel, Datum, Bild, Inhalt)
- Anzahl gefundener Artikel wird angezeigt

**Artikel-Kriterien:**
- Mindestlänge: 200 Zeichen
- Marker: "Fake Daily", "FPÖ", "ÖVP", spezifische Keywords
- Enthält möglicherweise Bild-Referenz (IMG-*.jpg)

### 2. Stage-Datenbank für Import vorbereiten

**Script:** `whatsapp_import_helper/cleanup_stage_for_reimport.py`

Bereitet die Stage-Datenbank vor, indem alte Importe gelöscht werden.

**Ausführung:**
```bash
ssh uu@stage "cd FakeDaily && source .venv/bin/activate && python3 cleanup_stage_for_reimport.py"
```

**Aktionen:**
- Löscht alle Artikel mit ID > 1
- Löscht alle Bild-Einträge außer für Artikel ID 1
- Löscht alle Bilddateien außer `1_*`

### 3. Artikel importieren (mit Tags und Formatierung)

**Script:** `whatsapp_import_helper/import_history_articles.py`

Importiert Artikel aus `Artikel_History.md` über die Stage API mit automatischer Tag-Generierung und Formatierungs-Konvertierung.

**Features:**
- ✅ WhatsApp→Markdown Formatierung (*bold* → **bold**, _italic_ → *italic*, ~strike~ → ~~strike~~)
- ✅ Automatische Tag-Generierung (15 Kategorien)
- ✅ Original-Zeitstempel aus WhatsApp
- ✅ Titel-Bereinigung (keine Formatierung in Metadaten)
- ✅ Content-Bereinigung (doppelter Titel entfernt)
- ✅ Batch-Processing (10 Artikel pro Durchlauf)

**Konfiguration:**
```python
API_BASE = "http://stage:5001/cms/admin/api"
HISTORY_FILE = "/home/richard/workspaces/FakeDaily/Artikel_History.md"
IMAGE_SOURCE_DIR = "/mnt/nas-synology-1/home/Downloads/WhatsApp-Chat mit +43 676 3518170"
BATCH_LIMIT = 10  # Artikel pro Durchlauf
```

**Tag-Kategorien:**
- Politik Österreich, Politik Deutschland, Politik USA, Politik EU
- Satire, Technologie, Wirtschaft, Wissenschaft
- Energie, Medien, Gesellschaft, Gesundheit
- Justiz, Militär, Lebensmittel

**Ausführung (alle Batches):**
```bash
cd /home/richard/workspaces/FakeDaily
source .venv/bin/activate

# 12 Batches für ~120 Artikel (12 x 10 = 120)
for i in {1..12}; do
    echo "=== Batch $i ==="
    python3 whatsapp_import_helper/import_history_articles.py
    sleep 1
done
```

**Einzelner Batch:**
```bash
python3 whatsapp_import_helper/import_history_articles.py
```

**Output:**
- Anzahl importierter Artikel
- Anzahl übersprungener Artikel (bereits in DB)
- Verbleibende Artikel
- Warnung bei fehlenden Bildern (normal, werden im nächsten Schritt hochgeladen)

### 4. Bilder hochladen

**Script:** `whatsapp_import_helper/upload_images_to_stage.py`

Lädt alle Bilder vom NAS über die Stage API hoch und ordnet sie den korrekten Artikeln zu.

**Matching-Strategie:**
1. Exakter Match: Titel + Zeitstempel (auf Minute genau)
2. Fallback: Exakter Titel-Match
3. Fallback: Fuzzy Match (erste 80 Zeichen)

**Ausführung:**
```bash
cd /home/richard/workspaces/FakeDaily
source .venv/bin/activate
python3 whatsapp_import_helper/upload_images_to_stage.py
```

**Output:**
- Anzahl hochgeladener Bilder
- Artikel ohne History-Match
- Upload-Fehler

### 5. Verifikation

**Artikel-Anzahl prüfen:**
```bash
curl -s http://stage:5001/cms/admin/api/export/articles | python3 -c 'import sys,json; a=json.load(sys.stdin)["articles"]; print(f"Gesamt: {len(a)} Artikel")'
```

**Tags prüfen:**
```bash
curl -s http://stage:5001/cms/admin/api/export/articles > /tmp/articles.json
python3 << 'EOF'
import json
with open('/tmp/articles.json') as f:
    a = json.load(f)['articles']
tagged = [x for x in a if x.get('tags') and len(x['tags']) > 0]
print(f'Mit Tags: {len(tagged)}/{len(a)}')
EOF
```

**Bilder prüfen:**
```bash
python3 << 'EOF'
import json
with open('/tmp/articles.json') as f:
    a = json.load(f)['articles']
with_images = [x for x in a if x.get('images') and len(x['images']) > 0]
print(f'Mit Bildern: {len(with_images)}/{len(a)}')
EOF
```

## Dateien und Verzeichnisse

### Helper-Scripts

Alle Import-Helper-Scripts befinden sich in `whatsapp_import_helper/`:
- `parse_whatsapp_articles.py` - WhatsApp-Chat Parser
- `import_history_articles.py` - Artikel-Import mit Tags
- `upload_images_to_stage.py` - Bild-Upload
- `cleanup_stage_for_reimport.py` - Stage DB Cleanup

### Generierte Dateien

- `Artikel_History.md` - Zwischenspeicher mit geparsten Artikeln
- `/tmp/fakedaily_images/` - Temporäre Bilder beim Upload

### Quell-Dateien

- WhatsApp-Chat: `/mnt/nas-synology-1/home/Downloads/WhatsApp-Chat mit +43 676 3518170/WhatsApp-Chat mit +43 676 3518170.txt`
- Bilder: `/mnt/nas-synology-1/home/Downloads/WhatsApp-Chat mit +43 676 3518170/IMG-*.jpg`

## Kompletter Workflow (Kurzversion)

```bash
cd /home/richard/workspaces/FakeDaily
source .venv/bin/activate

# 1. Parse WhatsApp-Chat
python3 whatsapp_import_helper/parse_whatsapp_articles.py

# 2. Cleanup Stage
ssh uu@stage "cd FakeDaily && source .venv/bin/activate && python3 cleanup_stage_for_reimport.py"

# 3. Import Artikel (alle Batches)
for i in {1..12}; do
    python3 whatsapp_import_helper/import_history_articles.py
    sleep 1
done

# 4. Upload Bilder
python3 whatsapp_import_helper/upload_images_to_stage.py

# 5. Verifizieren
curl -s http://stage:5001/cms/admin/api/export/articles > /tmp/articles.json
python3 << 'EOF'
import json
with open('/tmp/articles.json') as f:
    a = json.load(f)['articles']
tagged = [x for x in a if x.get('tags') and len(x['tags']) > 0]
with_images = [x for x in a if x.get('images') and len(x['images']) > 0]
print(f'Artikel: {len(a)}')
print(f'Mit Tags: {len(tagged)}')
print(f'Mit Bildern: {len(with_images)}')
EOF
```

## Erwartete Ergebnisse

Basierend auf dem WhatsApp-Export vom August 2024 - Januar 2026:
- **127** Artikel in Artikel_History.md
- **120** Artikel importiert (7 bereits existierend)
- **115** Artikel mit Tags
- **113** Artikel mit Bildern
- **3** Artikel ohne History-Match (IDs variieren)

## Troubleshooting

### Artikel werden doppelt importiert

**Problem:** Artikel erscheinen mehrmals in der DB.

**Lösung:** 
```bash
ssh uu@stage "cd FakeDaily && source .venv/bin/activate && python3 cleanup_stage_for_reimport.py"
```
Dann Re-Import durchführen.

### Bilder werden nicht hochgeladen

**Problem:** Artikel haben keine Bilder.

**Ursache:** 
- NAS nicht gemountet
- Falscher Pfad in IMAGE_SOURCE_DIR
- Bild-Dateien fehlen

**Lösung:**
1. NAS-Pfad prüfen: `ls /mnt/nas-synology-1/home/Downloads/WhatsApp-Chat\ mit\ +43\ 676\ 3518170/IMG-*.jpg | wc -l`
2. Pfad in Script korrigieren
3. Erneut ausführen: `python3 whatsapp_import_helper/upload_images_to_stage.py`

### Tags sind leer

**Problem:** Artikel haben leere Tag-Listen.

**Ursache:** Tags wurden als String statt Liste gesendet.

**Lösung:** In `import_history_articles.py` prüfen:
```python
'tags': tags  # Muss Liste sein, nicht String!
```

### Falsche Bild-Zuordnung

**Problem:** Artikel haben falsche Bilder.

**Ursache:** Titel-Matching findet falschen Artikel.

**Lösung:** 
1. Stage cleanup durchführen
2. Re-Import mit aktualisiertem Script (nutzt Titel + Zeitstempel für Match)

## Technische Details

### API-Endpunkte

**Import:**
```
POST http://stage:5001/cms/admin/api/import/articles
Content-Type: application/json

{
  "articles": [{
    "title": "...",
    "content": "...",
    "created_at": "2024-08-19 14:10:00",
    "tags": ["Politik Österreich", "Satire"]
  }]
}
```

**Bild-Upload:**
```
POST http://stage:5001/cms/admin/api/upload/images/{article_id}
Content-Type: multipart/form-data

files: image file
add_watermark: false
```

**Export:**
```
GET http://stage:5001/cms/admin/api/export/articles
```

### Datenbank-Schema

**articles:**
- id (INTEGER, PRIMARY KEY)
- title (TEXT)
- content (TEXT)
- created_at (TIMESTAMP)
- tags (TEXT) - JSON-Array als String in DB, Liste in API

**images:**
- id (INTEGER, PRIMARY KEY)
- article_id (INTEGER, FOREIGN KEY)
- filename (TEXT) - Format: `{article_id}_{timestamp}_{original_name}.jpg`

### Formatierungs-Regeln

**WhatsApp → Markdown:**
- `*text*` → `**text**` (fett)
- `_text_` → `*text*` (kursiv)
- `~text~` → `~~text~~` (durchgestrichen)

**Titel-Bereinigung:**
- Alle Formatierungen entfernt (CSS übernimmt Darstellung)
- Emojis bleiben erhalten

**Content-Bereinigung:**
- Titel aus erster Zeile entfernt (verhindert Duplikation)
- WhatsApp→Markdown Konvertierung
- Zeilenumbrüche normalisiert

## Notizen

- **Batch-Limit:** 10 Artikel pro Durchlauf verhindert API-Überlastung und ermöglicht Fehlerbehandlung
- **Zeitstempel:** Format in WhatsApp ist `DD.MM.YY, HH:MM`, wird zu ISO `YYYY-MM-DD HH:MM:SS` konvertiert
- **Bilder:** Werden nach Upload in `media/images/` gespeichert mit Format `{id}_{timestamp}_{original}.jpg`
- **Tags:** Automatisch generiert durch Keyword-Matching in Titel und Content
- **NAS-Zugriff:** Erforderlich für Bild-Upload, muss lokal gemountet sein
