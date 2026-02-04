# Auto-Tagging Funktion

## Überblick

Die Auto-Tagging-Funktion generiert automatisch Tags für Artikel basierend auf deren Titel und Inhalt. Sie wird in folgenden Situationen verwendet:

- **Beim Erstellen eines neuen Artikels** (Web-UI)
- **Beim Bearbeiten eines Artikels** (Web-UI)
- **Beim Import über API** (JSON-Import)

## Funktionsweise

### 1. Automatische Tag-Generierung

Wenn beim Speichern eines Artikels **keine Tags angegeben sind**, werden automatisch Tags generiert:

```python
from auto_tagger import add_auto_tags_if_empty

# Wenn tags leer ist, werden automatisch Tags generiert
tags = add_auto_tags_if_empty(tags, title, content)
```

### 2. Wortgrenzen-basiertes Matching (seit Februar 2026)

Die Tag-Erkennung verwendet **Regex-Wortgrenzen** (`\b`), um False Positives zu vermeiden:

```python
# ✅ Richtig: Nur vollständige Wörter werden gematcht
"organ" matched in "Das Organ arbeitet"
"organ" matched NICHT in "Organisationsplan"

# ✅ Weitere Beispiele
"kontrolle" matched in "Die Kontrolle funktioniert"
"kontrolle" matched NICHT in "Plausibilitätskontrollen"

"cia" matched in "Die CIA ermittelt"
"cia" matched NICHT in "Social Media"
```

**Vorteile:**
- Keine False Positives durch Teilwort-Matches
- Präzisere und relevantere Tags
- Bessere Filterbarkeit der Artikel

### 3. Kontextbezogenes Tagging mit negativen Keywords (seit Februar 2026)

Das System analysiert den **Kontext** mehrdeutiger Begriffe und verhindert falsche Tag-Zuordnungen:

```python
# ✅ Kontext-Analyse verhindert falsche Tags

# "Organ" im Kontext von Behörden → KEIN Gesundheit-Tag
"Das Organ des Strafvollzugs arbeitet effizient"
→ Tag: Justiz (NICHT Gesundheit)

"Der Europarat als Organ der Kontrolle"
→ Tag: Politik EU (NICHT Gesundheit)

# "Organ" im medizinischen Kontext → Gesundheit-Tag
"Das Organ muss transplantiert werden"
→ Tag: Gesundheit ✓

"Die Organspende rettet Leben"
→ Tag: Gesundheit ✓
```

**Negative Kontext-Regeln:**

Die Regeln in `NEGATIVE_CONTEXT` definieren Wörter, die einen Tag **verhindern**, wenn sie in der Nähe (±5 Wörter) eines Keywords stehen:

```python
NEGATIVE_CONTEXT = {
    'Gesundheit': {
        'organ': ['strafvollzug', 'justiz', 'polizei', 'behörde', 
                  'staat', 'verwaltung', 'institution', 'europarat', 'kontrolle'],
        'herz': ['hand', 'stein'],  # "Herz aus Stein", "Hand aufs Herz"
        'blut': ['bad'],  # "Blutbad" ist Gewalt, nicht Gesundheit
    },
    # ...
}
```

**Weitere Beispiele:**

```python
# ✗ "Herz aus Stein" → KEIN Gesundheit-Tag
# ✗ "Hand aufs Herz" → KEIN Gesundheit-Tag
# ✓ "Herzinfarkt" → Gesundheit ✓

# ✗ "Blutbad in der Arena" → KEIN Gesundheit-Tag
# ✓ "Blutspende im Krankenhaus" → Gesundheit ✓

# ✗ "Militärische Unternehmung" → KEIN Wirtschaft-Tag
# ✓ "Das Unternehmen meldet Insolvenz" → Wirtschaft ✓

# ✗ "Regelmäßige Bewegung ist wichtig" → Gesundheit (NICHT Politik)
# ✓ "Neue politische Bewegung gegründet" → Politik Österreich ✓

# ✗ "Partei will Steuern senken" (Parteiprogramm) → KEIN Wirtschaft-Tag
# ✓ "Unternehmen zahlen mehr Steuern" → Wirtschaft ✓
```

**Aktuelle negative Kontext-Regeln (Auswahl):**

