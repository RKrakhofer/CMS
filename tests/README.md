# Tests & Development

Dieses Verzeichnis ist für Tests und Entwicklungs-Experimente gedacht.

**Wichtig:**
- Wird NICHT ins Docker-Image gebaut (`.dockerignore`)
- Wird NICHT deployed (vom rsync ausgeschlossen)

## Setup

```bash
cd tests/

# Virtual Environment erstellen (optional)
python3 -m venv .venv
source .venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
```

## Tests ausführen

### Lokale Tests (localhost:5001)
```bash
# Alle Tests
pytest test_api.py -v

# Export/Import Loop Tests (mit automatischem Cleanup)
pytest test_export_import_loop.py -v

# Nur Export-Tests
pytest test_api.py::TestExportAPI -v

# Nur Import-Tests
pytest test_api.py::TestImportAPI -v

# Nur Reader-Tests
pytest test_api.py::TestReaderRoutes -v
```

### Stage-Tests (stage:5001/cms)
```bash
# Vorkonfiguriert für Stage
pytest test_stage.py -v

# Oder test_api.py mit Environment-Variablen
CMS_URL=http://stage:5001 CMS_PREFIX=/cms pytest test_api.py -v
```

### Custom Server
```bash
# Eigenen Server testen
CMS_URL=https://my-server.com CMS_PREFIX=/news pytest test_api.py -v
```

### Schneller Test
```bash
# Direkt ausführen (nutzt Environment-Variablen)
python test_api.py
python test_stage.py
python test_export_import_loop.py

# Unit-Tests (keine DB/Server nötig)
pytest test_db_manager.py -v            # DatabaseManager Tests
pytest test_security_functions.py -v    # DSGVO Security Tests
pytest test_whatsapp_formatter.py -v    # WhatsApp Formatter Tests
pytest test_image_processor.py -v       # Image Processing Tests

# Oder mit Test-Runner Script
./run_export_import_tests.sh           # Alle Export/Import Tests
./run_export_import_tests.sh simple    # Nur einfacher Test
./run_export_import_tests.sh images    # Test mit Bildern
./run_export_import_tests.sh cycle     # Vollständiger Zyklus
./run_export_import_tests.sh api       # Alle Tests
```

**Environment-Variablen:**
- `CMS_URL` - Server-URL (default: `http://localhost:5001`)
- `CMS_PREFIX` - App-Prefix (default: `` leer)

**test_stage.py:**
- Fest konfiguriert für `http://stage:5001/cms`

**test_export_import_loop.py:**
- Nutzt gleiche Environment-Variablen wie `test_api.py`
- Automatisches Cleanup nach jedem Test

## Beispiel-Session

```bash
# 1. Server starten (in anderem Terminal)
cd /home/richard/workspaces/FakeDaily
python start_web.py

# 2. Tests ausführen
cd tests
source .venv/bin/activate

# Schnelltest: Nur Export/Import Loop
pytest test_export_import_loop.py::TestExportImportLoop::test_simple_export_import_loop -v -s

# Alle Export/Import Tests
pytest test_export_import_loop.py -v

# Alle Tests (API + Export/Import)
pytest test_api.py test_export_import_loop.py -v

# Test-Output:
# test_export_import_loop.py::TestExportImportLoop::test_simple_export_import_loop PASSED
# test_export_import_loop.py::TestExportImportLoop::test_export_import_with_images PASSED
# test_export_import_loop.py::TestExportImportLoop::test_full_export_import_cycle PASSED
# ✓ Cleanup: Artikel 123 gelöscht
# ✓ Cleanup: Artikel 124 gelöscht
```

## Environment-Variablen

**test_api.py:**
- `CMS_URL` - Server-URL (default: `http://localhost:5001`)
- `CMS_PREFIX` - App-Prefix (default: `` leer)

**test_stage.py:**
- Fest konfiguriert für `http://stage:5001/cms`

## Test-Coverage

### Integration/E2E Tests

