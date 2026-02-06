# CMS - Artikel & Bild Datenbank

SQLite-basiertes Content Management System zur Verwaltung von Artikeln (Markdown) und Bildern mit Flask Web-Interface.

## 🚀 Quick Start

### Option 1: Docker (empfohlen)

```bash
# Build und Start
./deploy.sh

# Oder manuell:
docker-compose up -d

# Logs anzeigen
docker-compose logs -f

# Stoppen
docker-compose down
```

**URLs:**
- **Reader (Public):** http://localhost:5001/reader/
- **Admin:** http://localhost:5001/admin/

### Option 2: Lokal (Development)

### 1. Virtual Environment & Dependencies
```bash
# Virtual Environment erstellen
python3 -m venv .venv

# Aktivieren
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Packages installieren
pip install -r requirements.txt
```

### 2. Datenbank initialisieren
```bash
python scripts/init_db.py
```

### 3. Web-Interface starten
```bash
python start_web.py
```

**URLs:**
- **Reader (Public):** http://localhost:5000/reader/
- **Admin:** http://localhost:5000/admin/

## 🌐 Web-Interface Features

- ✅ **Artikel-Übersicht** - Alle Artikel auf einen Blick
- ✅ **Artikel erstellen/bearbeiten** - Mit Markdown-Editor
- ✅ **Markdown-Rendering** - Automatische Konvertierung in allen Ansichten
- ✅ **Reader-Ansicht** - Öffentliche Artikel-Ansicht ohne Admin-Interface
- ✅ **Tag-Filterung** - Klickbare Tags zum Filtern von Artikeln nach Themen
- ✅ **Bilder hochladen** - Drag & Drop Support
- ✅ **Wasserzeichen** - Automatisches Logo auf Bilder
- ✅ **Suche** - Volltextsuche über Titel und Inhalt
- ✅ **Filter** - Nach Veröffentlichungsstatus
- ✅ **Tags** - Kategorisierung und Filterung
- ✅ **WhatsApp Export** - Artikel als WhatsApp-formatierte Texte
- ✅ **JSON API** - Export und Import von Artikeln
- ✅ **Responsive Design** - Mobile-freundlich
- ✅ **Proxy-Support** - Funktioniert hinter Reverse-Proxies mit APP_PREFIX
- ✅ **Konfigurierbar** - Site-Titel, Base-URL und Prefix über Environment-Variablen

## ⚙️ Konfiguration

CMS kann über Environment-Variablen konfiguriert werden:

### Verfügbare Optionen

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `APP_PREFIX` | Sub-Path für Deployment (z.B. `/cms`) | `` (leer) |
| `SITE_TITLE` | Name der Website (erscheint in Logo, Titel, Footer) | `CMS` |
| `BASE_URL` | Base-URL für externe Links | `http://localhost:5001` |
| `SECRET_KEY` | Flask Secret Key für Sessions | `dev-secret-key-change-in-production` |

### Beispiel docker-compose.yml

```yaml
environment:
  - APP_PREFIX=/cms
  - SITE_TITLE=Meine Nachrichten
  - BASE_URL=https://news.example.com
  - SECRET_KEY=your-secret-key-here
```

### Beispiel direkter Start

```bash
APP_PREFIX=/news SITE_TITLE="Tech News" python start_web.py
```

## 📁 Struktur

```
CMS/
├── database/
│   └── articles.db         # SQLite Datenbank
├── media/
│   └── images/            # Gespeicherte Bilder
├── scripts/
│   ├── init_db.py         # DB initialisieren
│   ├── import_article.py  # Einzelner Artikel
│   └── batch_import.py    # Bulk-Import
└── src/
    └── db_manager.py      # Datenbank-Manager
```

## 💾 Datenbank-Schema

### Tabelle: articles
- `id` - Primärschlüssel
- `title` - Artikel-Titel
- `content` - Markdown-Inhalt
- `author` - Autor
- `created_at` - Erstellungsdatum
- `updated_at` - Aktualisierungsdatum
- `published` - Veröffentlicht (0/1)
- `tags` - JSON-Array von Tags

