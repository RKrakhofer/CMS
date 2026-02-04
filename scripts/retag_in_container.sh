#!/bin/bash
#
# Re-Tagging Script für importierte Artikel
# Führt Auto-Tagging direkt in der Container-Datenbank aus
#

cd /app && python3 << 'PYTHON_SCRIPT'
import sqlite3
import json
import sys
sys.path.insert(0, '/app')

from src.auto_tagger import generate_tags

# DB öffnen
conn = sqlite3.connect('/app/database/articles.db')
cursor = conn.cursor()

# Artikel mit nur generischen Tags finden
cursor.execute("""
    SELECT id, title, content, tags 
    FROM articles 
    WHERE tags IS NOT NULL
""")

articles = cursor.fetchall()

to_update = []
generic_tags = {'satire', 'fake-daily', 'Satire'}

for article in articles:
    article_id, title, content, tags_json = article
    
    try:
        current_tags = json.loads(tags_json) if tags_json else []
    except:
        current_tags = []
    
    # Nur Artikel mit generischen Tags
    if set(current_tags).issubset(generic_tags):
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
    exit(0)

# Preview
print("Beispiele (erste 10):")
for i, article in enumerate(to_update[:10], 1):
    print(f"\n{i}. ID {article['id']}: {article['title'][:60]}")
    print(f"   Alt: {article['current_tags']}")
    print(f"   Neu: {article['new_tags']}")

if len(to_update) > 10:
    print(f"\n... und {len(to_update) - 10} weitere")

# Update durchführen
print("\n✓ Aktualisiere Tags...")

for article in to_update:
    cursor.execute(
        "UPDATE articles SET tags = ? WHERE id = ?",
        (json.dumps(article['new_tags'], ensure_ascii=False), article['id'])
    )

conn.commit()
print(f"✓ {len(to_update)} Artikel aktualisiert")

conn.close()
PYTHON_SCRIPT
