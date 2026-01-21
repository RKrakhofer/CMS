# Ähnlichkeitserkennung bei Artikel-Deduplizierung

## Übersicht

Die Ähnlichkeitserkennung wird verwendet, um doppelte oder sehr ähnliche Artikel beim Import automatisch zu erkennen und zu entfernen. Dies verhindert, dass verschiedene Versionen desselben Artikels mehrfach in der Datenbank landen.

---

## Technische Implementierung

### SequenceMatcher-Algorithmus

Die Erkennung nutzt Pythons `difflib.SequenceMatcher`, der auf dem **Longest Common Subsequence (LCS)** Algorithmus basiert:

```python
from difflib import SequenceMatcher

def similarity(a, b):
    """Berechnet Ähnlichkeit zwischen zwei Strings (0.0 - 1.0)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()
```

### Funktionsweise

**1. Longest Common Subsequence (LCS)**
- Findet die längste gemeinsame Teilsequenz zwischen zwei Strings
- Beispiel:
  ```
  Text A: "Lindner vom Finanzminister zum Mediator"
  Text B: "Lindner vom Ex-Finanzminister zum Mediator"
  
  Gemeinsam: "Lindner vom ", "Finanzminister zum Mediator"
  ```

**2. Ratio-Berechnung**
```
ratio = 2.0 × M / T

Wobei:
  M = Länge der gemeinsamen Zeichen
  T = Gesamtlänge beider Strings
```

**3. Ergebnis**
- `0.0` = Völlig unterschiedlich
- `1.0` = Identisch
- `0.95` = 95% ähnlich (sehr wahrscheinlich Duplikat)

---

## Praktische Beispiele

### Identische Artikel (100%)

```python
titel1 = "Fake Daily – Die Wahrheit, die keiner hören will!"
titel2 = "Fake Daily – Die Wahrheit, die keiner hören will!"

similarity(titel1, titel2)
# → 1.00 (100% identisch)
```

### Minimale Unterschiede (98%)

```python
titel1 = "📰 Fake Daily – Die Wahrheit, die keiner hören will!"
titel2 = "Fake Daily – Die Wahrheit, die keiner hören will!"

similarity(titel1, titel2)
# → 0.98 (nur Emoji fehlt)
```

### Eingefügter Text (96%)

```python
titel1 = "Deutschland unregierbar – Kaiser von Österreich bietet Eingliederung"
titel2 = "Deutschland unregierbar – Kaiser „Chef" von Österreich bietet Eingliederung"

similarity(titel1, titel2)
# → 0.96 (nur „Chef" eingefügt)
```

### Leicht unterschiedlich (88%)

```python
titel1 = "Lindner vor neuer Karriere: Vom Finanzminister zum Mediator"
titel2 = "Lindner vor neuer Karriere: Vom Ex-Finanzminister zum Mediator"

similarity(titel1, titel2)
# → 0.94 (nur "Ex-" eingefügt)
```

---

## Schwellwerte beim Deduplizieren

### Titel-Vergleich

```python
if similarity(title1, title2) > 0.95:
    # → Als Duplikat markieren
    # → Längere Version behalten
```

**Begründung:** Bei >95% Ähnlichkeit handelt es sich fast immer um denselben Artikel mit minimalen Änderungen (Tippfehler, Formatierung, etc.)

### Content-Vergleich

```python
content1_preview = content1[:500]  # Erste 500 Zeichen
content2_preview = content2[:500]

if similarity(content1_preview, content2_preview) > 0.90:
    # → Als Duplikat markieren
```

**Begründung:** Content-Vergleich ist weniger streng (90% statt 95%), da:
- Artikel oft mit gleicher Einleitung beginnen
- Nur Preview verglichen wird (Performance)
- Geringe Unterschiede im Haupttext häufiger vorkommen

### Kombination

Ein Artikel gilt als Duplikat wenn **ENTWEDER**:
- Titel >95% ähnlich **ODER**
- Content >90% ähnlich

Bei Duplikaten wird die **längere Version** behalten.

---

## Performance-Überlegungen

### Komplexität

- **Zeit:** O(n × m) für jeden Vergleich
  - n = Länge String A
  - m = Länge String B
  
- **Gesamt:** O(N²) für N Artikel
  - Bei 264 Artikeln: ~35.000 Vergleiche
  - Bei 1000 Artikeln: ~500.000 Vergleiche

### Optimierungen

