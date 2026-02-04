#!/usr/bin/env python3
"""
Re-Tagging Script für importierte Artikel
Wendet Auto-Tagging auf Artikel an, die nur die generischen Tags haben.
"""

import sys
import os

# Füge src/ zum Path hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.db_manager import get_db_connection
from src.auto_tagger import generate_tags


def retag_articles(dry_run=True):
    """
    Wendet Auto-Tagging auf Artikel mit nur generischen Tags an.
    
    Args:
        dry_run: Wenn True, nur anzeigen was passieren würde
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Finde Artikel die nur "satire" und "fake-daily" tags haben
    cursor.execute("""
        SELECT id, title, content, tags 
        FROM articles 
        WHERE tags IS NOT NULL
    """)
    
    articles = cursor.fetchall()
    
    to_update = []
    
    for article in articles:
        article_id, title, content, tags_json = article
        
        # Parse tags
        import json
        try:
            current_tags = json.loads(tags_json) if tags_json else []
        except:
            current_tags = []
        
        # Prüfe ob nur generische Tags vorhanden
        generic_tags = {'satire', 'fake-daily', 'Satire'}
        if set(current_tags).issubset(generic_tags):
            # Generiere neue Tags
            new_tags = generate_tags(title, content)
            
            if new_tags and new_tags != current_tags:
                to_update.append({
                    'id': article_id,
                    'title': title,
                    'current_tags': current_tags,
                    'new_tags': new_tags
                })
    
    print(f"\n📊 Gefunden: {len(articles)} Artikel total")
    print(f"🏷️  Zu aktualisieren: {len(to_update)} Artikel\n")
    
    if not to_update:
        print("✓ Keine Artikel zum Aktualisieren gefunden.")
        conn.close()
        return
    
    # Zeige Preview
    print("Beispiele (erste 10):")
    for i, article in enumerate(to_update[:10], 1):
        print(f"\n{i}. ID {article['id']}: {article['title'][:60]}")
        print(f"   Alt: {article['current_tags']}")
        print(f"   Neu: {article['new_tags']}")
    
    if len(to_update) > 10:
        print(f"\n... und {len(to_update) - 10} weitere")
    
    if dry_run:
        print("\n⚠️  DRY RUN - Keine Änderungen vorgenommen")
        print("   Führe mit --execute aus um tatsächlich zu taggen")
    else:
        print("\n✓ Aktualisiere Tags...")
        
        import json
        for article in to_update:
            cursor.execute(
                "UPDATE articles SET tags = ? WHERE id = ?",
                (json.dumps(article['new_tags'], ensure_ascii=False), article['id'])
            )
        
        conn.commit()
        print(f"✓ {len(to_update)} Artikel aktualisiert")
    
    conn.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Re-Tagging für importierte Artikel')
    parser.add_argument('--execute', action='store_true', 
                        help='Tatsächlich updaten (sonst nur Preview)')
    
    args = parser.parse_args()
    
    retag_articles(dry_run=not args.execute)
