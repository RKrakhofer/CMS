"""
Umfassende API-Endpoint-Tests für FakeDaily
Testet alle API-Routen inkl. Upload und WhatsApp-Export
"""
import pytest
import requests
import json
import os
import tempfile
from pathlib import Path
from PIL import Image

# Konfiguration über Environment-Variablen
BASE_URL = os.getenv('CMS_URL', 'http://localhost:5001')
APP_PREFIX = os.getenv('CMS_PREFIX', '')

API_BASE = f"{BASE_URL}{APP_PREFIX}/admin/api"
ADMIN_BASE = f"{BASE_URL}{APP_PREFIX}/admin"
READER_BASE = f"{BASE_URL}{APP_PREFIX}/reader"
MEDIA_BASE = f"{BASE_URL}{APP_PREFIX}/media"


@pytest.fixture
def test_article_data():
    """Test-Artikel-Daten"""
    return {
        'title': f'API Test Artikel {os.getpid()}',
        'content': '# Test\n\n**Bold** und *italic* Text.\n\n- Liste\n- Item',
        'author': 'Test Author',
        'published': True,
        'tags': ['test', 'api', 'pytest']
    }


@pytest.fixture
def test_image_file():
    """Erstellt temporäres Test-Bild"""
    # Temp-Bild erstellen
    img = Image.new('RGB', (100, 100), color='blue')
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    img.save(temp_file.name, 'JPEG')
    temp_file.close()
    
    yield temp_file.name
    
    # Cleanup
    try:
        os.unlink(temp_file.name)
    except:
        pass


