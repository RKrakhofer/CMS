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
        
        # Normalisiere Überschriften: Entferne Newlines innerhalb von Überschriften-Zeilen
        # Dies behebt das Problem, wenn Überschriften über mehrere Zeilen gehen
        def normalize_heading(match):
            hashes = match.group(1)
            content = match.group(2)
            # Entferne alle Newlines und reduziere Whitespace
            content = re.sub(r'\s+', ' ', content).strip()
            return f"{hashes} {content}"
        
        text = re.sub(r'^(#{1,6})\s+(.+?)$', normalize_heading, text, flags=re.MULTILINE)
        
        # Überschriften (# bis ######) - Temporär mit Platzhalter ersetzen und Whitespace trimmen
        text = re.sub(r'^######\s+(.+?)\s*$', r'⚡BOLD⚡\1⚡BOLD⚡', text, flags=re.MULTILINE)
        text = re.sub(r'^#####\s+(.+?)\s*$', r'⚡BOLD⚡\1⚡BOLD⚡', text, flags=re.MULTILINE)
        text = re.sub(r'^####\s+(.+?)\s*$', r'⚡BOLD⚡\1⚡BOLD⚡', text, flags=re.MULTILINE)
        text = re.sub(r'^###\s+(.+?)\s*$', r'⚡BOLD⚡\1⚡BOLD⚡', text, flags=re.MULTILINE)
        text = re.sub(r'^##\s+(.+?)\s*$', r'⚡BOLD⚡\1⚡BOLD⚡', text, flags=re.MULTILINE)
        text = re.sub(r'^#\s+(.+?)\s*$', r'⚡BOLD⚡\1⚡BOLD⚡\n', text, flags=re.MULTILINE)
        
        # Fett: **text** oder __text__ → Temporärer Platzhalter
        # DOTALL-Flag für mehrzeilige Bold-Texte
        text = re.sub(r'\*\*(.+?)\*\*', r'⚡BOLD⚡\1⚡BOLD⚡', text, flags=re.DOTALL)
        text = re.sub(r'__(.+?)__', r'⚡BOLD⚡\1⚡BOLD⚡', text, flags=re.DOTALL)
        
        # Kursiv: *text* oder _text_ → _text_
        # Jetzt können wir sicher * durch _ ersetzen, da alle Bold-Marker geschützt sind
        # DOTALL-Flag für mehrzeilige Kursiv-Texte
        text = re.sub(r'(?<![⚡\*])\*(?!\*)(.+?)(?<!\*)\*(?![⚡\*])', r'⚡ITALIC⚡\1⚡ITALIC⚡', text, flags=re.DOTALL)
        
        # Platzhalter durch WhatsApp-Formatierung ersetzen und Newlines entfernen
        # WhatsApp unterstützt keine mehrzeilige Formatierung!
        def clean_bold(match):
            content = match.group(1)
            # Entferne Newlines und reduziere Whitespace
            content = re.sub(r'\s+', ' ', content).strip()
            return f"*{content}*"
        
        def clean_italic(match):
            content = match.group(1)
            # Entferne Newlines und reduziere Whitespace
            content = re.sub(r'\s+', ' ', content).strip()
            return f"_{content}_"
        
        text = re.sub(r'⚡BOLD⚡(.+?)⚡BOLD⚡', clean_bold, text, flags=re.DOTALL)
        text = re.sub(r'⚡ITALIC⚡(.+?)⚡ITALIC⚡', clean_italic, text, flags=re.DOTALL)
        
        # Durchgestrichen: ~~text~~ → ~text~
        text = re.sub(r'~~(.+?)~~', r'~\1~', text, flags=re.DOTALL)
        
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
        
        # Entferne führende/nachfolgende Whitespace bei jeder Zeile
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        text = '\n'.join(lines)
        
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
