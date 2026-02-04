#!/usr/bin/env python3
"""
Re-Tagging Script für alle Artikel
Wendet die verbesserte Auto-Tagger-Logik auf alle existierenden Artikel an
"""
import sys
sys.path.insert(0, '/app/src')

from db_manager import DatabaseManager
from auto_tagger import generate_tags

def main():
    db = DatabaseManager()
    articles = db.get_all_articles()

    print('=' * 80)
    print('Re-Tagging aller Artikel')
    print('=' * 80)
    print(f'Anzahl Artikel: {len(articles)}')
    print()

    updated = 0
    for article in articles:
        article_id = article['id']
        title = article['title']
        content = article['content']
        current_tags = article.get('tags', [])
        
        # Generiere neue Tags
        new_tags = generate_tags(title, content)
        
        # Nur updaten wenn Tags sich geändert haben
        if set(new_tags) != set(current_tags):
            db.update_article(article_id, tags=new_tags)
            updated += 1
            print(f'✓ Artikel {article_id}: {title[:70]}...')
            print(f'  Alt: {", ".join(current_tags) if current_tags else "keine"}')
            print(f'  Neu: {", ".join(new_tags) if new_tags else "keine"}')
            print()

    print('=' * 80)
    print(f'Fertig: {updated} von {len(articles)} Artikeln aktualisiert')
    print('=' * 80)

if __name__ == '__main__':
    main()
