#!/usr/bin/env python3
"""
Re-Tagging Script über API
Wendet Auto-Tagging auf Artikel mit nur generischen Tags an.
"""

import requests
import json
import sys
import os

# Füge src/ zum Path hinzu für auto_tagger
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.auto_tagger import generate_tags


def retag_articles(server_url, dry_run=True):
    """
    Wendet Auto-Tagging auf Artikel mit nur generischen Tags an.
    
    Args:
        server_url: URL zum CMS-Server (z.B. http://stage:5001/cms)
        dry_run: Wenn True, nur anzeigen was passieren würde
    """
    
    # 1. Alle Artikel abrufen
    print(f"📥 Rufe Artikel ab von {server_url}...")
    
    response = requests.get(f"{server_url}/admin/api/articles")
    if response.status_code != 200:
        print(f"❌ Fehler beim Abrufen: {response.status_code}")
        return
    
    data = response.json()
    articles = data.get('articles', [])
    
    print(f"✓ {len(articles)} Artikel geladen\n")
    
    # 2. Artikel filtern die nur generische Tags haben
    to_update = []
    generic_tags = {'satire', 'fake-daily', 'Satire'}
    
    for article in articles:
        current_tags = article.get('tags', [])
        
        # Prüfe ob nur generische Tags vorhanden
        if set(current_tags).issubset(generic_tags):
            # Generiere neue Tags
            new_tags = generate_tags(article['title'], article['content'])
            
            if new_tags and new_tags != current_tags:
                to_update.append({
                    'id': article['id'],
                    'title': article['title'],
                    'current_tags': current_tags,
                    'new_tags': new_tags
                })
    
    print(f"🏷️  Zu aktualisieren: {len(to_update)} Artikel\n")
    
    if not to_update:
        print("✓ Keine Artikel zum Aktualisieren gefunden.")
        return
    
    # 3. Preview anzeigen
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
        return
    
    # 4. Tags aktualisieren
    print("\n✓ Aktualisiere Tags...\n")
    
    success_count = 0
    error_count = 0
    
    for article in to_update:
        # Update via API
        update_data = {
            'title': article['title'],
            'tags': article['new_tags']
        }
        
        response = requests.put(
            f"{server_url}/admin/api/articles/{article['id']}/tags",
            json=update_data
        )
        
        if response.status_code == 200:
            success_count += 1
            print(f"  ✓ ID {article['id']}: {article['title'][:50]}")
        else:
            error_count += 1
            print(f"  ✗ ID {article['id']}: Fehler {response.status_code}")
    
    print(f"\n{'='*60}")
    print(f"✓ Abgeschlossen: {success_count} erfolgreich, {error_count} Fehler")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Re-Tagging für importierte Artikel via API')
    parser.add_argument('--server', '-s', default='http://stage:5001/cms',
                        help='CMS Server URL (default: http://stage:5001/cms)')
    parser.add_argument('--execute', action='store_true', 
                        help='Tatsächlich updaten (sonst nur Preview)')
    
    args = parser.parse_args()
    
    retag_articles(args.server, dry_run=not args.execute)
