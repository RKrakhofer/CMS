# Similarity Detection - Deployment Guide

## Änderungen im Production Build

Die Similarity Detection ist jetzt direkt in die Import-API integriert (`web/app.py`).

## Deployment auf Stage Server

### 1. Code auf Server aktualisieren

```bash
# Lokale Änderungen committen
git add web/app.py tests/test_similarity_detection.py docs/Aehnlichkeitserkennung.md
git commit -m "Add similarity detection to import API"
git push

# Auf Server pullen
ssh uu@stage 'cd FakeDaily && git pull'
```

### 2. Container neu starten

```bash
ssh uu@stage 'cd FakeDaily && docker compose restart cms-app'
```

### 3. Funktionalität testen

#### Test 1: Import mit Duplikaten

```bash
# Teste API mit JSON-Datei die Duplikate enthält
curl -X POST http://stage:5001/cms/admin/api/import/articles \
  -H "Content-Type: application/json" \
  -d @test-import-with-duplicates.json
```

**Erwartete Response:**
```json
{
  "success": true,
  "imported": 5,
  "skipped": 3,  // Sollte Similarity-Matches enthalten
  "updated": 0,
  "errors": []
}
```

#### Test 2: Logs prüfen

```bash
# Similarity Detection Events im Log finden
ssh uu@stage 'cd FakeDaily && docker compose logs cms-app | grep -i "similarity"'
```

**Erwartete Ausgabe:**
```
Similarity detected: 'Fake Daily 🎭 – News' ~ 'Fake Daily – News' (using existing)
```

#### Test 3: Unit Tests im Container

```bash
# Tests im Container ausführen
ssh uu@stage 'cd FakeDaily && docker compose exec cms-app pytest tests/test_similarity_detection.py -v'
```

**Erwartete Ausgabe:**
```
===================== 18 passed in 0.30s ======================
```

## Verifizierung

### 1. API Endpoint prüfen

```bash
curl -X POST http://stage:5001/cms/admin/api/import/articles \
  -H "Content-Type: application/json" \
  -d '{
    "articles": [
      {
        "title": "Test Artikel",
        "content": "Test Content",
        "tags": ["test"],
        "publish_date": "2026-01-21",
        "is_published": false
      }
    ],
    "count": 1,
    "success": true
  }'
```

### 2. Datenbank prüfen

```bash
# In Container einloggen
ssh -t uu@stage 'cd FakeDaily && docker compose exec cms-app bash'

# Artikel mit ähnlichen Titeln finden
sqlite3 /app/database/articles.db "SELECT id, title FROM articles WHERE title LIKE '%Fake Daily%' ORDER BY title;"
```

### 3. Performance Monitor

```python
# In Container: Python-Script für Performance-Test
import time
from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Test mit realen Daten
title1 = "Fake Daily – Die Wahrheit hinter den Nachrichten"
title2 = "Fake Daily 🎭 – Die Wahrheit hinter den Nachrichten"

start = time.time()
for i in range(1000):
    sim = similarity(title1, title2)
duration = time.time() - start

print(f"1000 Vergleiche: {duration:.3f}s ({duration/1000*1000:.3f}ms pro Vergleich)")
# Erwartung: < 5ms pro Vergleich
```

## Troubleshooting

### Problem: Similarity Detection funktioniert nicht

**Check 1: Code aktuell?**
```bash
ssh uu@stage 'cd FakeDaily && git log --oneline -5'
# Sollte Commit "Add similarity detection to import API" enthalten
```

**Check 2: Container neu gestartet?**
```bash
ssh uu@stage 'cd FakeDaily && docker compose ps'
# Status sollte "Up" sein mit aktuellem Timestamp
```

**Check 3: Import in Python verfügbar?**
```bash
ssh uu@stage 'cd FakeDaily && docker compose exec cms-app python3 -c "from difflib import SequenceMatcher; print(\"OK\")"'
# Sollte "OK" ausgeben
```

### Problem: Zu viele False Positives

