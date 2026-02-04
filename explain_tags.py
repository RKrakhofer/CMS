#!/usr/bin/env python3
"""
Tag Explanation Tool - Zeigt welche Tags vergeben werden und warum

Verwendung:
    ./explain_tags.py "Mein Artikel-Text"
    echo "Mein Text" | ./explain_tags.py
    cat artikel.txt | ./explain_tags.py
"""
import sys
import re
from src.auto_tagger import TAG_RULES, NEGATIVE_CONTEXT, CONTEXT_WINDOW, check_negative_context


def explain_tags(text: str) -> dict:
    """Generiert Tags und erklärt die Gründe für jede Auswahl
    
    Args:
        text: Zu analysierender Text
        
    Returns:
        Dict mit Tag -> Liste von Gründen (gematchte Keywords)
    """
    text_lower = text.lower()
    tag_explanations = {}
    
    for tag, keywords in TAG_RULES.items():
        matched_keywords = []
        
        for keyword in keywords:
            if len(keyword) < 3:
                continue
            
            # Wortgrenzen-Match
            pattern = r'\b' + re.escape(keyword) + r'\b'
            match = re.search(pattern, text_lower)
            
            if match:
                # Prüfe auf negativen Kontext
                if check_negative_context(text_lower, keyword, tag, match.start()):
                    # Negativer Kontext gefunden - erkläre warum NICHT gematcht
                    continue
                else:
                    matched_keywords.append(keyword)
        
        if matched_keywords:
            tag_explanations[tag] = matched_keywords
    
    return tag_explanations


def main():
    # Text von Kommandozeile oder stdin lesen
    if len(sys.argv) > 1:
        # Text als Argument
        text = ' '.join(sys.argv[1:])
    else:
        # Text von stdin
        if sys.stdin.isatty():
            print("Verwendung:")
            print("  ./explain_tags.py \"Mein Artikel-Text\"")
            print("  echo \"Mein Text\" | ./explain_tags.py")
            print("  cat artikel.txt | ./explain_tags.py")
            sys.exit(1)
        text = sys.stdin.read()
    
    if not text.strip():
        print("FEHLER: Kein Text angegeben", file=sys.stderr)
        sys.exit(1)
    
    # Tags analysieren
    explanations = explain_tags(text)
    
    if not explanations:
        print("Keine Tags gefunden.")
        sys.exit(0)
    
    # Ausgabe formatieren
    for tag in sorted(explanations.keys()):
        keywords = explanations[tag]
        print(f"{tag}: [{', '.join(keywords)}]")


if __name__ == '__main__':
    main()