**1. Preview für Content**
```python
# Statt ganzen Artikel (5000+ Zeichen):
content_preview = content[:500]
# → 10x schneller
```

**2. Nur generische Tags prüfen**
```python
generic_tags = {'satire', 'fake-daily', 'Satire'}
if set(current_tags).issubset(generic_tags):
    # Nur diese Artikel prüfen
```

**3. Early Exit**
```python
for existing in unique_articles:
    if similarity(title1, title2) > 0.95:
        break  # Erstes Duplikat gefunden, fertig
```

---

## Vorteile & Nachteile

### ✅ Vorteile

- **Erkennt Tippfehler:** "Finanzminister" vs "Finanzminiter"
- **Ignoriert Groß/Klein:** Durch `.lower()`
- **Funktioniert bei Umstellungen:** Teilweise
- **Schnell genug:** O(n×m) ist akzeptabel für kleine Datensätze
- **Keine Konfiguration:** Funktioniert out-of-the-box

### ❌ Nachteile

- **Keine Synonyme:** "Auto" vs "Fahrzeug" = unterschiedlich
- **Reihenfolge wichtig:** "A B C" vs "C B A" = geringe Ähnlichkeit
- **Falsch-Positive bei kurzen Texten:** "Die Wahrheit" ähnlich zu "Die Lüge"
- **Keine semantische Analyse:** Versteht keinen Kontext

---

## Alternative Ansätze

Für größere Projekte oder höhere Anforderungen:

### 1. Fuzzy Matching (fuzzywuzzy)
```python
from fuzzywuzzy import fuzz

ratio = fuzz.ratio(text1, text2)
token_sort_ratio = fuzz.token_sort_ratio(text1, text2)
```
**Vorteile:** Robuster bei Umstellungen

### 2. Levenshtein-Distanz
```python
from Levenshtein import distance

dist = distance(text1, text2)
```
**Vorteile:** Exakte Anzahl an Änderungen

### 3. Embeddings / Semantische Ähnlichkeit
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
embeddings = model.encode([text1, text2])
similarity = cosine_similarity(embeddings[0], embeddings[1])
```
**Vorteile:** Versteht Bedeutung, erkennt Paraphrasen

---

## Implementierung im Projekt

### Script: `clean_articles.py`

```python
# 1. Artikel laden
articles = load_articles()

# 2. Duplikate finden
unique_articles = []
for article in articles:
    is_duplicate = False
    
    for existing in unique_articles:
        # Titel-Check
        if similarity(article['title'], existing['title']) > 0.95:
            is_duplicate = True
            break
        
        # Content-Check
        if similarity(article['content'][:500], existing['content'][:500]) > 0.90:
            is_duplicate = True
            break
    
    if not is_duplicate:
        unique_articles.append(article)
```

### Ergebnis

```
Original: 358 Artikel
Nach Filterung: 273 Artikel (85 Nicht-Artikel entfernt)
Nach Deduplizierung: 264 Artikel (9 Duplikate entfernt)

Gesamt entfernt: 94 Einträge
```

---

## Integration in das CMS

Die Ähnlichkeitserkennung ist direkt in die Import-API integriert und wird bei jedem Import automatisch ausgeführt.

### API-Integration

**Endpoint:** `POST /cms/admin/api/import/articles`

**Import-Workflow:**
1. ✅ **Exakter Titel-Match**: Prüfen ob Artikel mit identischem Titel existiert
2. ✅ **Similarity Detection**: Wenn kein exakter Match → alle Artikel nach Ähnlichkeit durchsuchen
3. ✅ **Duplicate Handling**: Bei >95% Titel-Ähnlichkeit oder >90% Content-Ähnlichkeit → als Duplikat behandeln
4. ✅ **Timestamp-Vergleich**: Bei Duplikaten → neuere Version behalten (via `updated_at`)

### Code-Beispiel (app.py)

```python
from difflib import SequenceMatcher

