#!/usr/bin/env python3
"""
Parst WhatsApp-Chat und extrahiert Fake-Daily Artikel
"""
import re
from datetime import datetime

def parse_whatsapp_chat(filepath):
    """Liest WhatsApp-Chat und extrahiert Artikel mit Bildern"""
    
    articles = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Teile den Chat in Nachrichten auf
    # Format: DD.MM.YY, HH:MM - Sender: Nachricht
    message_pattern = r'(\d{2}\.\d{2}\.\d{2}, \d{2}:\d{2}) - Richard Krakhofer: (.*?)(?=\d{2}\.\d{2}\.\d{2}, \d{2}:\d{2} -|$)'
    
    messages = re.findall(message_pattern, content, re.DOTALL)
    
    i = 0
    while i < len(messages):
        timestamp, message = messages[i]
        
        # Bereinige Nachricht von Zeilenumbrüchen innerhalb des Textes
        message = message.strip()
        
        # Suche nach Bildanhang
        if '‎IMG-' in message and '.jpg' in message:
            # Extrahiere Bildnamen
            image_match = re.search(r'‎(IMG-\d+-WA\d+\.jpg)', message)
            if image_match:
                image_name = image_match.group(1)
                
                # Extrahiere Text nach dem Bild in derselben Nachricht
                text_after_image = message.split(image_name, 1)[1] if image_name in message else ""
                text_after_image = text_after_image.strip()
                
                article_text = text_after_image
                
                # Wenn kein Text nach dem Bild, schaue in die nächste Nachricht
                if len(text_after_image) < 50 and i + 1 < len(messages):
                    next_timestamp, next_message = messages[i + 1]
                    next_message = next_message.strip()
                    
                    # Prüfe ob die nächste Nachricht Text enthält (kein weiteres Bild/Video/Doc)
                    if not ('‎IMG-' in next_message or '‎VID-' in next_message or '‎DOC-' in next_message):
                        article_text = next_message
                
                # Bereinige den Text
                article_text = article_text.replace('<Diese Nachricht wurde bearbeitet.>', '').strip()
                # Entferne "(Datei angehängt)" am Anfang
                if article_text.startswith('(Datei angehängt)'):
                    article_text = article_text.replace('(Datei angehängt)', '', 1).strip()
                
                # Prüfe ob es genug Text ist und wie ein Fake-Daily Artikel aussieht
                if len(article_text) > 100:
                    # Prüfe auf typische Artikel-Merkmale
                    if ('*' in article_text or 
                        any(emoji in article_text for emoji in ['🎸', '🚨', '🐮', '🏦', '💉', '🤖', '🇺🇸', '🇦🇹', '🇪🇺', '🔬', '🌌', '📰', '🗞️', '💡', '🇩🇪', '🍨', '🥩', '☀️', '📱', '📸']) or
                        'Fake Daily' in article_text or 
                        'FAKE DAILY' in article_text or
                        re.search(r'\*.*\*', article_text)):  # Text mit Sternchen (Markdown Bold)
                        
                        articles.append({
                            'timestamp': timestamp,
                            'image': image_name,
                            'text': article_text
                        })
        
        i += 1
    
    return articles

def create_markdown(articles, output_file):
    """Erstellt Markdown-Datei mit allen Artikeln"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Fake-Daily Artikel History\n\n")
        f.write(f"Extrahiert am: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n")
        f.write(f"Anzahl Artikel: {len(articles)}\n\n")
        f.write("---\n\n")
        
        for idx, article in enumerate(articles, 1):
            # Extrahiere Titel (erste Zeile)
            lines = article['text'].split('\n')
            title = lines[0].strip() if lines else "Ohne Titel"
            rest_text = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
            
            f.write(f"## Artikel {idx}\n\n")
            f.write(f"**Titel:** {title}\n\n")
            f.write(f"**Datum/Uhrzeit:** {article['timestamp']}\n\n")
            f.write(f"**Bild:** `{article['image']}`\n\n")
            f.write(f"**Bildpfad:** `/mnt/nas-synology-1/home/Downloads/WhatsApp-Chat mit +43 676 3518170/{article['image']}`\n\n")
            if rest_text:
                f.write(f"**Text:**\n\n")
                f.write(f"{rest_text}\n\n")
            f.write("---\n\n")

if __name__ == '__main__':
    chat_file = '/mnt/nas-synology-1/home/Downloads/WhatsApp-Chat mit +43 676 3518170/WhatsApp-Chat mit +43 676 3518170.txt'
    output_file = '/home/richard/workspaces/FakeDaily/Artikel_History.md'
    
    print(f"Lese WhatsApp-Chat: {chat_file}")
    articles = parse_whatsapp_chat(chat_file)
    
    print(f"Gefundene Artikel: {len(articles)}")
    
    print(f"Erstelle Markdown: {output_file}")
    create_markdown(articles, output_file)
    
    print("Fertig!")
