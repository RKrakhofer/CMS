#!/usr/bin/env python3
"""
Tests für die Similarity Detection im Import-Workflow.

Testet die SequenceMatcher-basierte Duplikaterkennung:
- Title similarity (95% threshold)
- Content similarity (90% threshold)
- Integration mit Import API
"""

import pytest
import sys
from pathlib import Path

# Import from web app
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))
from app import similarity, are_similar_articles


class TestSimilarityDetection:
    """Tests für die Similarity Detection Funktionen"""
    
    def test_similarity_identical_strings(self):
        """Test: Identische Strings haben 100% Ähnlichkeit"""
        result = similarity("Test String", "Test String")
        assert result == 1.0
    
    def test_similarity_case_insensitive(self):
        """Test: Similarity ist case-insensitive"""
        result = similarity("Test String", "test string")
        assert result == 1.0
    
    def test_similarity_completely_different(self):
        """Test: Komplett unterschiedliche Strings haben niedrige Ähnlichkeit"""
        result = similarity("Hello World", "XYZ ABC DEF")
        assert result < 0.3
    
    def test_similarity_small_differences(self):
        """Test: Kleine Unterschiede ergeben hohe Ähnlichkeit"""
        # "Fake Daily" vs "Fake Daily 🎭" (mit Emoji)
        result = similarity("Fake Daily – Die Wahrheit hinter den Nachrichten", 
                           "Fake Daily 🎭 – Die Wahrheit hinter den Nachrichten")
        assert result > 0.95  # Sollte sehr ähnlich sein
    
    def test_similarity_threshold_examples(self):
        """Test: Beispiele aus docs/Aehnlichkeitserkennung.md"""
        # Exaktes Duplikat: 100%
        title1 = "Fake Daily – Die Wahrheit hinter den Nachrichten"
        title2 = "Fake Daily – Die Wahrheit hinter den Nachrichten"
        assert similarity(title1, title2) == 1.0
        
        # Mit Emoji: 98%
        title3 = "Fake Daily 🎭 – Die Wahrheit hinter den Nachrichten"
        sim = similarity(title1, title3)
        assert sim > 0.95
        assert sim < 1.0
        
        # Komplett anders: ~30%
        title4 = "KI-Revolution: ChatGPT übernimmt die Weltherrschaft"
        assert similarity(title1, title4) < 0.35  # Adjusted threshold
    
    def test_are_similar_articles_exact_title_match(self):
        """Test: Exakter Title-Match wird als Duplikat erkannt"""
        article1 = {
            'title': 'Identischer Titel',
            'content': 'Inhalt A'
        }
        article2 = {
            'title': 'Identischer Titel',
            'content': 'Komplett anderer Inhalt B'
        }
        assert are_similar_articles(article1, article2) is True
    
    def test_are_similar_articles_similar_title(self):
        """Test: Ähnliche Titel (>95%) werden als Duplikat erkannt"""
        article1 = {
            'title': 'Fake Daily – Die Wahrheit',
            'content': 'Inhalt A'
        }
        article2 = {
            'title': 'Fake Daily 🎭 – Die Wahrheit',
            'content': 'Inhalt B'
        }
        assert are_similar_articles(article1, article2) is True
    
    def test_are_similar_articles_different_titles_similar_content(self):
        """Test: Unterschiedliche Titel aber ähnlicher Content (>90%) = Duplikat"""
        content = "Dies ist ein sehr langer Artikel über Satire. " * 20  # >500 chars
        
        article1 = {
            'title': 'Titel Version 1',
            'content': content
        }
        article2 = {
            'title': 'Titel Version 2',
            'content': content + ' Minimale Änderung am Ende.'
        }
        assert are_similar_articles(article1, article2) is True
    
    def test_are_similar_articles_completely_different(self):
        """Test: Komplett unterschiedliche Artikel werden nicht als Duplikat erkannt"""
        article1 = {
            'title': 'Artikel über Politik',
            'content': 'Dies ist ein Artikel über politische Themen. ' * 20
        }
        article2 = {
            'title': 'Artikel über Technologie',
            'content': 'Dies ist ein Artikel über technische Innovationen. ' * 20
        }
        assert are_similar_articles(article1, article2) is False
    
    def test_are_similar_articles_below_threshold(self):
        """Test: Ähnlichkeit unter Threshold wird nicht als Duplikat erkannt"""
        article1 = {
            'title': 'Österreich wählt neuen Bundeskanzler',
            'content': 'Wahlkampf in Österreich...'
        }
        article2 = {
            'title': 'Deutschland wählt neuen Bundeskanzler',
            'content': 'Wahlkampf in Deutschland...'
        }
        # Titel sind ähnlich, aber unter 95%
        title_sim = similarity(article1['title'], article2['title'])
        assert title_sim < 0.95
        assert are_similar_articles(article1, article2) is False
    
    def test_are_similar_articles_custom_thresholds(self):
        """Test: Custom Thresholds können angepasst werden"""
        article1 = {
            'title': 'Ähnlicher Titel ABC',
            'content': 'Komplett unterschiedlicher Inhalt über Politik in Österreich und die neuesten Entwicklungen.'
        }
        article2 = {
            'title': 'Ähnlicher Titel XYZ',
            'content': 'Ganz andere Geschichte über Technologie-Trends und Innovation in der Industrie.'
        }
        
        # Mit Standard-Threshold (95%) kein Duplikat
        assert are_similar_articles(article1, article2, title_threshold=0.95) is False
        
        # Mit niedrigerem Threshold (70%) wird es als Duplikat erkannt
        assert are_similar_articles(article1, article2, title_threshold=0.70) is True
    
    def test_similarity_performance(self):
        """Test: Similarity Detection ist performant genug"""
        import time
        
        # Generiere längeren Text mit unterschiedlichem Inhalt
        long_text1 = "Dies ist ein sehr langer Artikel über Politik und Wirtschaft. " * 100
        long_text2 = "Eine komplett andere Geschichte über Technologie und Innovation. " * 100
        
        article1 = {
            'title': 'Performance Test Artikel ABC',
            'content': long_text1
        }
        article2 = {
            'title': 'Komplett anderer Titel XYZ',
            'content': long_text2
        }
        
        start = time.time()
        result = are_similar_articles(article1, article2)
        duration = time.time() - start
        
        # Sollte unter 10ms sein (sehr großzügig)
        assert duration < 0.01
        assert result is False  # Titel und Content komplett unterschiedlich
    
    def test_similarity_edge_cases(self):
        """Test: Edge Cases - leere Strings, None, etc."""
        # Leere Strings
        assert similarity("", "") == 1.0
        
        # Ein leerer String
        assert similarity("Test", "") < 0.1
        
        # Sehr kurze Strings
        assert similarity("A", "B") == 0.0
        assert similarity("A", "A") == 1.0
    
    def test_are_similar_articles_missing_fields(self):
        """Test: Fehlende Felder werden sicher behandelt"""
        article1 = {'title': 'Test', 'content': 'Content'}
        article2 = {}  # Keine Felder
        
        # Sollte nicht crashen
        result = are_similar_articles(article1, article2)
        assert result is False