### Tabelle: images
- `id` - Primärschlüssel
- `article_id` - Referenz zu articles
- `filename` - Dateiname
- `filepath` - Relativer Pfad
- `alt_text` - Alt-Text
- `caption` - Bildunterschrift
- `uploaded_at` - Upload-Datum

## 🔧 Verwendung

### Security Logging

Alle sicherheitsrelevanten Events werden automatisch geloggt:

**Log-Dateien:**
- `logs/security.log` - Admin-Aktionen, Uploads, API-Calls
- `logs/app.log` - Allgemeine Application Events

**Log-Rotation:**
- `security.log` - Max 10MB, rotiert zu 5 Backup-Dateien (security.log.1 bis .5)
- `app.log` - Max 5MB, rotiert zu 3 Backup-Dateien (app.log.1 bis .3)
- Älteste Logs werden automatisch gelöscht

**Geloggte Events:**
- ✅ Artikel erstellen/aktualisieren/löschen (mit IP, User-Agent)
- ✅ Bild-Uploads und -Löschungen
- ✅ API Export/Import Requests
- ✅ Fehler und Warnungen

**Beispiel-Log-Eintrag:**
```
2026-01-16 20:15:32 - cms.security - INFO - [192.168.1.100] Article created: ID=42, Title='Breaking News', Published=True - UA: Mozilla/5.0...
2026-01-16 20:16:05 - cms.security - WARNING - [192.168.1.100] Article deleted: ID=41
2026-01-16 20:17:22 - cms.security - INFO - [10.0.0.5] Image uploaded: ArticleID=42, File=42_20260116_201722_photo.jpg, Watermark=True
```

### Python API

```python
from src.db_manager import DatabaseManager

db = DatabaseManager()

# Artikel erstellen
article_id = db.add_article(
    title="Mein Artikel",
    content="# Überschrift\n\nText...",
    author="Max Mustermann",
    published=True,
    tags=["news", "wichtig"]
)

# Artikel abrufen
article = db.get_article(article_id)
all_articles = db.get_all_articles()

# Artikel aktualisieren
db.update_article(article_id, title="Neuer Titel", published=True)

# Bild hinzufügen
db.add_image(
    article_id=article_id,
    filename="bild.jpg",
    filepath="media/images/bild.jpg",
    alt_text="Beschreibung"
)

# Suche
results = db.search_articles("Suchbegriff")
```

### REST API

#### Artikel exportieren

```bash
# Alle Artikel als JSON exportieren
curl http://localhost:5001/admin/api/export/articles

# Mit jq formatiert
curl http://localhost:5001/admin/api/export/articles | jq
```

**Response:**
```json
{
  "success": true,
  "count": 10,
  "articles": [
    {
      "id": 1,
      "title": "Artikel-Titel",
      "content": "# Markdown\n\nInhalt...",
      "author": "Autor",
      "created_at": "2026-01-16T10:00:00",
      "updated_at": "2026-01-16T12:00:00",
      "published": 1,
      "tags": ["tag1", "tag2"],
      "images": [
        {
          "id": 1,
          "filename": "bild.jpg",
          "alt_text": "Beschreibung",
          "caption": "Bildunterschrift",
          "url": "http://localhost:5001/images/bild.jpg"
        }
      ]
    }
  ]
}
```

#### Artikel importieren

```bash
# Artikel aus JSON importieren
curl -X POST http://localhost:5001/admin/api/import/articles \
  -H "Content-Type: application/json" \
  -d '{
    "articles": [
      {
        "title": "Neuer Artikel",
        "content": "# Markdown\n\nInhalt...",
        "author": "Autor",
        "published": true,
        "tags": ["tag1", "tag2"],
        "created_at": "2026-01-16T10:00:00",
        "updated_at": "2026-01-16T12:00:00"
      }
    ]
  }'
```

**Import-Logik:**
- Artikel wird **neu erstellt**, wenn der Titel noch nicht existiert
- Artikel wird **aktualisiert**, wenn der Titel existiert UND `updated_at` im Import neuer ist
- Artikel wird **übersprungen**, wenn bereits eine neuere/gleiche Version existiert