- **Gesundheit**: organ, herz, blut, kammer, zelle, virus, behandlung, therapie, kultur, krebs, depression, fall
- **Wirtschaft**: unternehmen, bank, gold, gewinn, steuern
- **Politik Österreich/Deutschland**: steuerreform, steuerpolitik, bewegung
- **Gesundheit (Krone)**: krone (für Zahnkrone)
- **Wissenschaft**: studie (Film-Studio ausschließen)
- **Technologie**: virus (Grippe ausschließen)
- **Medien**: presse (Druckmaschine ausschließen)
- **Energie**: solar (Sonnensystem ausschließen), gas (Giftgas ausschließen)
- **Militär**: offensive (Fußball-Offensive ausschließen)
- **Justiz**: fall (Sturz ausschließen), zeuge (grammatisches "wurde" ausschließen)

**Vorteile:**
- Verhindert semantisch falsche Tag-Zuordnungen
- Berücksichtigt Mehrdeutigkeit von Wörtern (z.B. "Bewegung" = politisch vs. körperlich)
- Intelligentere Tag-Generierung basierend auf Kontext
- Reduziert manuelle Korrekturen erheblich

### 4. Bestehende Tags bleiben erhalten

Wenn bereits Tags vorhanden sind, werden diese **nicht überschrieben**:

```python
# Beispiel 1: Keine Tags → Auto-Tagging
tags = []
result = add_auto_tags_if_empty(tags, "Kickl plant Energiewende", "...")
# → ['Energie', 'Politik Österreich']

# Beispiel 2: Tags vorhanden → Keine Änderung
tags = ['Satire', 'Humor']
result = add_auto_tags_if_empty(tags, "Kickl plant Energiewende", "...")
# → ['Satire', 'Humor']
```

## Tag-Kategorien

Folgende Tag-Kategorien werden automatisch erkannt:

1. **Politik Österreich** - österreich, wien, fpö, övp, spö, kickl, nehammer, ...
2. **Politik Deutschland** - deutschland, berlin, afd, cdu, scholz, merz, ...
3. **Politik USA** - trump, usa, white house, republikaner, ...
4. **Politik EU** - eu, europa, brüssel, europaparlament, ...
5. **Satire** - fake daily, chefredakteur, kaiser, in eigener sache
6. **Technologie** - ki, künstliche intelligenz, musk, google, chatgpt, ...
7. **Wirtschaft** - wirtschaft, börse, inflation, benko, insolvenz, ...
8. **Wissenschaft** - wissenschaft, forschung, studie, klima, ...
9. **Energie** - energie, solar, windkraft, atomkraft, ...
10. **Medien** - medien, presse, orf, fake news, ...
11. **Gesellschaft** - integration, migration, demo, protest, ...
12. **Gesundheit** - gesundheit, arzt, krankenhaus, pflege, ...
13. **Justiz** - gericht, richter, klage, urteil, ...
14. **Militär** - militär, ukraine, russland, nato, ...
15. **Lebensmittel** - schnitzel, fleisch, restaurant, vegan, ...

## Tag-Regeln erweitern

### Neue Keywords hinzufügen

Um neue Keywords hinzuzufügen oder neue Kategorien zu erstellen, bearbeite [src/tag_rules.json](../src/tag_rules.json):

```json
{
  "tag_rules": {
    "Neue Kategorie": [
      "keyword1", "keyword2", "keyword3"
    ]
  }
}
```

**Seit Februar 2026:** Tag-Regeln werden in JSON-Datei verwaltet, nicht mehr im Python-Code.

### Negative Kontext-Regeln hinzufügen

Wenn ein Keyword mehrdeutig ist (z.B. "Organ" = Körperteil vs. Behörde, "Bewegung" = politisch vs. körperlich), füge negative Kontext-Regeln in [src/tag_rules.json](../src/tag_rules.json) hinzu:

```json
{
  "negative_context": {
    "Tag-Kategorie": {
      "mehrdeutiges_keyword": ["kontext_wort1", "kontext_wort2"]
    }
  }
}
```

**Beispiele:**

```json
{
  "negative_context": {
    "Gesundheit": {
      "organ": ["strafvollzug", "justiz", "polizei", "behörde", "staat"]
    },
    "Politik Österreich": {
      "bewegung": ["körper", "sport", "fitness", "training", "gesundheit"]
    },
    "Wirtschaft": {
      "steuern": ["partei", "parteiprogramm", "politiker", "bewegung"]
    }
  }
}
```