**API Tests (`test_api.py`):**
- ✅ Export-API (`/admin/api/export/articles`)
- ✅ Import-API (`/admin/api/import/articles`)
- ✅ Reader-Routes (`/reader/`, `/reader/article/<id>`)
- ✅ Tag-Filterung (`/reader/tag/<tag>`)
- ✅ Export-Import Roundtrip

**Export/Import Loop Tests (`test_export_import_loop.py`):**
- ✅ Vollständiger Export → Import Zyklus
- ✅ Export/Import mit Bildern (über Upload-API)
- ✅ Datenwiederherstellung nach Löschung
- ✅ Datenintegrität (Tags, Timestamps, Unicode)
- ✅ Edge Cases (ungültige IDs, fehlende Felder)
- ✅ **Automatisches Cleanup** - Keine DB-Verschmutzung

**Stage Tests (`test_stage.py`):**
- ✅ Stage-Server Erreichbarkeit
- ✅ APP_PREFIX funktioniert (`/fakedaily`)
- ✅ Static-Files mit Prefix
- ✅ Tag-Filterung auf Stage

### Unit Tests (isoliert, keine DB/Server nötig)

**DatabaseManager Tests (`test_db_manager.py`):**
- ✅ Artikel CRUD: add_article, get_article, get_all_articles, update_article, delete_article
- ✅ Tag-Filterung: get_articles_by_tag
- ✅ Suche: search_articles, get_article_by_title
- ✅ Bilder: add_image, get_images_for_article, delete_image
- ✅ Edge Cases: Nonexistent IDs, empty fields, Unicode, CASCADE delete
- ✅ 40+ Tests für alle DB-Operationen

**DSGVO Security Functions (`test_security_functions.py`):**
- ✅ IP Anonymisierung: anonymize_ip (IPv4, IPv6, invalid IPs)
- ✅ User-Agent Vereinfachung: simplify_user_agent (Chrome, Firefox, Safari, Edge, Opera, Bots)
- ✅ DSGVO-Konformität verifiziert: Keine PII-Leaks, Version-Stripping
- ✅ 20+ Tests für DSGVO-kritische Funktionen

**WhatsAppFormatter Tests (`test_whatsapp_formatter.py`):**
- ✅ Markdown → WhatsApp: Bold, Italic, Headers, Links, Code, Lists
- ✅ format_article: Vollständige Artikel-Formatierung
- ✅ Unicode & Special Characters
- ✅ Edge Cases: Empty content, long content, nested formatting
- ✅ 30+ Tests für WhatsApp-Export

**ImageProcessor Tests (`test_image_processor.py`):**
- ✅ Wasserzeichen: add_watermark (alle Positionen, Opacity, Size)
- ✅ Größenanpassung: resize_image (Aspect Ratio, Downscale, No Upscale)
- ✅ Thumbnails: create_thumbnail (Default/Custom Size, Aspect Ratio)
- ✅ Error Handling: Invalid paths, corrupted images
- ✅ 25+ Tests für Bildverarbeitung

## Test-Philosophie

### Cleanup-Strategie

Die Export/Import Loop Tests verwenden ein **automatisches Cleanup-System** statt DB-Backups:

**Warum kein Backup/Restore?**
- ❌ DB ist während Tests in Verwendung (Web-App läuft)
- ❌ Race Conditions möglich
- ❌ Komplexität durch Lock-Management

**Stattdessen: Smart Cleanup**
- ✅ Merkt sich initial state (Artikel-IDs vor Test)
- ✅ Führt Test durch (erstellt neue Artikel)
- ✅ Löscht nur neu erstellte Artikel nach Test
- ✅ Ursprüngliche Daten bleiben intakt
- ✅ Funktioniert auch bei parallel laufender App

**Implementierung (pytest fixture):**
```python
@pytest.fixture(autouse=True)
def setup_and_cleanup(self):
    # Vor Test: IDs merken
    self.initial_article_ids = {a['id'] for a in export['articles']}
    yield  # Test läuft
    # Nach Test: Neue Artikel löschen
    new_ids = current_ids - self.initial_article_ids
    for id in new_ids:
        delete_article(id)
```

