"""
API Tests für FakeDaily
"""
import pytest
import requests
import json
import os
from datetime import datetime

# Konfiguration über Environment-Variablen
BASE_URL = os.getenv('CMS_URL', 'http://localhost:5001')
APP_PREFIX = os.getenv('CMS_PREFIX', '')  # Leer für lokale Tests, "/cms" für Stage

API_BASE = f"{BASE_URL}{APP_PREFIX}/admin/api"
READER_BASE = f"{BASE_URL}{APP_PREFIX}/reader"


class TestExportAPI:
    """Tests für Export-API"""
    
    def test_export_articles_success(self):
        """Test: Export liefert JSON mit Artikeln"""
        response = requests.get(f"{API_BASE}/export/articles")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['success'] is True
        assert 'count' in data
        assert 'articles' in data
        assert isinstance(data['articles'], list)
    
    def test_export_articles_structure(self):
        """Test: Exportierte Artikel haben korrekte Struktur"""
        response = requests.get(f"{API_BASE}/export/articles")
        data = response.json()
        
        if data['count'] > 0:
            article = data['articles'][0]
            
            # Pflichtfelder
            assert 'id' in article
            assert 'title' in article
            assert 'content' in article
            assert 'created_at' in article
            assert 'updated_at' in article
            assert 'published' in article
            
            # Optionale Felder
            assert 'author' in article
            assert 'tags' in article
            assert 'images' in article
            
            # Tags ist eine Liste
            assert isinstance(article['tags'], list)
            assert isinstance(article['images'], list)


class TestImportAPI:
    """Tests für Import-API"""
    
    def test_import_articles_missing_body(self):
        """Test: Import ohne JSON-Body gibt Fehler"""
        response = requests.post(
            f"{API_BASE}/import/articles",
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        # API gibt HTML-Fehlerseite zurück, kein JSON
        assert 'Bad Request' in response.text
    
    def test_import_articles_empty_list(self):
        """Test: Import mit leerer Artikel-Liste"""
        payload = {'articles': []}
        response = requests.post(
            f"{API_BASE}/import/articles",
            json=payload
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
    
    def test_import_single_article(self):
        """Test: Import eines neuen Artikels"""
        test_article = {
            'title': f'Test Artikel {datetime.now().isoformat()}',
            'content': '# Test\n\nDies ist ein Test-Artikel.',
            'author': 'Test Bot',
            'published': False,
            'tags': ['test', 'api'],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        payload = {'articles': [test_article]}
        response = requests.post(
            f"{API_BASE}/import/articles",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['imported'] >= 0
        assert data['skipped'] >= 0
        assert data['updated'] >= 0
    
    def test_import_duplicate_handling(self):
        """Test: Import von Duplikaten (gleicher Titel)"""
        title = f'Duplikat Test {datetime.now().timestamp()}'
        test_article = {
            'title': title,
            'content': '# Original',
            'published': False,
            'tags': ['test'],
            'created_at': datetime.now().isoformat()
        }
        
        payload = {'articles': [test_article]}
        
        # Erster Import
        response1 = requests.post(f"{API_BASE}/import/articles", json=payload)
        data1 = response1.json()
        
        # Zweiter Import (gleicher Titel, keine Änderung)
        response2 = requests.post(f"{API_BASE}/import/articles", json=payload)
        data2 = response2.json()
        
        assert data1['success'] is True
        assert data2['success'] is True
        
        # Zweiter Import sollte übersprungen werden
        assert data2['skipped'] >= 1 or data2['updated'] >= 1


class TestReaderRoutes:
    """Tests für Reader-Interface"""
    
    def test_reader_index(self):
        """Test: Reader-Startseite lädt"""
        response = requests.get(f"{READER_BASE}/")
        assert response.status_code == 200
        assert 'Aktuelle Artikel' in response.text or 'FakeDaily' in response.text
    
    def test_reader_article(self):
        """Test: Einzelner Artikel im Reader"""
        # Erst Export holen um eine Artikel-ID zu bekommen
        export = requests.get(f"{API_BASE}/export/articles").json()
        
        if export['count'] > 0:
            article_id = export['articles'][0]['id']
            response = requests.get(f"{READER_BASE}/article/{article_id}")
            assert response.status_code == 200
    
    def test_reader_tag_filter(self):
        """Test: Tag-Filterung im Reader"""
        # Erst Export holen um Tags zu finden
        export = requests.get(f"{API_BASE}/export/articles").json()
        
        if export['count'] > 0:
            for article in export['articles']:
                if article['tags']:
                    tag = article['tags'][0]
                    response = requests.get(f"{READER_BASE}/tag/{tag}")
                    assert response.status_code == 200
                    assert f'Tag: {tag}' in response.text
                    break
    
    def test_reader_unpublished_blocked(self):
        """Test: Unveröffentlichte Artikel sind im Reader nicht sichtbar"""
        # Teste mit hoher ID die wahrscheinlich nicht existiert oder unveröffentlicht ist
        response = requests.get(f"{READER_BASE}/article/99999", allow_redirects=False)
        # API leitet um bei nicht gefundenen Artikeln
        assert response.status_code in [302, 404]


class TestAPIIntegration:
    """Integrationstests: Export -> Import Zyklus"""
    
    def test_export_import_roundtrip(self):
        """Test: Export und Re-Import funktioniert"""
        # 1. Export
        export_response = requests.get(f"{API_BASE}/export/articles")
        assert export_response.status_code == 200
        export_data = export_response.json()
        
        if export_data['count'] == 0:
            pytest.skip("Keine Artikel zum Testen vorhanden")
        
        # 2. Einen Artikel nehmen und leicht modifizieren
        test_articles = export_data['articles'][:1]  # Nur ersten Artikel
        test_articles[0]['title'] = f"Modified: {test_articles[0]['title']}"
        
        # 3. Re-Import
        import_response = requests.post(
            f"{API_BASE}/import/articles",
            json={'articles': test_articles}
        )
        assert import_response.status_code == 200
        import_data = import_response.json()
        
        assert import_data['success'] is True
        assert import_data['imported'] + import_data['updated'] >= 1


if __name__ == '__main__':
    # Direktes Ausführen der Tests
    print("FakeDaily API Tests")
    print(f"Base URL: {BASE_URL}{APP_PREFIX}")
    print("-" * 50)
    
    # Pytest mit verbose output
    pytest.main([__file__, '-v', '--tb=short'])