class TestImportDuplicateScenarios:
    """Test-Szenarien für Import mit Similarity Detection"""
    
    def test_import_scenario_exact_duplicate(self):
        """Szenario: Exaktes Duplikat wird übersprungen"""
        new_article = {
            'title': 'Fake Daily – Breaking News',
            'content': 'Dies ist der Artikel-Inhalt.',
            'tags': ['satire'],
            'publish_date': '2026-01-21'
        }
        
        existing_article = {
            'title': 'Fake Daily – Breaking News',
            'content': 'Dies ist der Artikel-Inhalt.',
            'created_at': '2026-01-20T10:00:00'
        }
        
        # Sollte als Duplikat erkannt werden
        assert are_similar_articles(new_article, existing_article) is True
    
    def test_import_scenario_title_with_emoji(self):
        """Szenario: Titel mit/ohne Emoji wird als Duplikat erkannt"""
        new_article = {
            'title': 'Fake Daily 🎭 – Satire News',
            'content': 'Satire-Artikel über aktuelle Ereignisse.'
        }
        
        existing_article = {
            'title': 'Fake Daily – Satire News',
            'content': 'Satire-Artikel über aktuelle Ereignisse.'
        }
        
        # Sollte als Duplikat erkannt werden (>95% title similarity)
        assert are_similar_articles(new_article, existing_article) is True
    
    def test_import_scenario_updated_version(self):
        """Szenario: Aktualisierte Version desselben Artikels"""
        new_article = {
            'title': 'Artikel über Politik',
            'content': 'Version 2 des Artikels mit erweiterten Informationen...' * 10
        }
        
        existing_article = {
            'title': 'Artikel über Politik',
            'content': 'Version 1 des Artikels...' * 5
        }
        
        # Sollte als ähnlich erkannt werden (gleicher Titel)
        assert are_similar_articles(new_article, existing_article) is True
    
    def test_import_scenario_similar_but_different(self):
        """Szenario: Ähnliche aber unterschiedliche Artikel"""
        new_article = {
            'title': 'Bundeskanzler kündigt Reformen an',
            'content': 'Der Bundeskanzler hat heute weitreichende Reformen angekündigt...'
        }
        
        existing_article = {
            'title': 'Bundespräsident kündigt Reformen an',
            'content': 'Der Bundespräsident hat gestern Reformen angekündigt...'
        }
        
        # Sollte NICHT als Duplikat erkannt werden
        title_sim = similarity(new_article['title'], existing_article['title'])
        assert title_sim < 0.95
        assert are_similar_articles(new_article, existing_article) is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