**Response:**
```json
{
  "success": true,
  "imported": 5,   // Neu hinzugefügte Artikel
  "updated": 2,    // Aktualisierte Artikel
  "skipped": 3,    // Übersprungene Artikel
  "errors": []     // Eventuelle Fehler
}
```

### Bilder hochladen (API)

**Endpoint:** `POST /admin/api/upload/images/<article_id>`

**Beispiel:**
```bash
# Einzelnes Bild hochladen
curl -X POST "http://localhost:5001/admin/api/upload/images/1" \
  -F "images=@/path/to/image1.jpg"

# Mehrere Bilder gleichzeitig
curl -X POST "http://localhost:5001/admin/api/upload/images/1" \
  -F "images=@/path/to/image1.jpg" \
  -F "images=@/path/to/image2.png"

# Mit Wasserzeichen (Logo)
curl -X POST "http://localhost:5001/admin/api/upload/images/1" \
  -F "images=@/path/to/image1.jpg" \
  -F "add_watermark=true"
```

**Response:**
```json
{
  "success": true,
  "uploaded": 2,
  "errors": [],
  "images": [
    {
      "filename": "1_20260117_123456_image1.jpg",
      "original_filename": "image1.jpg",
      "url": "http://localhost:5001/media/images/1_20260117_123456_image1.jpg"
    }
  ]
}
```

**Hinweise:**
- Erlaubte Dateitypen: PNG, JPG, JPEG, GIF, WebP
- Maximale Dateigröße: 16MB pro Bild
- Bilder werden automatisch umbenannt: `<article_id>_<timestamp>_<filename>`
- Optional: `add_watermark=true` fügt Logo hinzu (erfordert logo.png im Projektverzeichnis)

### Public Reader Interface

```
http://localhost:5001/                  # Redirect zu /reader/
http://localhost:5001/reader/           # Alle veröffentlichten Artikel
http://localhost:5001/reader/article/1  # Einzelner Artikel
http://localhost:5001/reader/tag/Politik # Artikel gefiltert nach Tag
http://localhost:5001/public/           # Alternative Route
```

**Tag-Filterung:**
- Klickbare Tags in der Reader-Ansicht
- Zeigt nur Artikel mit dem ausgewählten Tag
- Aktives Tag wird visuell hervorgehoben (dunkler + ✓)
- "Filter entfernen" Button zum Zurücksetzen

**Proxy-Tauglich:**
Das `/reader/` Interface ist vollständig proxy-tauglich und funktioniert mit:
- X-Forwarded-For, X-Forwarded-Proto, X-Forwarded-Host, X-Forwarded-Prefix
- **APP_PREFIX Environment-Variable** für einfaches Sub-Path-Deployment (z.B. `/cms`)
- Automatische URL-Generierung durch `url_for()` - funktioniert in jedem Context

**Beispiel - App unter /cms deployen:**
```bash
# In docker-compose.yml:
environment:
  - APP_PREFIX=/cms

# URLs werden automatisch:
# https://deine-domain.de/cms/           -> Redirect zu /reader/
# https://deine-domain.de/cms/reader/    -> Public Reader
# https://deine-domain.de/cms/admin/     -> Admin-Interface
```

Beispiel Nginx-Config siehe unten im Abschnitt "Reverse Proxy Setup".

### WhatsApp Export

Artikel als WhatsApp-formatierter Text exportieren:
```
http://localhost:5001/admin/article/1/whatsapp
```

## � Export & Backup

### Export mit Bildern (Script)

Das `export_with_images.sh` Script exportiert alle Artikel als JSON und lädt zugehörige Bilder automatisch herunter:

```bash
# Export von localhost
./export_with_images.sh

# Export von anderem Server
./export_with_images.sh http://stage:5001/cms

# Mit eigenem Export-Verzeichnis
./export_with_images.sh http://stage:5001/cms my_export
```

**Was macht das Script:**
1. Ruft `/admin/api/export/articles` auf
2. Speichert JSON in `export_TIMESTAMP/articles.json`
3. Lädt alle referenzierten Bilder nach `export_TIMESTAMP/images/`
4. Zeigt Import-Befehl für anderen Server

