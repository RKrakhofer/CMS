"""
Database Manager für CMS
Verwaltet Artikel und Bilder
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

class DatabaseManager:
    """Verwaltet alle Datenbank-Operationen"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "database" / "articles.db"
        self.db_path = db_path
    
    def get_connection(self):
        """Erstellt eine neue DB-Verbindung"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Ermöglicht dict-ähnlichen Zugriff
        return conn
    
    # ===== Artikel-Operationen =====
    
    def add_article(self, title: str, content: str, author: str = None, 
                   published: bool = False, tags: List[str] = None) -> int:
        """Fügt einen neuen Artikel hinzu"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        tags_json = json.dumps(tags) if tags else None
        
        cursor.execute("""
            INSERT INTO articles (title, content, author, published, tags)
            VALUES (?, ?, ?, ?, ?)
        """, (title, content, author, published, tags_json))
        
        article_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return article_id
    
    def get_article(self, article_id: int) -> Optional[Dict[str, Any]]:
        """Holt einen einzelnen Artikel"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            article = dict(row)
            if article.get('tags'):
                # Prüfe ob Tags bereits als JSON gespeichert sind oder als einfacher String
                try:
                    article['tags'] = json.loads(article['tags'])
                except (json.JSONDecodeError, TypeError):
                    # Falls kein JSON, konvertiere String zu Liste (z.B. "Politik, Satire" -> ["Politik", "Satire"])
                    article['tags'] = [tag.strip() for tag in article['tags'].split(',') if tag.strip()]
            else:
                article['tags'] = []
            return article
        return None
    
    def get_all_articles(self, published_only: bool = False) -> List[Dict[str, Any]]:
        """Holt alle Artikel"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if published_only:
            cursor.execute("SELECT * FROM articles WHERE published = 1 ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM articles ORDER BY created_at DESC")
        
        rows = cursor.fetchall()
        conn.close()
        
        articles = []
        for row in rows:
            article = dict(row)
            if article.get('tags'):
                # Prüfe ob Tags bereits als JSON gespeichert sind oder als einfacher String
                try:
                    article['tags'] = json.loads(article['tags'])
                except (json.JSONDecodeError, TypeError):
                    # Falls kein JSON, konvertiere String zu Liste (z.B. "Politik, Satire" -> ["Politik", "Satire"])
                    article['tags'] = [tag.strip() for tag in article['tags'].split(',') if tag.strip()]
            else:
                article['tags'] = []
            articles.append(article)
        
        return articles
    
    def get_articles_by_tag(self, tag: str, published_only: bool = False) -> List[Dict[str, Any]]:
        """Holt alle Artikel mit einem bestimmten Tag"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if published_only:
            cursor.execute("SELECT * FROM articles WHERE published = 1 ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM articles ORDER BY created_at DESC")
        
        rows = cursor.fetchall()
        conn.close()
        
        articles = []
        for row in rows:
            article = dict(row)
            # Tags parsen
            if article.get('tags'):
                try:
                    article['tags'] = json.loads(article['tags'])
                except (json.JSONDecodeError, TypeError):
                    article['tags'] = [t.strip() for t in article['tags'].split(',') if t.strip()]
            else:
                article['tags'] = []
            
            # Prüfe ob der gesuchte Tag im Artikel vorhanden ist (case-insensitive)
            if any(t.lower() == tag.lower() for t in article['tags']):
                articles.append(article)
        
        return articles
    
    def update_article(self, article_id: int, **kwargs) -> bool:
        """Aktualisiert einen Artikel"""
        allowed_fields = ['title', 'content', 'author', 'published', 'tags', 'created_at']
        updates = []
        values = []
        created_at_value = None
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                if key == 'tags':
                    value = json.dumps(value)
                elif key == 'created_at':
                    if value:  # Wenn created_at übergeben wird
                        # HTML5 datetime-local Format: '2024-01-17T10:30' -> SQLite: '2024-01-17 10:30:00'
                        try:
                            from datetime import datetime
                            dt = datetime.strptime(value, '%Y-%m-%dT%H:%M')
                            value = dt.strftime('%Y-%m-%d %H:%M:%S')
                            created_at_value = value
                        except:
                            continue  # Bei Fehler created_at nicht updaten
                    else:
                        continue  # Leerer Wert wird ignoriert
                updates.append(f"{key} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        # Wenn created_at gesetzt wurde, setze updated_at auf denselben Wert
        # Ansonsten setze updated_at auf aktuellen Zeitstempel
        if created_at_value:
            updates.append("updated_at = ?")
            values.append(created_at_value)
        else:
            updates.append("updated_at = CURRENT_TIMESTAMP")
        
        values.append(article_id)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = f"UPDATE articles SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_article(self, article_id: int) -> bool:
        """Löscht einen Artikel und zugehörige Bilder"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success
    
    # ===== Bild-Operationen =====
    
    def add_image(self, article_id: int, filename: str, filepath: str,
                 alt_text: str = None, caption: str = None) -> int:
        """Fügt ein Bild hinzu"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO images (article_id, filename, filepath, alt_text, caption)
            VALUES (?, ?, ?, ?, ?)
        """, (article_id, filename, filepath, alt_text, caption))
        
        image_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return image_id
    
    def get_images_for_article(self, article_id: int) -> List[Dict[str, Any]]:
        """Holt alle Bilder eines Artikels"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM images WHERE article_id = ?", (article_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def delete_image(self, image_id: int) -> bool:
        """Löscht ein Bild aus der DB"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success
    
    # ===== Suche =====
    
    def search_articles(self, query: str) -> List[Dict[str, Any]]:
        """Sucht nach Artikeln (Titel oder Inhalt) - vollständig case-insensitive auch für Umlaute"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Hole alle Artikel und filtere in Python für echte Unicode-case-insensitive Suche
        cursor.execute("SELECT * FROM articles ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        # Case-insensitive Suche in Python
        query_lower = query.lower()
        
        articles = []
        for row in rows:
            article = dict(row)
            # Prüfe ob Query in Titel oder Inhalt vorkommt (case-insensitive)
            if (query_lower in article['title'].lower() if article['title'] else False) or \
               (query_lower in article['content'].lower() if article['content'] else False):
                
                if article['tags']:
                    # Prüfe ob Tags bereits als JSON gespeichert sind oder als einfacher String
                    try:
                        article['tags'] = json.loads(article['tags'])
                    except (json.JSONDecodeError, TypeError):
                        # Falls kein JSON, konvertiere String zu Liste (z.B. "Politik, Satire" -> ["Politik", "Satire"])
                        article['tags'] = [tag.strip() for tag in article['tags'].split(',') if tag.strip()]
                articles.append(article)
        
        return articles
    
    def get_article_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Holt einen Artikel nach exaktem Titel"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM articles WHERE title = ?", (title,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            article = dict(row)
            if article['tags']:
                try:
                    article['tags'] = json.loads(article['tags'])
                except (json.JSONDecodeError, TypeError):
                    article['tags'] = [tag.strip() for tag in article['tags'].split(',') if tag.strip()]
            return article
        return None
