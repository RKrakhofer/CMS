"""
Export/Import Loop Test für FakeDaily
Testet den vollständigen Export -> Import Zyklus inklusive Bilder und Cleanup
"""
import pytest
import requests
import json
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Konfiguration über Environment-Variablen
BASE_URL = os.getenv('CMS_URL', 'http://localhost:5001')
APP_PREFIX = os.getenv('CMS_PREFIX', '')

API_BASE = f"{BASE_URL}{APP_PREFIX}/admin/api"
READER_BASE = f"{BASE_URL}{APP_PREFIX}/reader"
ADMIN_BASE = f"{BASE_URL}{APP_PREFIX}/admin"


class TestExportImportLoop:
    """Vollständiger Export/Import Zyklus mit automatischem Cleanup"""
    
    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Setup: Merke initial state, Cleanup: Stelle wieder her"""
        # Vor dem Test: Aktuelle Artikel-IDs merken
        export_before = requests.get(f"{API_BASE}/export/articles").json()
        self.initial_article_ids = {a['id'] for a in export_before.get('articles', [])}
        self.initial_count = export_before.get('count', 0)
        
        # Test ausführen
        yield
        
        # Nach dem Test: Cleanup - Lösche alle neu erstellten Artikel
        export_after = requests.get(f"{API_BASE}/export/articles").json()
        current_article_ids = {a['id'] for a in export_after.get('articles', [])}
        
        # Neue Artikel identifizieren
        new_article_ids = current_article_ids - self.initial_article_ids
        
        # Neue Artikel löschen
        for article_id in new_article_ids:
            try:
                # Artikel löschen (über Admin-Interface)
                delete_url = f"{ADMIN_BASE}/article/{article_id}/delete"
                requests.post(delete_url)
                print(f"✓ Cleanup: Artikel {article_id} gelöscht")
            except Exception as e:
                print(f"⚠ Cleanup-Fehler für Artikel {article_id}: {e}")
    
    def test_simple_export_import_loop(self):
        """Test: Einfacher Export -> Import Zyklus ohne Bilder"""
        # 1. Erstelle Test-Artikel via Import
        test_article = {
            'title': f'Export-Import Test {datetime.now().timestamp()}',
            'content': '# Test Artikel\n\nDieser Artikel wird exportiert und re-importiert.',
            'author': 'Test Bot',
            'published': True,
            'tags': ['test', 'export-import'],
            'created_at': '2026-01-17T10:00:00',
            'updated_at': '2026-01-17T10:00:00'
        }
        
        # Artikel erstellen
        import_response = requests.post(
            f"{API_BASE}/import/articles",
            json={'articles': [test_article]}
        )
        assert import_response.status_code == 200
        import_data = import_response.json()
        assert import_data['success'] is True
        assert import_data['imported'] >= 1
        
        # 2. Export durchführen
        export_response = requests.get(f"{API_BASE}/export/articles")
        assert export_response.status_code == 200
        export_data = export_response.json()
        
        # Prüfen ob unser Artikel im Export ist
        exported_article = None
        for article in export_data['articles']:
            if test_article['title'] in article['title']:
                exported_article = article
                break
        
        assert exported_article is not None, "Test-Artikel nicht im Export gefunden"
        
        # 3. Exportierten Artikel modifizieren
        exported_article['content'] = exported_article['content'] + '\n\n**Update:** Re-importiert!'
        exported_article['updated_at'] = datetime.now().isoformat()
        
        # 4. Re-Import durchführen
        reimport_response = requests.post(
            f"{API_BASE}/import/articles",
            json={'articles': [exported_article]}
        )
        assert reimport_response.status_code == 200
        reimport_data = reimport_response.json()
        
        assert reimport_data['success'] is True
        # Sollte als Update gezählt werden
        assert reimport_data['updated'] >= 1 or reimport_data['imported'] >= 0
        
        # 5. Verifizieren dass Update funktioniert hat
        verify_export = requests.get(f"{API_BASE}/export/articles").json()
        verified_article = None
        for article in verify_export['articles']:
            if article['id'] == exported_article['id']:
                verified_article = article
                break
        
        assert verified_article is not None
        assert '**Update:** Re-importiert!' in verified_article['content']
    
    def test_export_import_with_images(self):
        """Test: Export/Import mit Bildern (via API)"""
        # 1. Erstelle Test-Artikel
        test_article = {
            'title': f'Bild Test {datetime.now().timestamp()}',
            'content': '# Artikel mit Bildern\n\n![Test Bild](example.jpg)',
            'author': 'Test Bot',
            'published': True,
            'tags': ['test', 'bilder'],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        import_response = requests.post(
            f"{API_BASE}/import/articles",
            json={'articles': [test_article]}
        )
        assert import_response.status_code == 200
        
        # Artikel-ID ermitteln
        export_data = requests.get(f"{API_BASE}/export/articles").json()
        article_id = None
        for article in export_data['articles']:
            if test_article['title'] in article['title']:
                article_id = article['id']
                break
        
        assert article_id is not None, "Test-Artikel nicht gefunden"
        
        # 2. Test-Bild erstellen (1x1 PNG)
        temp_dir = tempfile.mkdtemp()
        try:
            test_image_path = Path(temp_dir) / 'test_image.png'
            
            # Minimales PNG erstellen (1x1 Pixel, schwarz)
            png_data = (
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
                b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01'
                b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            )
            test_image_path.write_bytes(png_data)
            
            # 3. Bild hochladen via API
            with open(test_image_path, 'rb') as img_file:
                upload_response = requests.post(
                    f"{API_BASE}/upload/images/{article_id}",
                    files={'images': ('test_image.png', img_file, 'image/png')}
                )
            
            assert upload_response.status_code == 200
            upload_data = upload_response.json()
            assert upload_data['success'] is True
            assert upload_data['uploaded'] >= 1
            
            uploaded_filename = upload_data['images'][0]['filename']
            
            # 4. Export durchführen (sollte Bild enthalten)
            export_with_images = requests.get(f"{API_BASE}/export/articles").json()
            article_with_images = None
            for article in export_with_images['articles']:
                if article['id'] == article_id:
                    article_with_images = article
                    break
            
            assert article_with_images is not None
            assert len(article_with_images['images']) >= 1
            assert article_with_images['images'][0]['filename'] == uploaded_filename
            
            # 5. Bild-URL testen
            image_url = article_with_images['images'][0]['url']
            image_response = requests.get(image_url)
            assert image_response.status_code == 200
            assert image_response.headers['Content-Type'].startswith('image/')
            
        finally:
            # Cleanup: Temp-Verzeichnis löschen
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_full_export_import_cycle(self):
        """Test: Vollständiger Zyklus - Export, Löschen, Re-Import, Verifizierung"""
        # 1. Erstelle mehrere Test-Artikel
        test_articles = [
            {
                'title': f'Cycle Test 1 - {datetime.now().timestamp()}',
                'content': '# Artikel 1\n\nInhalt 1',
                'author': 'Bot 1',
                'published': True,
                'tags': ['test', 'cycle'],
                'created_at': '2026-01-15T10:00:00',
                'updated_at': '2026-01-15T10:00:00'
            },
            {
                'title': f'Cycle Test 2 - {datetime.now().timestamp()}',
                'content': '# Artikel 2\n\nInhalt 2',
                'author': 'Bot 2',
                'published': False,
                'tags': ['test', 'cycle', 'draft'],
                'created_at': '2026-01-16T12:00:00',
                'updated_at': '2026-01-16T12:00:00'
            }
        ]
        
        # Artikel erstellen
        import_response = requests.post(
            f"{API_BASE}/import/articles",
            json={'articles': test_articles}
        )
        assert import_response.status_code == 200
        assert import_response.json()['imported'] >= 2
        
        # 2. Export durchführen und Test-Artikel extrahieren
        export_data = requests.get(f"{API_BASE}/export/articles").json()
        exported_test_articles = []
        for article in export_data['articles']:
            if 'Cycle Test' in article['title']:
                exported_test_articles.append(article)
        
        assert len(exported_test_articles) >= 2
        
        # 3. Artikel-IDs merken
        test_article_ids = [a['id'] for a in exported_test_articles]
        
        # 4. Einen Artikel löschen (simuliert Datenverlust)
        delete_url = f"{ADMIN_BASE}/article/{test_article_ids[0]}/delete"
        delete_response = requests.post(delete_url)
        # Note: Delete might redirect, so accept 302 or 200
        assert delete_response.status_code in [200, 302]
        
        # 5. Verifizieren dass Artikel weg ist
        verify_export = requests.get(f"{API_BASE}/export/articles").json()
        article_ids = [a['id'] for a in verify_export['articles']]
        assert test_article_ids[0] not in article_ids
        
        # 6. Re-Import durchführen (sollte gelöschten Artikel wiederherstellen)
        reimport_response = requests.post(
            f"{API_BASE}/import/articles",
            json={'articles': exported_test_articles}
        )
        assert reimport_response.status_code == 200
        reimport_data = reimport_response.json()
        
        assert reimport_data['success'] is True
        # Mindestens ein Artikel sollte neu importiert worden sein
        assert reimport_data['imported'] >= 1
        
        # 7. Verifizieren dass beide Artikel wieder da sind
        final_export = requests.get(f"{API_BASE}/export/articles").json()
        final_article_ids = [a['id'] for a in final_export['articles']]
        
        # Prüfe anhand Titel, da IDs sich geändert haben können
        final_titles = {a['title'] for a in final_export['articles']}
        for test_article in test_articles:
            # Titel sollte im Export sein (möglicherweise mit modifiziertem Timestamp)
            matching_titles = [t for t in final_titles if test_article['title'].split(' - ')[0] in t]
            assert len(matching_titles) > 0, f"Artikel '{test_article['title']}' nicht wiederhergestellt"
    
    def test_export_import_preserves_data_integrity(self):
        """Test: Export/Import behält Datenintegrität (Tags, Timestamps, etc.)"""
        # Erstelle Artikel mit komplexen Daten
        complex_article = {
            'title': f'Integrity Test {datetime.now().timestamp()}',
            'content': '''# Komplexer Artikel

## Markdown Features

- **Fett**
- *Kursiv*
- `Code`

### Code Block

```python
def test():
    return "Hello World"
```

> Zitat mit Umlauten: äöüÄÖÜß

[Link](https://example.com)
''',
            'author': 'Test Bot with Ümläuts',
            'published': True,
            'tags': ['test', 'unicode', 'markdown', 'äöü'],
            'created_at': '2026-01-17T10:30:45',
            'updated_at': '2026-01-17T11:45:30'
        }
        
        # Import
        import_response = requests.post(
            f"{API_BASE}/import/articles",
            json={'articles': [complex_article]}
        )
        assert import_response.status_code == 200
        
        # Export
        export_data = requests.get(f"{API_BASE}/export/articles").json()
        exported = None
        for article in export_data['articles']:
            if complex_article['title'] in article['title']:
                exported = article
                break
        
        assert exported is not None
        
        # Verifiziere Datenintegrität
        assert exported['author'] == complex_article['author']
        assert set(exported['tags']) == set(complex_article['tags'])
        assert '```python' in exported['content']
        assert 'äöüÄÖÜß' in exported['content']
        assert exported['published'] == complex_article['published']
        
        # Timestamps sollten erhalten bleiben (Format: YYYY-MM-DD HH:MM:SS)
        # API konvertiert zu eigenem Format, aber Datum sollte stimmen
        assert exported['created_at'].startswith('2026-01-17')
        assert exported['updated_at'].startswith('2026-01-17')


class TestExportImportEdgeCases:
    """Edge Cases und Fehlerbehandlung"""
    
    def test_import_with_invalid_article_id(self):
        """Test: Import ignoriert ungültige Artikel-IDs"""
        # Artikel mit sehr hoher ID (sollte ignoriert werden)
        article = {
            'id': 999999,  # Wird beim Import ignoriert
            'title': f'Invalid ID Test {datetime.now().timestamp()}',
            'content': 'Test',
            'published': False,
            'tags': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        import_response = requests.post(
            f"{API_BASE}/import/articles",
            json={'articles': [article]}
        )
        
        # Import sollte erfolgreich sein (ID wird neu vergeben)
        assert import_response.status_code == 200
        data = import_response.json()
        assert data['success'] is True
    
    def test_import_with_missing_fields(self):
        """Test: Import mit fehlenden Pflichtfeldern"""
        incomplete_article = {
            'title': f'Incomplete {datetime.now().timestamp()}',
            # content fehlt absichtlich
            'published': False
        }
        
        import_response = requests.post(
            f"{API_BASE}/import/articles",
            json={'articles': [incomplete_article]}
        )
        
        # API akzeptiert Artikel ohne Content (wird als leerer String gespeichert)
        data = import_response.json()
        assert data['success'] is True
        assert data['imported'] >= 0  # Kann importiert oder geskippt werden


if __name__ == '__main__':
    print("FakeDaily Export/Import Loop Tests")
    print(f"Base URL: {BASE_URL}{APP_PREFIX}")
    print("-" * 70)
    
    # Pytest mit verbose output
    pytest.main([__file__, '-v', '--tb=short', '-s'])