**Ausgabe:**
```
export_20260116_123456/
├── articles.json          # Alle Artikel mit Metadaten
└── images/                # Heruntergeladene Bilder
    ├── image1.jpg
    └── image2.jpg
```

### Import mit Bildern (Script)

Das `import_with_images.sh` Script importiert ein Export-Verzeichnis auf einen anderen Server:

```bash
# Import auf localhost
./import_with_images.sh export_20260116_123456

# Import auf anderen Server
./import_with_images.sh export_20260116_123456 http://production:5001/cms
```

**Was macht das Script:**
1. Liest `articles.json` aus dem Export-Verzeichnis
2. Importiert alle Artikel über `/admin/api/import/articles`
3. Zeigt Statistik (neu/aktualisiert/übersprungen)
4. Informiert über Bilder (müssen manuell ins `media/images/` Verzeichnis kopiert werden)

**Hinweis zu Bildern:**
Die Import-API importiert nur Artikel-Metadaten. Bilder müssen separat kopiert werden:
```bash
# Bilder ins Ziel-System kopieren
cp export_20260116_123456/images/* /pfad/zu/cms/media/images/

# Oder per rsync auf Remote-Server
rsync -av export_20260116_123456/images/ server:/pfad/zu/cms/media/images/
```

### Backup (Script)

Vollständiges Backup mit Datenbank und Bildern:

```bash
./backup.sh
```

Erstellt ein komprimiertes Archiv mit:
- SQLite-Datenbank (`articles.db`)
- Allen Bildern (`images/`)
- JSON-Export für Interoperabilität

## �📝 Import-Formate

### JSON
```json
[
  {
    "title": "Artikel-Titel",
    "content": "# Markdown\n\nInhalt...",
    "author": "Autor",
    "published": true,
    "tags": ["tag1", "tag2"]
  }
]
```

### CSV
```csv
title,content,author,published,tags
"Titel 1","# Content","Autor",true,"tag1,tag2"
```

## 🔄 Reverse Proxy Setup

CMS ist vollständig proxy-tauglich und respektiert alle Standard-Forwarded-Headers.

### Methode 1: APP_PREFIX (empfohlen für einfache Setups)

Setze die `APP_PREFIX` Environment-Variable in `docker-compose.yml`:

```yaml
environment:
  - APP_PREFIX=/cms
  - SITE_TITLE=Meine News  # Optional: Site-Titel ändern
  - BASE_URL=https://my-domain.com  # Optional: Für externe Links
```

Oder beim direkten Start:
```bash
APP_PREFIX=/cms SITE_TITLE="Meine News" python start_web.py
```

**Was passiert:**
- Flask konfiguriert automatisch alle Routen unter `/cms`
- Static-Files (CSS/JS) werden unter `/cms/static/` serviert
- `url_for()` generiert automatisch korrekte Pfade mit Prefix

Dann einfache Nginx-Config:
```nginx
location /cms/ {
    proxy_pass http://localhost:5001/cms/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Wichtig: Erlaube Datei-Uploads bis 16MB
    client_max_body_size 16M;
}
```

### Methode 2: X-Forwarded-Prefix (flexibler)

Ohne APP_PREFIX - Nginx setzt den Prefix:
```nginx
location /news/ {
    proxy_pass http://localhost:5001/;
    proxy_set_header X-Forwarded-Prefix /news;
    # ... andere Headers ...
    
    # Wichtig: Erlaube Datei-Uploads bis 16MB
    client_max_body_size 16M;
}
```

### Nginx (empfohlen)

```nginx
# Standard Setup (Root-Pfad)
location / {
    proxy_pass http://localhost:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    
    # Wichtig: Erlaube Datei-Uploads bis 16MB
    client_max_body_size 16M;
}

# Mit Sub-Path (z.B. /news/)
location /news/ {
    proxy_pass http://localhost:5001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Prefix /news;
    
    # Wichtig: Erlaube Datei-Uploads bis 16MB
    client_max_body_size 16M;
}
```

### Apache

```apache
<Location /reader>
    ProxyPass http://localhost:5001/reader
    ProxyPassReverse http://localhost:5001/reader
    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-Prefix "/reader"
</Location>
```

### Traefik