def similarity(a: str, b: str) -> float:
    """Calculate similarity ratio using SequenceMatcher"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def are_similar_articles(new_article: dict, existing_article: dict,
                         title_threshold: float = 0.95,
                         content_threshold: float = 0.90) -> bool:
    """Check if two articles are similar"""
    title_sim = similarity(new_article.get('title', ''), 
                          existing_article.get('title', ''))
    
    if title_sim > title_threshold:
        return True
    
    # Check content similarity (first 500 chars)
    content1 = new_article.get('content', '')[:500]
    content2 = existing_article.get('content', '')[:500]
    content_sim = similarity(content1, content2)
    
    if content_sim > content_threshold:
        return True
    
    return False

@app.route('/admin/api/import/articles', methods=['POST'])
def import_articles_json():
    """Import articles with similarity detection"""
    # ... (siehe web/app.py Zeile 744+)
    
    # Prüfen ob Artikel mit diesem Titel bereits existiert
    existing = db.get_article_by_title(title)
    
    # Wenn kein exakter Match: Ähnlichkeitserkennung
    if not existing:
        all_articles = db.get_all_articles()
        for article in all_articles:
            if are_similar_articles(article_data, article):
                existing = article
                break
    
    # Bei Duplikat: Timestamp-Vergleich
    if existing:
        # ... Update-Logik ...
```

### Tests

Vollständige Unit-Tests in `tests/test_similarity_detection.py`:

```bash
pytest tests/test_similarity_detection.py -v
```

**Test-Kategorien:**
- ✅ Similarity-Funktion (identisch, case-insensitive, unterschiedlich)
- ✅ Threshold-Beispiele aus Dokumentation
- ✅ Article-Vergleich (exakt, ähnlich, unterschiedlich)
- ✅ Custom Thresholds
- ✅ Performance-Tests
- ✅ Edge Cases
- ✅ Import-Szenarien (Duplikat, Emoji, Update, ähnlich aber anders)

## Vorteile der Integration

**✅ Automatische Erkennung** - Keine manuelle Prüfung mehr nötig

**✅ Flexibel** - Thresholds können angepasst werden (derzeit 95%/90%)

**✅ Performance** - Vergleich in <10ms pro Artikel-Paar

**✅ Logging** - Ähnlichkeiten werden geloggt für Review

**✅ Dokumentiert** - Thresholds und Algorithmus sind nachvollziehbar

## Verwendung

### Import via API

```bash
curl -X POST http://stage:5001/cms/admin/api/import/articles \
  -H "Content-Type: application/json" \
  -d @articles.json
```

**Response:**
```json
{
  "success": true,
  "imported": 198,
  "skipped": 66,  # Enthält auch via Similarity erkannte Duplikate
  "updated": 0,
  "errors": []
}
```

### Import via Python-Skript

Automatisiertes Workflow-Skript in `import/import_workflow.py`:

```bash
cd import
python3 import_workflow.py \
  --input conversations.json \
  --output articles-import.json \
  --title-threshold 0.95 \
  --content-threshold 0.90
```

**Features:**
- Lädt Conversations aus ChatGPT Export
- Extrahiert Artikel
- Dedupliziert via Similarity Detection
- Konvertiert zu CMS-Format
- Importiert direkt zur API

## Wartung und Anpassung

### Thresholds anpassen

Wenn zu viele False Positives (fälschlich als Duplikat erkannt):
- Title-Threshold erhöhen: `0.95` → `0.97`
- Content-Threshold erhöhen: `0.90` → `0.93`

Wenn Duplikate nicht erkannt werden:
- Title-Threshold senken: `0.95` → `0.92`
- Content-Threshold senken: `0.90` → `0.85`

### Logging überprüfen

Bei Similarity-Matches wird geloggt:
```
Similarity detected: 'Neuer Titel' ~ 'Existierender Titel' (using existing)
```

Logs finden in `logs/app.log`

## Best Practices

### ✅ Empfohlene Schwellwerte

| Vergleich | Schwellwert | Verwendung |
|-----------|-------------|------------|
| Titel | >95% | Duplikat-Erkennung |
| Titel | >80% | Warnung/Prüfung |
| Content (Preview) | >90% | Duplikat-Erkennung |
| Content (Voll) | >85% | Für kleine Datensätze |

### ⚠️ Grenzfälle manuell prüfen

Bei Ähnlichkeit zwischen 85-95%:
- Manuell anschauen
- Könnte legitim verschiedene Artikel sein
- Oder unterschiedliche Versionen

### 🔍 Logging

```python
if 0.85 < similarity_ratio < 0.95:
    logger.warning(f"Potentielles Duplikat: {title1} vs {title2} ({similarity_ratio:.0%})")
```

---

## Siehe auch

- **ChatGPT Import:** `import/clean_articles.py`
- **Duplikate-Check:** `import/check_duplicates.py`
- **Auto-Tagging:** `docs/Auto-Tagging.md`
- **Python difflib:** https://docs.python.org/3/library/difflib.html
