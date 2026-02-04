"""
Auto-Tagging für Artikel basierend auf Inhalt und Titel mit Kontextanalyse
"""
import re
import json
import os
from typing import List, Dict

# Lade Tag-Regeln aus JSON-Datei
def load_tag_rules():
    """Lädt Tag-Regeln und negative Kontext-Regeln aus JSON-Datei"""
    config_path = os.path.join(os.path.dirname(__file__), 'tag_rules.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config['tag_rules'], config['negative_context'], config['context_window']

# Lade Konfiguration beim Import
TAG_RULES, NEGATIVE_CONTEXT, CONTEXT_WINDOW = load_tag_rules()


def check_negative_context(text_lower: str, keyword: str, tag: str, match_pos: int) -> bool:
    """Prüft, ob negative Kontextwörter in der Nähe des Keywords stehen
    
    Args:
        text_lower: Der gesamte Text (lowercase)
        keyword: Das gefundene Keyword
        tag: Die Tag-Kategorie
        match_pos: Position des Matches im Text
        
    Returns:
        True wenn negativer Kontext gefunden wurde (Tag NICHT vergeben), False sonst
    """
    if tag not in NEGATIVE_CONTEXT or keyword not in NEGATIVE_CONTEXT[tag]:
        return False  # Keine negativen Regeln für dieses Keyword
    
    negative_words = NEGATIVE_CONTEXT[tag][keyword]
    
    # Extrahiere Text rund um das Keyword (±CONTEXT_WINDOW Wörter)
    words = text_lower.split()
    # Finde die Wortposition des Keywords
    text_before_match = text_lower[:match_pos]
    word_index = len(text_before_match.split())
    
    # Bestimme Start- und End-Index für Kontextfenster
    start_idx = max(0, word_index - CONTEXT_WINDOW)
    end_idx = min(len(words), word_index + CONTEXT_WINDOW + 1)
    
    context_words = words[start_idx:end_idx]
    context_text = ' '.join(context_words)
    
    # Prüfe ob eines der negativen Wörter im Kontext vorkommt
    for neg_word in negative_words:
        if re.search(r'\b' + re.escape(neg_word) + r'\b', context_text):
            return True  # Negativer Kontext gefunden
    
    return False


def generate_tags(title: str, content: str) -> List[str]:
    """Generiert Tags basierend auf Titel und Inhalt mit Kontextanalyse
    
    Args:
        title: Artikel-Titel
        content: Artikel-Inhalt
        
    Returns:
        Liste von generierten Tags
    """
    # Kombiniere Titel und Content für Analyse
    text_lower = (title + ' ' + content).lower()
    matched_tags = []
    
    for tag, keywords in TAG_RULES.items():
        for keyword in keywords:
            if len(keyword) < 3:
                continue  # Ignoriere Keywords mit weniger als 3 Buchstaben
            
            # Verwende Wortgrenzen-Regex, um nur vollständige Wörter zu matchen
            # \b = Wortgrenze (verhindert Matches in Teilwörtern)
            pattern = r'\b' + re.escape(keyword) + r'\b'
            match = re.search(pattern, text_lower)
            
            if match:
                # Prüfe auf negativen Kontext
                if check_negative_context(text_lower, keyword, tag, match.start()):
                    continue  # Überspringe diesen Tag wegen negativem Kontext
                
                matched_tags.append(tag)
                break  # Ein Match pro Tag-Kategorie reicht
    
    # Entferne Duplikate und sortiere
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
    # Wenn bereits Tags vorhanden sind, diese zurückgeben
    if tags and len(tags) > 0:
        return tags
    
    # Ansonsten Auto-Tagging verwenden
    return generate_tags(title, content)
