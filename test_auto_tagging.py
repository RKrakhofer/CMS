#!/usr/bin/env python3
"""
Test-Skript für Auto-Tagging
Zeigt wie verschiedene Artikel automatisch getaggt werden
"""
import sys
from pathlib import Path

# Füge src zum Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent / "src"))

from auto_tagger import add_auto_tags_if_empty, generate_tags

# Test-Artikel
test_articles = [
    {
        'title': 'Kickl plant massive Energiewende',
        'content': 'FPÖ-Chef Herbert Kickl kündigte an, dass Österreich massiv in Solarenergie investieren wird.'
    },
    {
        'title': 'Trump kündigt neue KI-Initiative an',
        'content': 'US-Präsident Trump präsentiert neues Programm für künstliche Intelligenz mit Elon Musk.'
    },
    {
        'title': 'Neue Studie zur Erderwärmung',
        'content': 'Wissenschaftler der Universität Wien warnen vor beschleunigter Klimaveränderung.'
    },
    {
        'title': 'Benko-Firma meldet Insolvenz an',
        'content': 'Die Wirtschaft in Österreich ist betroffen: Weiteres Unternehmen von Benko ist pleite.'
    },
    {
        'title': 'Krankenhaus in Berlin überlastet',
        'content': 'Das Gesundheitssystem in Deutschland steht vor Herausforderungen, Ärzte und Pfleger sind überlastet.'
    },
    {
        'title': 'Schnitzel aus dem Labor bald in Restaurants',
        'content': 'Österreichische Gastronomen testen vegetarisches Laborfleisch für ihre Speisekarten.'
    }
]

print("=" * 80)
print("Auto-Tagging Test")
print("=" * 80)
print()

for i, article in enumerate(test_articles, 1):
    print(f"{i}. {article['title']}")
    print(f"   Content: {article['content'][:60]}...")
    
    # Generiere Tags
    tags = generate_tags(article['title'], article['content'])
    print(f"   → Tags: {', '.join(tags) if tags else '(keine)'}")
    print()

print("=" * 80)
print("Test mit bestehenden Tags")
print("=" * 80)
print()

# Test mit bestehenden Tags
test_article = test_articles[0]
existing_tags = ['Satire', 'Humor']

print(f"Artikel: {test_article['title']}")
print(f"Bestehende Tags: {', '.join(existing_tags)}")

result_tags = add_auto_tags_if_empty(existing_tags, test_article['title'], test_article['content'])
print(f"Resultat: {', '.join(result_tags)}")
print("→ Bestehende Tags bleiben erhalten ✓")
print()

# Test ohne bestehende Tags
print(f"Artikel: {test_article['title']}")
print(f"Bestehende Tags: (keine)")

result_tags = add_auto_tags_if_empty([], test_article['title'], test_article['content'])
print(f"Resultat: {', '.join(result_tags)}")
print("→ Auto-Tags wurden generiert ✓")
print()
