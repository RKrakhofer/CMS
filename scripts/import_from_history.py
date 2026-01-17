#!/usr/bin/env python3
"""
Importiert Artikel aus history.txt in die Datenbank.
Erstellt zuerst eine SQL-Datei zur Überprüfung.
"""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Projekt-Root finden
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

def parse_history_file(file_path):
    """Extrahiert Artikel aus der history.txt"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Teile den Chat in Blöcke
    articles = []
    
    # Finde alle "Du:" Prompts und "ChatGPT:" Antworten
    pattern = r'Du:\s*\n(.*?)\nChatGPT:\s*\n(.*?)(?=\nDu:|$)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for prompt, response in matches:
        prompt = prompt.strip()
        response = response.strip()
        
        # Überspringe Meta-Anweisungen
        if any(skip in prompt.lower() for skip in ['füge hinzu', 'ändere', 'korrigiere', 'bolsonaro', 'trump']):
            continue
            
        # Extrahiere nur wenn es "Erstelle Zeitungsmeldung" enthält
        if 'erstelle zeitungsmeldung' in prompt.lower():
            # Versuche Titel zu extrahieren
            title_match = re.search(r'Erstelle Zeitungsmeldung:\s*(.+?)(?:\n|$)', prompt, re.IGNORECASE)
            if title_match:
                prompt_title = title_match.group(1).strip()
            else:
                prompt_title = prompt[:100]
            
            # Extrahiere den eigentlichen Artikel aus der Antwort
            # Suche nach dem ersten Titel (meist fett oder als Überschrift)
            lines = response.split('\n')
            article_lines = []
            article_title = None
            in_article = False
            
            for line in lines:
                line = line.strip()
                # Überspringe ChatGPT Meta-Text
                if line.startswith('Hier ist') or line.startswith('Falls du') or '😊' in line or '😆' in line:
                    continue
                
                # Erster nicht-leerer Text nach Meta = Titel
                if not article_title and line and not in_article:
                    article_title = line.replace('**', '').replace('##', '').strip()
                    in_article = True
                    continue
                
                if in_article and line:
                    article_lines.append(line)
            
            if article_title and article_lines:
                content_text = '\n\n'.join(article_lines)
                articles.append({
                    'prompt': prompt_title,
                    'title': article_title,
                    'content': content_text
                })
    
    return articles


def assign_dates_and_correlate(articles):
    """Weist Artikel Daten zu (Juni 2025 - Januar 2026) und korreliert mit realen Ereignissen"""
    
    # Startdatum: Juni 2025
    start_date = datetime(2025, 6, 1)
    # Enddatum: Vor kurzem (ca. Anfang Januar 2026)
    end_date = datetime(2026, 1, 10)
    
    # Berechne Zeitabstand zwischen Artikeln
    total_days = (end_date - start_date).days
    num_articles = len(articles)
    
    if num_articles == 0:
        return []
    
    days_between = total_days / num_articles if num_articles > 1 else 0
    
    dated_articles = []
    current_date = start_date
    
    # Reale Ereignisse zur Korrelation (Beispiele für 2025/2026)
    # Diese können angepasst werden basierend auf tatsächlichen Ereignissen
    real_events = {
        (2025, 6): "Beginn der heißen Phase der österreichischen Wahlkampagne",
        (2025, 7): "Sommerhitze und Klimadiskussionen in Europa",
        (2025, 8): "Urlaubssaison und Reisewarnungen",
        (2025, 9): "Nationalratswahl in Österreich",
        (2025, 10): "Koalitionsverhandlungen in Österreich beginnen",
        (2025, 11): "Budgetverhandlungen und Wirtschaftskrise",
        (2025, 12): "Jahresendpolitik und Reformdiskussionen",
        (2026, 1): "Neujahr und politische Neuausrichtung"
    }
    
    for i, article in enumerate(articles):
        # Datum zuweisen
        pub_date = current_date + timedelta(days=int(i * days_between))
        
        # Event-Kontext
        month_key = (pub_date.year, pub_date.month)
        context = real_events.get(month_key, "")
        
        # Tags basierend auf Inhalt generieren
        tags = generate_tags(article['title'], article['content'])
        
        dated_articles.append({
            'title': article['title'],
            'content': article['content'],
            'author': 'Chefredakteur',
            'created_at': pub_date.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': pub_date.strftime('%Y-%m-%d %H:%M:%S'),
            'tags': tags,
            'published': 1,  # Boolean: 1 = veröffentlicht
            'context': context
        })
        
    return dated_articles


def generate_tags(title, content):
    """Generiert Tags basierend auf Inhalt"""
    tags = []
    text = (title + ' ' + content).lower()
    
    # Politik
    if any(word in text for word in ['kickl', 'övp', 'fpö', 'regierung', 'koalition', 'wahl', 'parlament']):
        tags.append('Politik')
    
    # Satire
    if any(word in text for word in ['satiriker', 'fake daily', 'satire']):
        tags.append('Medien')
    
    # International
    if any(word in text for word in ['uno', 'deutschland', 'putin', 'orbán', 'trump', 'international']):
        tags.append('International')
    
    # Gesellschaft
    if any(word in text for word in ['wissenschaft', 'bildung', 'gesellschaft', 'meinungsfreiheit']):
        tags.append('Gesellschaft')
    
    # Österreich
    if any(word in text for word in ['österreich', 'wien', 'kickl', 'övp', 'fpö']):
        tags.append('Österreich')
    
    # Deutschland
    if 'deutschland' in text or 'berlin' in text:
        tags.append('Deutschland')
    
    # Satire immer dabei
    tags.append('Satire')
    
    return ', '.join(list(set(tags)))  # Unique tags


def generate_sql(articles, output_file):
    """Generiert SQL INSERT Statements"""
    
    sql_lines = [
        "-- FakeDaily Artikel Import",
        "-- Generiert am: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "-- Anzahl Artikel: " + str(len(articles)),
        "",
        "-- Backup erstellen vor Import:",
        "-- cp database/articles.db database/articles_backup_$(date +%Y%m%d_%H%M%S).db",
        "",
    ]
    
    for i, article in enumerate(articles, 1):
        # Escape single quotes in SQL
        title = article['title'].replace("'", "''")
        content = article['content'].replace("'", "''")
        author = article['author'].replace("'", "''")
        tags = article['tags'].replace("'", "''")
        
        sql_lines.append(f"-- Artikel {i}: {article['created_at'][:10]}")
        if article['context']:
            sql_lines.append(f"-- Kontext: {article['context']}")
        
        sql = f"""INSERT INTO articles (title, content, author, created_at, updated_at, tags, published)