Artikel werden fälschlich als Duplikat erkannt.

**Lösung: Thresholds erhöhen in `web/app.py`**

```python
# Zeile ~786 (in are_similar_articles)
def are_similar_articles(new_article: dict, existing_article: dict,
                         title_threshold: float = 0.97,  # War: 0.95
                         content_threshold: float = 0.93) -> bool:  # War: 0.90
```

Nach Änderung:
```bash
ssh uu@stage 'cd FakeDaily && docker compose restart cms-app'
```

### Problem: Duplikate werden nicht erkannt

**Lösung: Thresholds senken**

```python
# Zeile ~786 (in are_similar_articles)
def are_similar_articles(new_article: dict, existing_article: dict,
                         title_threshold: float = 0.92,  # War: 0.95
                         content_threshold: float = 0.85) -> bool:  # War: 0.90
```

### Problem: Import zu langsam

Bei sehr vielen Artikeln (>1000) kann der Similarity-Check langsam werden.

**Optimierung 1: Nur letzten N Artikel prüfen**

```python
# In import_articles_json(), Zeile ~800
if not existing:
    # Nur letzte 500 Artikel prüfen statt alle
    all_articles = db.get_all_articles(limit=500, order='DESC')
    for article in all_articles:
        if are_similar_articles(article_data, article):
            existing = article
            break
```

**Optimierung 2: Index auf title-Spalte**

```sql
-- In Container
sqlite3 /app/database/articles.db
CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title);
```

## Monitoring

### 1. Similarity-Matches tracken

```bash
# Täglich: Wie viele Similarity-Matches?
ssh uu@stage 'cd FakeDaily && docker compose logs --since 24h cms-app | grep -c "Similarity detected"'
```

### 2. Import-Statistiken

```bash
# Letzte Imports anzeigen
ssh uu@stage 'cd FakeDaily && docker compose logs --tail 100 cms-app | grep "API: Import completed"'
```

**Beispiel-Output:**
```
API: Import completed - Imported=5, Updated=0, Skipped=3, Errors=0
```

### 3. Performance-Metriken

```bash
# Import-Dauer tracken (in app.py logging hinzufügen)
# Siehe logs/app.log für Zeitstempel
```

## Rollback-Plan

Falls Similarity Detection Probleme verursacht:

```bash
# 1. Zu vorherigem Commit zurück
ssh uu@stage 'cd FakeDaily && git log --oneline -10'
ssh uu@stage 'cd FakeDaily && git checkout <commit-hash-vor-similarity>'

# 2. Container neu bauen
ssh uu@stage 'cd FakeDaily && docker compose up -d --build'

# 3. Verifizieren
curl http://stage:5001/cms/admin/
```

## Best Practices

✅ **Vor Deployment:** Alle Tests lokal ausführen
```bash
pytest tests/test_similarity_detection.py -v
```

✅ **Nach Deployment:** Logs für 24h überwachen
```bash
ssh uu@stage 'cd FakeDaily && docker compose logs -f cms-app | grep -i "similarity\|error"'
```

✅ **Wöchentlich:** Import-Statistiken reviewen
- Wie viele Duplikate wurden erkannt?
- Gibt es False Positives?
- Performance OK?

✅ **Bei Threshold-Änderungen:** A/B Test mit Testdaten
```bash
# Test-Import mit bekannten Duplikaten
curl -X POST http://stage:5001/cms/admin/api/import/articles -d @test-duplicates.json
```

## Dokumentation

- **Algorithmus:** `docs/Aehnlichkeitserkennung.md`
- **Tests:** `tests/test_similarity_detection.py`
- **Code:** `web/app.py` (Zeile 744+)
- **Workflow:** `import/import_workflow.py`

## Support

Bei Problemen:
1. Logs prüfen: `docker compose logs cms-app`
2. Tests ausführen: `pytest tests/test_similarity_detection.py -v`
3. Dokumentation lesen: `docs/Aehnlichkeitserkennung.md`
4. Thresholds anpassen falls nötig