Das System prüft automatisch ±5 Wörter rund um das Keyword. Wird ein negatives Kontextwort gefunden, wird der Tag **nicht** vergeben.

**Tipp:** Debugging mit `explain_tags.py` zeigt, welche Keywords welche Tags auslösen:

```bash
./explain_tags.py "Neue politische Bewegung gegründet"
# Output: Politik Österreich: [bewegung]
```

```python
NEGATIVE_CONTEXT = {
    'Tag-Kategorie': {
        'mehrdeutiges_keyword': ['kontext_wort1', 'kontext_wort2'],
    }
}
```

**Beispiel:**

```python
NEGATIVE_CONTEXT = {
    'Gesundheit': {
        # Wenn "organ" zusammen mit diesen Wörtern vorkommt → KEIN Gesundheit-Tag
        'organ': ['strafvollzug', 'justiz', ' (ursprüngliche Tests):**

| Metrik | Kontext-basiert | spaCy-basiert |
|--------|----------------|---------------|
| **Genauigkeit** | 12/12 (100%) | 12/12 (100%) |
| **Durchschnitt/Test** | ~34.56ms | ~44.75ms |
| **Speedup** | **1.3x schneller** | - |
| **Modellgröße** | 0 MB | 15 MB |
| **Dependencies** | Standard-Library | spaCy + Modell |

**Nachtest mit erweiterten Mehrdeutigkeiten (Februar 2026):**

| Test | Kontext-basiert | spaCy-basiert |
|------|----------------|---------------|
| "Regelmäßige Bewegung für Gesundheit" | Gesundheit ✓ | Gesundheit + Politik Ö ❌ |
| "Neue politische Bewegung gegründet" | Politik Österreich ✓ | Politik Österreich ✓ |
| "Partei will Steuern senken" | Politik Österreich ✓ | Wirtschaft ❌ |

**Ergebnis:** Die kontextbasierte Lösung ist **präziser** als spaCy bei mehrdeutigen Begriffen.
Es wurde ein Vergleich zwischen dem kontextbasierten System und einer spaCy-NLP-basierten Implementierung durchgeführt.

### Testergebnisse

**Vergleich auf 12 repräsentativen Testfällen:**

| Metrik | Kontext-basiert | spaCy-basiert |
|--------|----------------|---------------|
| **Genauigkeit** | 12/12 (100%) | 12/12 (100%) |
| **Durchschnitt/Test** | ~34.56ms | ~44.75ms |
| **Speedup** | **1.3x schneller** | - |
| **Modellgröße** | 0 MB | 15 MB |
| **Dependencies** | Standard-Library | spaCy + Modell |

### Erkenntnisse

**Warum spaCy keinen Vorteil brachte:**

1. **Gleichwertige Genauigkeit**: Beide Systeme lösten alle Testfälle korrekt
2. **Kontext-Fenster ausreichend**: ±5 Wörter reichen für Mehrdeutigkeiten
3. **Domain-spezifisch**: Fake Daily hat sehr spezifische Kategorien, die ein allgemeines NLP-Modell nicht besser erkennt
4. **Kurze Texte**: Bei kurzen satirischen Artikeln ist der Overhead von spaCy nicht gerechtfertigt
ist die bevorzugte Lösung:

✅ **Präziser** - Erkennt mehrdeutige Begriffe besser (siehe "Bewegung"-Test)  
✅ **1.3x schneller** - Kein NLP-Overhead  
✅ **Keine zusätzlichen Dependencies** - Nur Standard-Library  
✅ **Einfach erweiterbar** - JSON-basierte Konfiguration  
✅ **Transparent und wartbar** - Klare Regeln, keine Black-Box  
✅ **Flexibel** - Negative Kontext-Regeln sind domänenspezifisch optimierbar

**Warum spaCy nicht verwendet wird:**

- ❌ Weniger präzise bei domänenspezifischen Mehrdeutigkeiten
- ❌ 1.3x langsamer trotz 15 MB Modell
- ❌ Generisches NLP-Modell passt nicht optimal zu Satire-News
- ❌ Komplexere Wartung (AMBIGUOUS_TERMS + spaCy-Logik)

spaCy würde nur Sinn machen bei:
- Hunderten von komplexen Kategorien
- Sehr langen, grammatikalisch komplexen Texten
- Bedarf an semantischer Ähnlichkeitserkennung
- Multilingualen Anforderungen

Die spaCy-Implementierung ist verfügbar in [`src/auto_tagger_spacy.py`](../src/auto_tagger_spacy.py) (archiviert, 
✅ Einfach erweiterbar  
✅ Transparent und wartbar  

spaCy würde nur Sinn machen bei:
- Hunderten von komplexen Kategorien
- Sehr langen, grammatikalisch komplexen Texten
- Bedarf an semantischer Ähnlichkeitserkennung
- Multilingualen Anforderungen

Die spaCy-Implementierung ist verfügbar in [`src/auto_tagger_spacy.py`](../src/auto_tagger_spacy.py) (nicht produktiv).

---

## Integration in der App

### Web-UI (app.py)

```python
from auto_tagger import add_auto_tags_if_empty