```yaml
http:
  routers:
    fakedaily:
      rule: "Host(`news.example.com`)"
      service: fakedaily
      middlewares:
        - forward-headers
  
  services:
    fakedaily:
      loadBalancer:
        servers:
          - url: "http://localhost:5001"
  
  middlewares:
    forward-headers:
      headers:
        customRequestHeaders:
          X-Forwarded-Proto: "https"
```

## 🎯 Features

- ✅ **Flask Web-Interface** - Komfortable Browser-Verwaltung
- ✅ **Reader-Interface** - Öffentliche Artikel-Ansicht (`/public/` oder `/reader/`)
- ✅ **Tag-System** - Kategorisierung mit klickbarer Filterung
- ✅ SQLite-Datenbank (portabel, keine Server nötig)
- ✅ **Markdown-Rendering** - Automatische HTML-Konvertierung mit Extensions
- ✅ Bild-Verwaltung (Filesystem + DB-Referenzen)
- ✅ **Logo/Wasserzeichen automatisch auf Bilder**
- ✅ Bildverarbeitung (Resize, Thumbnails)
- ✅ Veröffentlichungs-Status
- ✅ **JSON API für Export/Import** - Synchronisation zwischen Instanzen
- ✅ Batch-Import (JSON/CSV)
- ✅ **WhatsApp-Export** - Formatierte Texte für Messaging
- ✅ Volltextsuche (Unicode-aware)
- ✅ **Proxy-Support** - APP_PREFIX für Sub-Path-Deployment
- ✅ **Security Logging** - Rotating Logs für Admin-Actions
- ✅ Python API

## 🔒 Sicherheit

⚠️ **WICHTIG:** CMS hat **keine eingebaute Authentifizierung**. Der `/admin/` Pfad **MUSS im Reverse Proxy geschützt werden!**

**Siehe [OWASP10_Report.md](OWASP10_Report.md) für:**
- Vollständige Sicherheitsanalyse (OWASP Top 10)
- Nginx/Apache Konfigurationsbeispiele mit HTTP Basic Auth
- Security Best Practices
- Action Items vor Production-Deployment

**Quick-Tipp für Nginx:**
```nginx
location /admin/ {
    auth_basic "CMS Admin";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:5001/admin/;
}
```

## 📦 Abhängigkeiten

```bash
# Virtual Environment erstellen
python3 -m venv .venv

# Aktivieren
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Packages installieren
pip install -r requirements.txt
```

**Benötigt:**
- Python 3.8+
- Pillow (Bildverarbeitung)

## 🖼️ Bildverarbeitung

### Logo/Wasserzeichen hinzufügen

```python
from src.image_processor import ImageProcessor

processor = ImageProcessor(logo_path="logo.png")

# Logo auf Bild platzieren
processor.add_watermark(
    image_path="bild.jpg",
    output_path="bild_mit_logo.jpg",
    position="bottom-right",    # bottom-right, bottom-left, top-right, top-left, center
    logo_size_ratio=0.15,       # Logo = 15% der Bildbreite
    opacity=255,                # Transparenz (0-255)
    margin=20                   # Abstand vom Rand
)
```

### Automatisch beim Import

```python
from scripts.import_article import import_article

import_article(
    title="Artikel mit Logo",
    content="# Content",
    image_paths=["bild1.jpg", "bild2.jpg"],
    logo_path="logo.png",
    add_watermark=True,
    watermark_position="bottom-right"
)
```

### Test

```bash
# Bildverarbeitungs-Test
python scripts/test_images.py
```

## 🧪 API Tests

### Setup

```bash
cd tests/
pip install -r requirements.txt
```

### Tests ausführen

**Lokale Tests:**
```bash
# Gegen localhost:5001
pytest test_api.py -v
```

**Stage-Tests:**
```bash
# Gegen stage:5001/cms
pytest test_stage.py -v

# Oder mit Environment-Variablen
CMS_URL=http://stage:5001 CMS_PREFIX=/cms python test_api.py
```

**Test-Coverage:**
- Export/Import API
- Reader-Interface
- Tag-Filterung
- APP_PREFIX Funktionalität
- Static-Files mit Proxy

Details siehe [tests/README.md](tests/README.md)
