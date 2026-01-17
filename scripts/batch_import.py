#!/usr/bin/env python3
"""
Batch-Import von Artikeln aus JSON oder CSV
"""
import sys
import json
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db_manager import DatabaseManager

def import_from_json(json_file: str):
    """
    Importiert Artikel aus JSON-Datei
    
    Erwartetes Format:
    [
        {
            "title": "Artikel 1",
            "content": "# Content\n\nMarkdown...",
            "author": "Autor",
            "published": true,
            "tags": ["tag1", "tag2"]
        },
        ...
    ]
    """
    db = DatabaseManager()
    
    with open(json_file, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    imported = 0
    for article in articles:
        try:
            article_id = db.add_article(
                title=article['title'],
                content=article['content'],
                author=article.get('author'),
                published=article.get('published', False),
                tags=article.get('tags')
            )
            print(f"✓ Importiert: {article['title']} (ID: {article_id})")
            imported += 1
        except Exception as e:
            print(f"✗ Fehler bei '{article.get('title', 'unbekannt')}': {e}")
    
    print(f"\n✓ {imported} Artikel erfolgreich importiert")
    return imported

def import_from_csv(csv_file: str):
    """
    Importiert Artikel aus CSV-Datei
    
    Erwartete Spalten: title, content, author, published, tags
    """
    db = DatabaseManager()
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        imported = 0
        
        for row in reader:
            try:
                tags = row.get('tags', '').split(',') if row.get('tags') else None
                tags = [t.strip() for t in tags] if tags else None
                
                published = row.get('published', '').lower() in ['true', '1', 'yes']
                
                article_id = db.add_article(
                    title=row['title'],
                    content=row['content'],
                    author=row.get('author'),
                    published=published,
                    tags=tags
                )
                print(f"✓ Importiert: {row['title']} (ID: {article_id})")
                imported += 1
            except Exception as e:
                print(f"✗ Fehler bei '{row.get('title', 'unbekannt')}': {e}")
        
        print(f"\n✓ {imported} Artikel erfolgreich importiert")
        return imported

def create_example_json():
    """Erstellt eine Beispiel-JSON-Datei"""
    examples = [
        {
            "title": "Erste Nachricht",
            "content": "# Breaking News\n\nDies ist die erste Nachricht.",
            "author": "Reporter 1",
            "published": True,
            "tags": ["news", "wichtig"]
        },
        {
            "title": "Tech-Update",
            "content": "## Neue Technologie\n\nSpannende Entwicklungen...",
            "author": "Tech-Team",
            "published": False,
            "tags": ["tech", "innovation"]
        }
    ]
    
    example_path = Path(__file__).parent.parent / "example_articles.json"
    with open(example_path, 'w', encoding='utf-8') as f:
        json.dump(examples, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Beispiel-Datei erstellt: {example_path}")
    return example_path

def main():
    """Beispiel-Nutzung"""
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        
        if file_path.endswith('.json'):
            import_from_json(file_path)
        elif file_path.endswith('.csv'):
            import_from_csv(file_path)
        else:
            print("Unterstütztes Format: .json oder .csv")
    else:
        print("Erstelle Beispiel-Datei...")
        example_file = create_example_json()
        print(f"\nZum Importieren ausführen:")
        print(f"  python {sys.argv[0]} {example_file}")

if __name__ == "__main__":
    main()
