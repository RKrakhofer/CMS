#!/usr/bin/env python3
"""
Initialisiert die SQLite-Datenbank für FakeDaily
"""
import sqlite3
import os
from pathlib import Path

# Pfad zur Datenbank
DB_PATH = Path(__file__).parent.parent / "database" / "articles.db"

def init_database():
    """Erstellt die Datenbank und Tabellen"""
    
    # Sicherstellen, dass der database-Ordner existiert
    DB_PATH.parent.mkdir(exist_ok=True)
    
    # Verbindung zur Datenbank
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Articles Tabelle
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published BOOLEAN DEFAULT 0,
            tags TEXT
        )
    """)
    
    # Images Tabelle
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            alt_text TEXT,
            caption TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
        )
    """)
    
    # Index für schnellere Suche
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_published 
        ON articles(published)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_images_article 
        ON images(article_id)
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✓ Datenbank erfolgreich initialisiert: {DB_PATH}")

if __name__ == "__main__":
    init_database()
