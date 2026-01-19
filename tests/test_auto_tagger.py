"""
Unit Tests for Auto-Tagging Module
Tests tag generation and automatic tagging logic
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path to import from src/
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auto_tagger import generate_tags, add_auto_tags_if_empty, TAG_RULES


class TestGenerateTags:
    """Tests for generate_tags() function"""
    
    def test_generate_tags_with_single_category_returns_one_tag(self):
        """Test: Article matching one category returns single tag"""
        title = "Österreich plant neue Gesetze"
        content = "Die österreichische Regierung kündigte an..."
        
        tags = generate_tags(title, content)
        
        assert 'Politik Österreich' in tags
        assert len(tags) >= 1
    
    def test_generate_tags_with_multiple_categories_returns_multiple_tags(self):
        """Test: Article matching multiple categories returns multiple tags"""
        title = "Kickl plant massive Energiewende in Österreich"
        content = "FPÖ-Chef Herbert Kickl kündigte an, dass Österreich massiv in Solarenergie investieren wird."
        
        tags = generate_tags(title, content)
        
        assert 'Politik Österreich' in tags
        assert 'Energie' in tags
        assert len(tags) >= 2
    
    def test_generate_tags_with_usa_politics_returns_usa_tag(self):
        """Test: Article about USA politics returns Politik USA tag"""
        title = "Trump kündigt neue Initiative an"
        content = "US-Präsident Trump präsentiert neues Programm im Weißen Haus."
        
        tags = generate_tags(title, content)
        
        assert 'Politik USA' in tags
    
    def test_generate_tags_with_technology_keywords_returns_tech_tag(self):
        """Test: Article with technology keywords returns Technologie tag"""
        title = "Neue KI-Software revolutioniert Entwicklung"
        content = "Künstliche Intelligenz und ChatGPT verändern die Software-Entwicklung."
        
        tags = generate_tags(title, content)
        
        assert 'Technologie' in tags
    
    def test_generate_tags_with_economics_returns_wirtschaft_tag(self):
        """Test: Article about economics returns Wirtschaft tag"""
        title = "Benko-Firma meldet Insolvenz an"
        content = "Das Unternehmen ist pleite und hat Insolvenz angemeldet."
        
        tags = generate_tags(title, content)
        
        assert 'Wirtschaft' in tags
    
    def test_generate_tags_with_science_returns_wissenschaft_tag(self):
        """Test: Article about science returns Wissenschaft tag"""
        title = "Neue Studie zur Erderwärmung"
        content = "Wissenschaftler warnen vor beschleunigter Klimaveränderung."
        
        tags = generate_tags(title, content)
        
        assert 'Wissenschaft' in tags
    
    def test_generate_tags_with_health_returns_gesundheit_tag(self):
        """Test: Article about health returns Gesundheit tag"""
        title = "Krankenhaus in Berlin überlastet"
        content = "Das Gesundheitssystem steht vor Herausforderungen, Ärzte und Pfleger sind überlastet."
        
        tags = generate_tags(title, content)
        
        assert 'Gesundheit' in tags
    
    def test_generate_tags_with_food_returns_lebensmittel_tag(self):
        """Test: Article about food returns Lebensmittel tag"""
        title = "Schnitzel aus dem Labor bald in Restaurants"
        content = "Gastronomen testen vegetarisches Laborfleisch für ihre Speisekarten."
        
        tags = generate_tags(title, content)
        
        assert 'Lebensmittel' in tags
    
    def test_generate_tags_with_satire_keywords_returns_satire_tag(self):
        """Test: Article with satire keywords returns Satire tag"""
        title = "Chefredakteur Kaiser in eigener Sache"
        content = "Der Fake Daily Chefredakteur meldet sich zu Wort."
        
        tags = generate_tags(title, content)
        
        assert 'Satire' in tags
    
    def test_generate_tags_case_insensitive_matches_keywords(self):
        """Test: Tag matching is case-insensitive"""
        title = "ÖSTERREICH PLANT NEUE GESETZE"
        content = "DIE ÖSTERREICHISCHE REGIERUNG..."
        
        tags = generate_tags(title, content)
        
        assert 'Politik Österreich' in tags
    
    def test_generate_tags_with_no_matches_returns_empty_list(self):
        """Test: Article with no keyword matches returns empty list"""
        title = "Lorem Ipsum Dolor"
        content = "Sit amet consectetur adipiscing elit."
        
        tags = generate_tags(title, content)
        
        assert tags == []
    
    def test_generate_tags_with_empty_strings_returns_empty_list(self):
        """Test: Empty title and content returns empty list"""
        tags = generate_tags("", "")
        
        assert tags == []
    
    def test_generate_tags_returns_sorted_list(self):
        """Test: Generated tags are sorted alphabetically"""
        title = "Trump plant Energiewende mit deutscher Unterstützung"
        content = "USA und Deutschland arbeiten zusammen an Solar-Projekten."
        
        tags = generate_tags(title, content)
        
        # Should contain multiple tags
        assert len(tags) > 1
        # Should be sorted
        assert tags == sorted(tags)
    
    def test_generate_tags_no_duplicate_tags(self):
        """Test: Same tag category only appears once even with multiple matches"""
        title = "Österreich und Wien planen neue FPÖ-Koalition"
        content = "Herbert Kickl und die österreichische Regierung in Wien..."
        
        tags = generate_tags(title, content)
        
        # Count occurrences of Politik Österreich
        count = tags.count('Politik Österreich')
        assert count == 1


class TestAddAutoTagsIfEmpty:
    """Tests for add_auto_tags_if_empty() function"""
    
    def test_add_auto_tags_with_empty_list_generates_tags(self):
        """Test: Empty tag list triggers auto-generation"""
        title = "Kickl plant Energiewende"
        content = "FPÖ-Chef in Österreich..."
        
        result = add_auto_tags_if_empty([], title, content)
        
        assert len(result) > 0
        assert 'Politik Österreich' in result
    
    def test_add_auto_tags_with_existing_tags_keeps_them(self):
        """Test: Existing tags are not replaced"""
        existing = ['Satire', 'Humor']
        title = "Kickl plant Energiewende"
        content = "FPÖ-Chef in Österreich..."
        
        result = add_auto_tags_if_empty(existing, title, content)
        
        assert result == existing
    
    def test_add_auto_tags_with_none_generates_tags(self):
        """Test: None is treated as empty and triggers generation"""
        # In real app, tags might be None from form input
        title = "Trump in USA"
        content = "US-Präsident..."
        
        # Convert None to empty list (as app.py does)
        tags = None or []
        result = add_auto_tags_if_empty(tags, title, content)
        
        assert len(result) > 0
        assert 'Politik USA' in result
    
    def test_add_auto_tags_with_single_tag_keeps_it(self):
        """Test: Single existing tag is preserved"""
        existing = ['Custom Tag']
        title = "Some Article"
        content = "Content..."
        
        result = add_auto_tags_if_empty(existing, title, content)
        
        assert result == existing
    
    def test_add_auto_tags_with_whitespace_only_tags_generates_new(self):
        """Test: Tags with only whitespace are treated as empty"""
        # This might happen with form input "  ,  , "
        whitespace_tags = []  # After strip() in app.py
        title = "Technologie News"
        content = "ChatGPT und künstliche Intelligenz..."
        
        result = add_auto_tags_if_empty(whitespace_tags, title, content)
        
        assert len(result) > 0
        assert 'Technologie' in result


class TestTagRulesConfiguration:
    """Tests for TAG_RULES configuration"""
    
    def test_tag_rules_has_expected_categories(self):
        """Test: TAG_RULES contains all expected categories"""
        expected_categories = [
            'Politik Österreich',
            'Politik Deutschland',
            'Politik USA',
            'Politik EU',
            'Satire',
            'Technologie',
            'Wirtschaft',
            'Wissenschaft',
            'Energie',
            'Medien',
            'Gesellschaft',
            'Gesundheit',
            'Justiz',
            'Militär',
            'Lebensmittel'
        ]
        
        for category in expected_categories:
            assert category in TAG_RULES
    
    def test_tag_rules_all_categories_have_keywords(self):
        """Test: All categories have at least one keyword"""
        for category, keywords in TAG_RULES.items():
            assert len(keywords) > 0
            assert isinstance(keywords, list)
    
    def test_tag_rules_keywords_are_lowercase(self):
        """Test: All keywords are lowercase for case-insensitive matching"""
        for category, keywords in TAG_RULES.items():
            for keyword in keywords:
                assert keyword == keyword.lower(), f"Keyword '{keyword}' in '{category}' is not lowercase"


class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_generate_tags_with_special_characters_works(self):
        """Test: Special characters in content don't break tagging"""
        title = "Österreich & Deutschland @ EU-Gipfel!"
        content = "Politik-News: FPÖ/ÖVP-Koalition §123..."
        
        tags = generate_tags(title, content)
        
        assert 'Politik Österreich' in tags
    
    def test_generate_tags_with_very_long_content_works(self):
        """Test: Very long content is processed correctly"""
        title = "Energiewende"
        content = "Solar " * 1000 + " in Österreich"
        
        tags = generate_tags(title, content)
        
        assert 'Energie' in tags
        assert 'Politik Österreich' in tags
    
    def test_generate_tags_with_unicode_characters_works(self):
        """Test: Unicode characters are handled correctly"""
        title = "Österreich 🇦🇹 plant neue Gesetze"
        content = "Die österreichische Regierung 🏛️..."
        
        tags = generate_tags(title, content)
        
        assert 'Politik Österreich' in tags
    
    def test_add_auto_tags_preserves_tag_order_when_keeping_existing(self):
        """Test: Existing tag order is preserved"""
        existing = ['Zebra', 'Alpha', 'Beta']
        title = "Something"
        content = "Content"
        
        result = add_auto_tags_if_empty(existing, title, content)
        
        assert result == existing
        # Not sorted, original order preserved
        assert result != sorted(result)