# In new_article() und edit_article()
tags = add_auto_tags_if_empty(tags, title, content)
```

### API-Import (app.py)

```python
# In import_articles_json()
tags = article_data.get('tags', [])
tags = add_auto_tags_if_empty(
    tags,
    article_data.get('title', ''),
    article_data.get('content', '')
)
```

## Testen

### Unit Tests

Teste die Auto-Tagging-Funktion mit pytest:

```bash
python -m pytest tests/test_auto_tagger.py -v
```

**Wichtige Testfälle:**
- `test_no_false_positive_for_partial_word_matches` - Verhindert Regressions zu False Positives
- `test_whole_word_match_for_chef` - Verifiziert Wortgrenzen-Matching
- Alle 28 Tests sollten bestehen

### Manuelle Tests

```bash
python test_auto_tagging.py
```

## Beispiele

```bash
# Beispiel 1: Politik Österreich + Energie
Titel: "Kickl plant massive Energiewende"
Content: "FPÖ-Chef Herbert Kickl kündigte an, dass Österreich massiv in Solarenergie investieren wird."
→ TRe-Tagging bestehender Artikel

Um alle Artikel mit der verbesserten Logik neu zu taggen:

```bash
# Lokal
python retag_all_articles.py

# Auf dem Server
ssh uu@stage "cd FakeDaily && cat retag_all_articles.py | docker exec -i cms python"
```

**Ergebnis:** Entfernt False Positives und wendet aktuelle Tag-Regeln an.

## Bekannte False Positives (behoben)

Diese Probleme wurden am 4. Februar 2026 behoben:

| Keyword | Kategorie | False Match in | Problem |
|---------|-----------|----------------|---------|
| `organ` | Gesundheit | **Organ**isationsplan | Teilwort-Match |
| `kontrolle` | Lebensmittel | Plausibilitäts**kontrollen** | Teilwort-Match |
| `cia` | Politik USA | So**cia**l Media | Teilwort-Match |
| `gehalt` | Wirtschaft | ein**gehalten** | Teilwort-Match |
| `scheidung` | Gesellschaft | Ent**scheidung** | Teilwort-Match |
| `haft` | Justiz | Gesells**chaft** | Teilwort-Match |

**Lösung:** Wortgrenzen-Regex (`\b keyword \b`) statt einfachem Substring-Matching.

## Vorteile

- ✅ **Konsistente Tags** - Alle Artikel erhalten relevante Tags
- ✅ **Zeitersparnis** - Keine manuelle Tag-Eingabe bei jedem Artikel
- ✅ **Optionaler Override** - Manuelle Tags haben immer Vorrang
- ✅ **Einfach erweiterbar** - Neue Kategorien und Keywords können jederzeit hinzugefügt werden
- ✅ **Präzise Erkennung** - Keine False Positives durch Wortgrenzen-Matching
- ✅ **Getestet** - 28 Unit-Tests mit Regression-Tests für bekannte Probleme

# Beispiel 3: Wissenschaft + Politik Österreich
Titel: "Neue Studie zur Erderwärmung"
Content: "Wissenschaftler der Universität Wien warnen vor beschleunigter Klimaveränderung."
→ Tags: ['Politik Österreich', 'Wissenschaft']
```

## Vorteile

- ✅ **Konsistente Tags** - Alle Artikel erhalten relevante Tags
- ✅ **Zeitersparnis** - Keine manuelle Tag-Eingabe bei jedem Artikel
- ✅ **Optionaler Override** - Manuelle Tags haben immer Vorrang
- ✅ **Einfach erweiterbar** - Neue Kategorien und Keywords können jederzeit hinzugefügt werden
