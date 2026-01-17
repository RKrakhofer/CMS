"""
WhatsApp Formatter für CMS
Konvertiert Markdown zu WhatsApp-Formatierung
"""
import re

class WhatsAppFormatter:
    """Konvertiert Markdown zu WhatsApp-Formatierung"""
    
    @staticmethod
    def convert(markdown_text: str) -> str:
        """
        Konvertiert Markdown zu WhatsApp-Format
        
        WhatsApp-Formatierung:
        - *fett*
        - _kursiv_
        - ~durchgestrichen~
        - ```code```
        
        Args:
            markdown_text: Markdown-Text
            
        Returns:
            WhatsApp-formatierter Text
        """
        text = markdown_text
        
        # Überschriften (# bis ######) - Temporär mit Platzhalter ersetzen
        text = re.sub(r'^######\s+(.+)$', r'⚡BOLD⚡\1⚡BOLD⚡', text, flags=re.MULTILINE)
        text = re.sub(r'^#####\s+(.+)$', r'⚡BOLD⚡\1⚡BOLD⚡', text, flags=re.MULTILINE)
        text = re.sub(r'^####\s+(.+)$', r'⚡BOLD⚡\1⚡BOLD⚡', text, flags=re.MULTILINE)
        text = re.sub(r'^###\s+(.+)$', r'⚡BOLD⚡\1⚡BOLD⚡', text, flags=re.MULTILINE)
        text = re.sub(r'^##\s+(.+)$', r'⚡BOLD⚡\1⚡BOLD⚡', text, flags=re.MULTILINE)
        text = re.sub(r'^#\s+(.+)$', r'⚡BOLD⚡\1⚡BOLD⚡\n', text, flags=re.MULTILINE)
        
        # Fett: **text** oder __text__ → Temporärer Platzhalter
        text = re.sub(r'\*\*(.+?)\*\*', r'⚡BOLD⚡\1⚡BOLD⚡', text)
        text = re.sub(r'__(.+?)__', r'⚡BOLD⚡\1⚡BOLD⚡', text)
        
        # Kursiv: *text* oder _text_ → _text_
        # Jetzt können wir sicher * durch _ ersetzen, da alle Bold-Marker geschützt sind
        text = re.sub(r'(?<![⚡\*])\*(?!\*)(.+?)(?<!\*)\*(?![⚡\*])', r'_\1_', text)
        text = re.sub(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)', r'_\1_', text)
        
        # Platzhalter durch WhatsApp-Bold ersetzen
        text = text.replace('⚡BOLD⚡', '*')
        
        # Durchgestrichen: ~~text~~ → ~text~
        text = re.sub(r'~~(.+?)~~', r'~\1~', text)
        
        # Code inline: `code` → ```code```
        text = re.sub(r'`([^`]+)`', r'```\1```', text)
        
        # Code-Blöcke: ```lang\ncode\n``` → ```code```
        text = re.sub(r'```\w*\n(.*?)```', r'```\1```', text, flags=re.DOTALL)
        
        # Links: [text](url) → text: url
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'\1: \2', text)
        
        # Bilder entfernen (werden separat behandelt): ![alt](url)
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'', text)
        
        # Listen: - item oder * item → • item
        text = re.sub(r'^[\-\*]\s+', r'• ', text, flags=re.MULTILINE)
        
        # Nummerierte Listen beibehalten
        # 1. item bleibt 1. item
        
        # Mehrfache Leerzeilen reduzieren
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    @staticmethod
    def format_article(title: str, content: str, author: str = None) -> str:
        """
        Formatiert einen kompletten Artikel für WhatsApp
        
        Args:
            title: Artikel-Titel
            content: Markdown-Inhalt
            author: Autor (optional)
            
        Returns:
            WhatsApp-fertiger Text
        """
        parts = []
        
        # Titel (fett und groß)
        parts.append(f"*{title.upper()}*")
        parts.append("")
        
        # Inhalt
        parts.append(WhatsAppFormatter.convert(content))
        
        # Autor am Ende
        if author:
            parts.append("")
            parts.append(f"_{author}_")
        
        return "\n".join(parts)


if __name__ == "__main__":
    # Test
    markdown = """# Überschrift 1

Dies ist ein **fetter Text** und das ist _kursiv_.

## Überschrift 2

- Listenpunkt 1
- Listenpunkt 2

Hier ist ein [Link](https://example.com) und `Code`.

```python
print("Hello")
```

~~Durchgestrichen~~
"""
    
    print("=== Original Markdown ===")
    print(markdown)
    print("\n=== WhatsApp Format ===")
    print(WhatsAppFormatter.convert(markdown))
