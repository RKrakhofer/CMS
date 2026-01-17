"""
Unit Tests for WhatsAppFormatter
Tests Markdown to WhatsApp conversion
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.whatsapp_formatter import WhatsAppFormatter


class TestWhatsAppFormatter:
    """Unit tests for WhatsAppFormatter class"""
    
    @pytest.fixture
    def formatter(self):
        """Create formatter instance"""
        return WhatsAppFormatter()
    
    # ===== convert() Method Tests =====
    
    def test_convert_bold(self, formatter):
        """Test: Bold Markdown conversion - **bold** → *bold* for WhatsApp"""
        assert formatter.convert("**bold text**") == "*bold text*"
        assert formatter.convert("__bold text__") == "*bold text*"
    
    def test_convert_italic(self, formatter):
        """Test: Italic Markdown conversion - *italic* → _italic_ for WhatsApp"""
        result = formatter.convert("*italic*")
        assert "_italic_" in result
    
    def test_convert_headers(self, formatter):
        """Test: Header conversion - # Header → *Header* (headers become bold)"""
        result = formatter.convert("# Header 1")
        assert result.strip() == "*Header 1*"
    
    def test_convert_links(self, formatter):
        """Test: Link Markdown conversion"""
        result = formatter.convert("[Link Text](https://example.com)")
        assert "Link Text" in result
        assert "https://example.com" in result
    
    def test_convert_links_preserves_url(self, formatter):
        """Test: Links preserve URL for WhatsApp auto-linking"""
        result = formatter.convert("[Click here](https://example.com)")
        # Should contain both text and URL (WhatsApp needs URL visible)
        assert "https://example.com" in result
    
    def test_convert_code_blocks(self, formatter):
        """Test: Code block conversion"""
        code = "```python\nprint('hello')\n```"
        result = formatter.convert(code)
        assert "```" in result  # WhatsApp supports monospace with ```
        assert "print('hello')" in result
    
    def test_convert_inline_code(self, formatter):
        """Test: Inline code conversion"""
        result = formatter.convert("Use `print()` function")
        assert "```print()```" in result or "`print()`" in result
    
    def test_convert_lists(self, formatter):
        """Test: List conversion"""
        markdown = "- Item 1\n- Item 2\n- Item 3"
        result = formatter.convert(markdown)
        assert "Item 1" in result
        assert "Item 2" in result
        assert "Item 3" in result
    
    def test_convert_ordered_lists(self, formatter):
        """Test: Ordered list conversion"""
        markdown = "1. First\n2. Second\n3. Third"
        result = formatter.convert(markdown)
        assert "First" in result
        assert "Second" in result
        assert "Third" in result
    
    def test_convert_strikethrough(self, formatter):
        """Test: Strikethrough conversion"""
        result = formatter.convert("~~strikethrough~~")
        assert "~strikethrough~" in result
    
    def test_convert_mixed_formatting(self, formatter):
        """Test: Multiple formatting in one text"""
        markdown = "This is **bold** and *italic* text"
        result = formatter.convert(markdown)
        assert "*bold*" in result  # **bold** → *bold*
        assert "_italic_" in result  # *italic* → _italic_
    
    def test_convert_nested_formatting(self, formatter):
        """Test: Nested formatting (bold + italic)"""
        markdown = "***bold and italic***"
        result = formatter.convert(markdown)
        # Should handle nested formatting
        assert result is not None
        assert len(result) > 0
    
    def test_convert_empty_string(self, formatter):
        """Test: Empty string conversion"""
        assert formatter.convert("") == ""
    
    def test_convert_plain_text(self, formatter):
        """Test: Plain text without formatting"""
        text = "Just plain text without any formatting"
        assert formatter.convert(text) == text
    
    def test_convert_unicode(self, formatter):
        """Test: Unicode characters preservation"""
        text = "Hallo 👋 Welt 🌍 Test äöü ß"
        result = formatter.convert(text)
        assert "👋" in result
        assert "🌍" in result
        assert "äöü" in result
        assert "ß" in result
    
    def test_convert_special_characters(self, formatter):
        """Test: Special characters handling"""
        text = "Special chars: & < > \" ' @#$%"
        result = formatter.convert(text)
        # Should preserve special characters
        assert "&" in result or "&amp;" in result
        assert "@" in result
    
    def test_convert_multiple_paragraphs(self, formatter):
        """Test: Multiple paragraphs with blank lines"""
        markdown = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        result = formatter.convert(markdown)
        assert "Paragraph 1" in result
        assert "Paragraph 2" in result
        assert "Paragraph 3" in result
    
    # ===== format_article() Method Tests =====
    
    def test_format_article_basic(self, formatter):
        """Test: format_article with basic article structure"""
        result = formatter.format_article(
            title='Test Article',
            content='This is the **content**',
            author='Test Author'
        )
        
        assert 'TEST ARTICLE' in result  # Title is uppercased
        assert '*content*' in result  # Bold converted correctly
        assert 'Test Author' in result
    
    def test_format_article_with_tags(self, formatter):
        """Test: format_article doesn't handle tags (they're not in signature)"""
        # format_article only takes title, content, author
        # Tags would need to be added to content manually
        result = formatter.format_article(
            title='Article',
            content='Content with #python #testing tags',
            author='Author'
        )
        
        assert 'ARTICLE' in result
        assert 'Content' in result
    
    def test_format_article_without_author(self, formatter):
        """Test: format_article with no author"""
        result = formatter.format_article(
            title='Article',
            content='Content'
        )
        
        assert 'ARTICLE' in result
        assert 'Content' in result
        # Should not crash or show "None"
        assert result is not None
    
    def test_format_article_without_tags(self, formatter):
        """Test: format_article with empty tags (not in signature anyway)"""
        result = formatter.format_article(
            title='Article',
            content='Content',
            author='Author'
        )
        
        assert 'ARTICLE' in result
        assert 'Content' in result
        # Should not crash
        assert result is not None
    
    def test_format_article_markdown_conversion(self, formatter):
        """Test: format_article converts Markdown in content"""
        result = formatter.format_article(
            title='Test',
            content='# Heading\n\n**Bold text** and *italic text*\n\n- List item',
            author='Author'
        )
        
        # Should convert Markdown correctly
        assert '*Heading*' in result  # Header converted to bold
        assert '*Bold text*' in result  # Bold converted correctly
        assert '_italic text_' in result  # Italic converted
        assert 'List item' in result
    
    def test_format_article_structure(self, formatter):
        """Test: format_article has proper structure"""
        result = formatter.format_article(
            title='Title',
            content='Content',
            author='Author'
        )
        
        # Should have clear separators or structure
        assert len(result) > 0
        # Title should appear before content
        title_pos = result.find('TITLE')  # Title is uppercased
        content_pos = result.find('Content')
        assert title_pos < content_pos
    
    def test_format_article_long_content(self, formatter):
        """Test: format_article handles long content"""
        long_content = "Lorem ipsum dolor sit amet. " * 100  # ~2800 chars
        
        result = formatter.format_article(
            title='Long Article',
            content=long_content,
            author='Author'
        )
        
        assert 'LONG ARTICLE' in result
        assert 'Lorem ipsum' in result
        # Should not truncate
        assert len(result) > 1000
    
    def test_format_article_unicode_title(self, formatter):
        """Test: format_article with Unicode in title"""
        result = formatter.format_article(
            title='Überschrift mit äöü und 中文',
            content='Content',
            author='Author'
        )
        
        # Title gets uppercased
        assert 'ÜBERSCHRIFT' in result or 'Überschrift' in result
        assert 'äöü' in result or 'ÄÖÜ' in result
        assert '中文' in result
    
    def test_format_article_preserves_line_breaks(self, formatter):
        """Test: format_article preserves paragraph breaks"""
        result = formatter.format_article(
            title='Test',
            content='Paragraph 1\n\nParagraph 2\n\nParagraph 3',
            author='Author'
        )
        
        # Should have line breaks between paragraphs
        assert 'Paragraph 1' in result
        assert 'Paragraph 2' in result
        assert 'Paragraph 3' in result
        # Check that there's some separation (newlines or spaces)
        assert '\n' in result or '  ' in result


if __name__ == '__main__':
    print("WhatsAppFormatter Unit Tests")
    print("-" * 70)
    pytest.main([__file__, '-v', '--tb=short'])