class TestExportImportAPI:
    """Tests für Export/Import API Endpoints"""
    
    def test_export_articles_endpoint(self):
        """Test: GET /admin/api/export/articles"""
        response = requests.get(f"{API_BASE}/export/articles")
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        
        data = response.json()
        assert 'success' in data
        assert data['success'] is True
        assert 'count' in data
        assert 'articles' in data
        assert isinstance(data['articles'], list)

        if data['count'] > 0:
            article = data['articles'][0]
            required_fields = ['id', 'title', 'content', 'created_at', 'updated_at', 
                             'published', 'author', 'tags', 'images']
            for field in required_fields:
                assert field in article, f"Feld '{field}' fehlt in Artikel"
    
    def test_import_articles_endpoint_empty(self):
        """Test: POST /admin/api/import/articles mit leerer Liste"""
        payload = {'articles': []}
        response = requests.post(
            f"{API_BASE}/import/articles",
            json=payload
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
    
    def test_import_articles_endpoint_invalid_json(self):
        """Test: Import mit ungültigem JSON"""
        response = requests.post(
            f"{API_BASE}/import/articles",
            data="invalid json",
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code in [400, 500]
    
    def test_import_articles_endpoint_missing_articles_key(self):
        """Test: Import ohne 'articles' Key"""
        payload = {'data': []}
        response = requests.post(
            f"{API_BASE}/import/articles",
            json=payload
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False


class TestUploadAPI:
    """Tests für Upload API Endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup_cleanup(self):
        """Setup und Cleanup für Upload-Tests"""
        self.created_article_ids = []
        yield
        # Cleanup: Erstellte Artikel löschen
        for article_id in self.created_article_ids:
            try:
                requests.post(f"{ADMIN_BASE}/article/{article_id}/delete")
            except:
                pass
    
    def test_upload_images_endpoint_success(self, test_article_data, test_image_file):
        """Test: POST /admin/api/upload/images/<article_id>"""
        # Erst Artikel erstellen via Import
        import_response = requests.post(
            f"{API_BASE}/import/articles",
            json={'articles': [test_article_data]}
        )
        import_data = import_response.json()
        assert import_data['success'] is True
        
        # Artikel-ID aus der Datenbank holen
        export_response = requests.get(f"{API_BASE}/export/articles")
        articles = export_response.json()['articles']
        article_id = next(a['id'] for a in articles if a['title'] == test_article_data['title'])
        self.created_article_ids.append(article_id)
        
        # Bild hochladen
        with open(test_image_file, 'rb') as f:
            files = {'images': ('test.jpg', f, 'image/jpeg')}
            response = requests.post(
                f"{API_BASE}/upload/images/{article_id}",
                files=files
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'uploaded' in data
        assert data['uploaded'] == 1
        assert 'images' in data
        assert len(data['images']) == 1
    
    def test_upload_images_endpoint_multiple_files(self, test_article_data, test_image_file):
        """Test: Upload mehrerer Bilder"""
        # Artikel erstellen
        import_response = requests.post(
            f"{API_BASE}/import/articles",
            json={'articles': [test_article_data]}
        )
        
        # Artikel-ID aus der Datenbank holen
        export_response = requests.get(f"{API_BASE}/export/articles")
        articles = export_response.json()['articles']
        article_id = next(a['id'] for a in articles if a['title'] == test_article_data['title'])
        self.created_article_ids.append(article_id)
        
        # Mehrere Bilder hochladen
        with open(test_image_file, 'rb') as f1, open(test_image_file, 'rb') as f2:
            files = [
                ('images', ('test1.jpg', f1, 'image/jpeg')),
                ('images', ('test2.jpg', f2, 'image/jpeg'))
            ]
            response = requests.post(
                f"{API_BASE}/upload/images/{article_id}",
                files=files
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data['uploaded'] == 2
    
    def test_upload_images_endpoint_nonexistent_article(self, test_image_file):
        """Test: Upload für nicht existierenden Artikel"""
        with open(test_image_file, 'rb') as f:
            files = {'images': ('test.jpg', f, 'image/jpeg')}
            response = requests.post(
                f"{API_BASE}/upload/images/999999",
                files=files
            )
        
        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False
    
    def test_upload_images_endpoint_no_files(self, test_article_data):
        """Test: Upload ohne Dateien"""
        # Artikel erstellen
        import_response = requests.post(
            f"{API_BASE}/import/articles",
            json={'articles': [test_article_data]}
        )
        
        # Artikel-ID aus der Datenbank holen
        export_response = requests.get(f"{API_BASE}/export/articles")
        articles = export_response.json()['articles']
        article_id = next(a['id'] for a in articles if a['title'] == test_article_data['title'])
        self.created_article_ids.append(article_id)
        
        # Upload ohne Dateien
        response = requests.post(f"{API_BASE}/upload/images/{article_id}")
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
    
    def test_upload_images_endpoint_invalid_file_type(self, test_article_data):
        """Test: Upload mit ungültigem Dateityp"""
        # Artikel erstellen
        import_response = requests.post(
            f"{API_BASE}/import/articles",
            json={'articles': [test_article_data]}
        )
        
        # Artikel-ID aus der Datenbank holen
        export_response = requests.get(f"{API_BASE}/export/articles")
        articles = export_response.json()['articles']
        article_id = next(a['id'] for a in articles if a['title'] == test_article_data['title'])
        self.created_article_ids.append(article_id)
        
        # Textdatei als "Bild" hochladen
        files = {'images': ('test.txt', b'Not an image', 'text/plain')}
        response = requests.post(
            f"{API_BASE}/upload/images/{article_id}",
            files=files
        )
        
        # Sollte entweder ablehnen oder akzeptieren aber nicht speichern
        assert response.status_code in [200, 400]


class TestMediaEndpoint:
    """Tests für Media-Serving Endpoint"""
    
    def test_media_images_endpoint_existing_image(self):
        """Test: GET /media/images/<filename> für existierendes Bild"""
        # Erst prüfen ob überhaupt Bilder existieren
        export_response = requests.get(f"{API_BASE}/export/articles")
        articles = export_response.json()['articles']
        
        image_found = False
        for article in articles:
            if article.get('images'):
                for img in article['images']:
                    # Versuche Bild-URL zu extrahieren
                    if 'url' in img:
                        img_url = img['url']
                        response = requests.get(img_url)
                        
                        if response.status_code == 200:
                            assert response.headers['Content-Type'].startswith('image/')
                            assert len(response.content) > 0
                            image_found = True
                            break
            if image_found:
                break
        
        if not image_found:
            pytest.skip("Keine Bilder in der Datenbank gefunden")
    
    def test_media_images_endpoint_nonexistent_image(self):
        """Test: GET /media/images/<filename> für nicht existierendes Bild"""
        response = requests.get(f"{MEDIA_BASE}/images/nonexistent_image_12345.jpg")
        
        assert response.status_code == 404


class TestReaderEndpoints:
    """Tests für Reader/Public API Endpoints"""
    
    def test_reader_index_endpoint(self):
        """Test: GET /reader/ liefert HTML"""
        response = requests.get(f"{READER_BASE}/")
        
        assert response.status_code == 200
        assert 'text/html' in response.headers['Content-Type']
        assert len(response.text) > 0
    
    def test_reader_tag_endpoint(self):
        """Test: GET /reader/tag/<tag> funktioniert"""
        # Hole Export um zu sehen welche Tags existieren
        export_response = requests.get(f"{API_BASE}/export/articles")
        articles = export_response.json()['articles']
        
        tag_found = False
        for article in articles:
            if article.get('tags') and len(article['tags']) > 0:
                tag = article['tags'][0]
                response = requests.get(f"{READER_BASE}/tag/{tag}")
                
                assert response.status_code == 200
                assert 'text/html' in response.headers['Content-Type']
                tag_found = True
                break
        
        if not tag_found:
            pytest.skip("Keine Tags in Artikeln gefunden")
    
    def test_reader_tag_endpoint_nonexistent(self):
        """Test: GET /reader/tag/<tag> für nicht existierenden Tag"""
        response = requests.get(f"{READER_BASE}/tag/nonexistent_tag_xyz_12345")
        
        # Sollte 200 mit leerer Liste oder 404 zurückgeben
        assert response.status_code in [200, 404]
    
    def test_reader_article_endpoint(self):
        """Test: GET /reader/article/<id> zeigt Artikel"""
        # Hole Export um Artikel-IDs zu finden
        export_response = requests.get(f"{API_BASE}/export/articles")
        articles = export_response.json()['articles']
        
        # Finde einen veröffentlichten Artikel
        published_article = next((a for a in articles if a.get('published')), None)
        
        if published_article:
            article_id = published_article['id']
            response = requests.get(f"{READER_BASE}/article/{article_id}")
            
            assert response.status_code == 200
            assert 'text/html' in response.headers['Content-Type']
            # Titel sollte im HTML vorkommen
            assert published_article['title'] in response.text
        else:
            pytest.skip("Keine veröffentlichten Artikel in der Datenbank")
    
    def test_reader_article_endpoint_nonexistent(self):
        """Test: GET /reader/article/<id> für nicht existierenden Artikel"""
        response = requests.get(f"{READER_BASE}/article/999999", allow_redirects=False)
        
        # API leitet um statt 404 zurückzugeben
        assert response.status_code in [302, 404]


class TestWhatsAppExportEndpoint:
    """Tests für WhatsApp-Export Endpoint"""
    
    def test_whatsapp_export_endpoint_existing_article(self):
        """Test: GET /admin/article/<id>/whatsapp zeigt WhatsApp-Export"""
        # Hole Export um Artikel-IDs zu finden
        export_response = requests.get(f"{API_BASE}/export/articles")
        articles = export_response.json()['articles']
        
        if len(articles) > 0:
            article_id = articles[0]['id']
            response = requests.get(f"{ADMIN_BASE}/article/{article_id}/whatsapp")
            
            assert response.status_code == 200
            assert 'text/html' in response.headers['Content-Type']
            # Sollte WhatsApp-formatierte Vorschau enthalten
            assert 'WhatsApp' in response.text or 'whatsapp' in response.text.lower()
        else:
            pytest.skip("Keine Artikel in der Datenbank")
    
    def test_whatsapp_export_endpoint_nonexistent_article(self):
        """Test: WhatsApp-Export für nicht existierenden Artikel"""
        response = requests.get(f"{ADMIN_BASE}/article/999999/whatsapp", allow_redirects=False)
        
        # API leitet um statt 404 zurückzugeben
        assert response.status_code in [302, 404]


class TestAPIErrorHandling:
    """Tests für Fehlerbehandlung aller API Endpoints"""
    
    def test_export_endpoint_accepts_only_get(self):
        """Test: Export-Endpoint akzeptiert nur GET"""
        response = requests.post(f"{API_BASE}/export/articles")
        assert response.status_code == 405  # Method Not Allowed
    
    def test_import_endpoint_accepts_only_post(self):
        """Test: Import-Endpoint akzeptiert nur POST"""
        response = requests.get(f"{API_BASE}/import/articles")
        assert response.status_code == 405  # Method Not Allowed
    
    def test_upload_endpoint_accepts_only_post(self):
        """Test: Upload-Endpoint akzeptiert nur POST"""
        response = requests.get(f"{API_BASE}/upload/images/1")
        assert response.status_code == 405  # Method Not Allowed


class TestAPIPerformance:
    """Performance-Tests für API Endpoints"""
    
    def test_export_response_time(self):
        """Test: Export-Endpoint antwortet schnell genug"""
        import time
        start = time.time()
        response = requests.get(f"{API_BASE}/export/articles")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 5.0, f"Export dauerte {duration:.2f}s (max 5s)"
    
    def test_reader_index_response_time(self):
        """Test: Reader-Index antwortet schnell"""
        import time
        start = time.time()
        response = requests.get(f"{READER_BASE}/")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 2.0, f"Reader-Index dauerte {duration:.2f}s (max 2s)"


if __name__ == '__main__':
    print("FakeDaily API Endpoint Tests")
    print(f"Server: {BASE_URL}")
    print(f"Prefix: '{APP_PREFIX}'")
    print("-" * 70)
    pytest.main([__file__, '-v', '--tb=short'])
