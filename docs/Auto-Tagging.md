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

### 2. Bestehende Tags bleiben erhalten

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

Um neue Keywords hinzuzufügen oder neue Kategorien zu erstellen, bearbeite [src/auto_tagger.py](../src/auto_tagger.py):

```python
TAG_RULES = {
    'Neue Kategorie': [
        'keyword1', 'keyword2', 'keyword3'
    ],
    # ...
}
```

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

Teste die Auto-Tagging-Funktion mit dem Test-Skript:

```bash
python3 test_auto_tagging.py
```

## Beispiele

```bash
# Beispiel 1: Politik Österreich + Energie
Titel: "Kickl plant massive Energiewende"
Content: "FPÖ-Chef Herbert Kickl kündigte an, dass Österreich massiv in Solarenergie investieren wird."
→ Tags: ['Energie', 'Politik Österreich']

# Beispiel 2: Politik USA + Technologie
Titel: "Trump kündigt neue KI-Initiative an"
Content: "US-Präsident Trump präsentiert neues Programm für künstliche Intelligenz mit Elon Musk."
→ Tags: ['Politik USA', 'Technologie']

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