VALUES (
    '{title}',
    '{content}',
    '{author}',
    '{article['created_at']}',
    '{article['updated_at']}',
    '{tags}',
    {article['published']}
);
"""
        sql_lines.append(sql)
    
    # SQL-Datei schreiben
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))
    
    print(f"✅ SQL-Datei erstellt: {output_file}")
    print(f"📊 {len(articles)} Artikel")
    print(f"📅 Zeitraum: {articles[0]['created_at'][:10]} bis {articles[-1]['created_at'][:10]}")
    print()
    print("Überprüfe die SQL-Datei und führe dann aus:")
    print(f"  sqlite3 database/articles.db < {output_file}")


def main():
    history_file = project_root / 'history.txt'
    output_sql = project_root / 'import_articles.sql'
    
    print("📖 Lese history.txt...")
    articles = parse_history_file(history_file)
    print(f"   Gefunden: {len(articles)} Artikel-Rohdaten")
    
    print("\n📅 Weise Daten zu und korreliere mit realen Ereignissen...")
    dated_articles = assign_dates_and_correlate(articles)
    
    print("\n💾 Generiere SQL-Datei...")
    generate_sql(dated_articles, output_sql)
    
    # Zeige Vorschau
    print("\n📰 Vorschau (erste 3 Artikel):")
    for article in dated_articles[:3]:
        print(f"\n  {article['created_at'][:10]} - {article['title'][:60]}")
        print(f"  Tags: {article['tags']}")
        if article['context']:
            print(f"  Kontext: {article['context']}")


if __name__ == '__main__':
    main()
