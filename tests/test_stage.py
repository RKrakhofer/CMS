"""
API Tests für CMS Stage-Server
Verwendet http://stage:5001/cms
"""
import pytest
import requests

# Stage-Konfiguration
BASE_URL = "http://stage:5001"
APP_PREFIX = "/cms"

API_BASE = f"{BASE_URL}{APP_PREFIX}/admin/api"
READER_BASE = f"{BASE_URL}{APP_PREFIX}/reader"


class TestStageAPI:
    """Tests für Stage-Server"""
    
    def test_stage_reachable(self):
        """Test: Stage-Server ist erreichbar"""
        response = requests.get(f"{READER_BASE}/")
        assert response.status_code == 200
    
    def test_stage_export_api(self):
        """Test: Export-API funktioniert auf Stage"""
        response = requests.get(f"{API_BASE}/export/articles")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        print(f"\n✓ Stage hat {data['count']} Artikel")
    
    def test_stage_reader_index(self):
        """Test: Reader-Startseite auf Stage"""
        response = requests.get(f"{READER_BASE}/")
        assert response.status_code == 200
        assert 'Aktuelle Artikel' in response.text or 'CMS' in response.text or 'Artikel' in response.text
    
    def test_stage_tag_filter(self):
        """Test: Tag-Filterung auf Stage"""
        # Häufige Tags testen
        common_tags = ['Politik', 'Satire', 'Medien', 'International']
        
        for tag in common_tags:
            response = requests.get(f"{READER_BASE}/tag/{tag}")
            if response.status_code == 200:
                print(f"\n✓ Tag '{tag}' gefunden")
                assert f'Tag: {tag}' in response.text
                break
    
    def test_stage_static_files(self):
        """Test: Static-Files (CSS) laden mit Prefix"""
        response = requests.get(f"{BASE_URL}{APP_PREFIX}/static/css/reader.css")
        assert response.status_code == 200
        assert 'article-card' in response.text or '.tag' in response.text


if __name__ == '__main__':
    print("CMS Stage Tests")
    print(f"Stage URL: {BASE_URL}{APP_PREFIX}")
    print("-" * 50)
    
    pytest.main([__file__, '-v', '--tb=short'])
