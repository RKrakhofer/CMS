"""
Auto-Tagging mit spaCy für NLP-basierte Kontext-Erkennung
"""
import spacy
from typing import List, Set
import re
import json
import os

# Lade spaCy-Modell (nur einmal beim Import)
try:
    nlp = spacy.load('de_core_news_sm')
except OSError:
    print("WARNUNG: Deutsches spaCy-Modell nicht gefunden!")
    print("Installiere mit: python -m spacy download de_core_news_sm")
    nlp = None


def load_tag_rules():
    """Lädt Tag-Regeln aus JSON-Datei"""
    json_path = os.path.join(os.path.dirname(__file__), 'tag_rules.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['tag_rules']


# Lade Tag-Regeln aus JSON
TAG_RULES = load_tag_rules()

# Mehrdeutige Begriffe, die spaCy-basierte Kontext-Analyse benötigen
AMBIGUOUS_TERMS = {
    'organ': {
        'Gesundheit': ['medizinisch', 'körper', 'transplantation', 'spende', 'patient', 'arzt'],
        'exclude_pos': ['PROPN'],  # Eigennamen wie "Organ des Strafvollzugs"
        'exclude_entities': ['ORG']  # Organisationen
    },
    'herz': {
        'Gesundheit': ['medizinisch', 'infarkt', 'kammer', 'kreislauf', 'patient'],
        'exclude_phrases': ['herz aus stein', 'hand aufs herz']
    },
    'blut': {
        'Gesundheit': ['spende', 'druck', 'probe', 'gruppe', 'transfusion', 'plasma'],
        'exclude_phrases': ['blutbad']
    },
    'virus': {
        'Gesundheit': ['grippe', 'corona', 'covid', 'pandemie', 'infektion', 'impfung'],
        'Technologie': ['computer', 'software', 'malware', 'cyber']
    },
    'bank': {
        'Wirtschaft': ['national', 'zentral', 'sparkasse', 'zinsen', 'kredit', 'konto'],
        'exclude_phrases': ['parkbank', 'sitzbank', 'sandbank']
    },
    'gold': {
        'Wirtschaft': ['preis', 'unze', 'börse', 'rohstoff', 'edelmetall'],
        'exclude_phrases': ['goldmedaille', 'olympia']
    }
}


def analyze_with_spacy(text: str) -> dict:
    """Analysiert Text mit spaCy und extrahiert linguistische Features
    
    Args:
        text: Zu analysierender Text
        
    Returns:
        Dict mit POS-Tags, Entities, Lemmas etc.
    """
    if nlp is None:
        return {'tokens': [], 'entities': [], 'noun_chunks': []}
    
    doc = nlp(text.lower())
    
    return {
        'doc': doc,
        'tokens': [(token.text, token.pos_, token.lemma_) for token in doc],
        'entities': [(ent.text, ent.label_) for ent in doc.ents],
        'noun_chunks': [chunk.text for chunk in doc.noun_chunks]
    }


def check_ambiguous_term(term: str, text_lower: str, spacy_analysis: dict, tag: str) -> bool:
    """Prüft ob ein mehrdeutiger Begriff zu einem bestimmten Tag passt
    
    Args:
        term: Der mehrdeutige Begriff
        text_lower: Der gesamte Text (lowercase)
        spacy_analysis: Ergebnis von analyze_with_spacy()
        tag: Die zu prüfende Tag-Kategorie
        
    Returns:
        True wenn der Begriff zum Tag passt, False sonst
    """
    if term not in AMBIGUOUS_TERMS:
        return True  # Kein mehrdeutiger Begriff
    
    rules = AMBIGUOUS_TERMS[term]
    
    # Prüfe auf ausgeschlossene Phrasen
    if 'exclude_phrases' in rules:
        for phrase in rules['exclude_phrases']:
            if phrase in text_lower:
                return False
    
    # Prüfe POS-Tags
    if 'exclude_pos' in rules and spacy_analysis.get('doc'):
        for token in spacy_analysis['doc']:
            if token.text == term and token.pos_ in rules['exclude_pos']:
                return False
    
    # Prüfe Entities
    if 'exclude_entities' in rules and spacy_analysis.get('entities'):
        for ent_text, ent_label in spacy_analysis['entities']:
            if term in ent_text and ent_label in rules['exclude_entities']:
                return False
    
    # Prüfe positive Kontext-Wörter für spezifischen Tag
    if tag in rules:
        context_words = rules[tag]
        for word in context_words:
            if word in text_lower:
                return True
        return False  # Kein positiver Kontext gefunden
    
    return True


def generate_tags(title: str, content: str) -> List[str]:
    """Generiert Tags basierend auf Titel und Inhalt mit spaCy-Analyse
    
    Args:
        title: Artikel-Titel
        content: Artikel-Inhalt
        
    Returns:
        Liste von generierten Tags
    """
    # Kombiniere Titel und Content für Analyse
    text_lower = (title + ' ' + content).lower()
    
    # spaCy-Analyse durchführen
    spacy_analysis = analyze_with_spacy(text_lower)
    
    matched_tags = []
    
    for tag, keywords in TAG_RULES.items():
        for keyword in keywords:
            if len(keyword) < 3:
                continue
            
            # Wortgrenzen-Match
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                # Prüfe ob mehrdeutiger Begriff und ob er zum Tag passt
                if check_ambiguous_term(keyword, text_lower, spacy_analysis, tag):
                    matched_tags.append(tag)
                    break
    
    return sorted(list(set(matched_tags)))


def add_auto_tags_if_empty(tags: List[str], title: str, content: str) -> List[str]:
    """Fügt automatische Tags hinzu, falls keine Tags angegeben sind
    
    Args:
        tags: Bestehende Tags (kann leer sein)
        title: Artikel-Titel
        content: Artikel-Inhalt
        
    Returns:
        Tags (entweder die bestehenden oder auto-generierte)
    """
    if tags and len(tags) > 0:
        return tags
    
    return generate_tags(title, content)
