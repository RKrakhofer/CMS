#!/bin/bash
#
# FakeDaily Complete Backup Script
# Sichert Datenbank, Bilder und Konfiguration
#

set -e

# Konfiguration
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
DB_PATH="${DB_PATH:-database/articles.db}"
IMAGES_PATH="${IMAGES_PATH:-media/images}"

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== CMS Complete Backup ===${NC}"
echo -e "Backup-Verzeichnis: ${GREEN}$BACKUP_DIR${NC}"
echo ""

# Backup-Verzeichnis erstellen
mkdir -p "$BACKUP_DIR"

# 1. Datenbank sichern
echo -e "${BLUE}[1/3]${NC} Sichere Datenbank..."
if [ -f "$DB_PATH" ]; then
    cp "$DB_PATH" "$BACKUP_DIR/articles.db"
    DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
    echo -e "${GREEN}✓${NC} Datenbank gesichert ($DB_SIZE)"
else
    echo -e "${RED}✗${NC} Datenbank nicht gefunden: $DB_PATH"
    exit 1
fi

# 2. Bilder sichern
echo -e "\n${BLUE}[2/3]${NC} Sichere Bilder..."
if [ -d "$IMAGES_PATH" ]; then
    IMAGE_COUNT=$(find "$IMAGES_PATH" -type f | wc -l)
    if [ $IMAGE_COUNT -gt 0 ]; then
        cp -r "$IMAGES_PATH" "$BACKUP_DIR/images"
        IMAGES_SIZE=$(du -sh "$IMAGES_PATH" | cut -f1)
        echo -e "${GREEN}✓${NC} $IMAGE_COUNT Bilder gesichert ($IMAGES_SIZE)"
    else
        echo -e "${GREEN}✓${NC} Keine Bilder vorhanden"
    fi
else
    echo -e "${GREEN}✓${NC} Kein Images-Verzeichnis vorhanden"
fi

# 3. JSON-Export erstellen (für Interoperabilität)
echo -e "\n${BLUE}[3/3]${NC} Erstelle JSON-Export..."
if command -v python3 &> /dev/null; then
    python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, 'src')
from db_manager import DatabaseManager
import json

db = DatabaseManager()
articles = db.get_all_articles()

# Bilder für jeden Artikel laden
for article in articles:
    images = db.get_images_for_article(article['id'])
    article['images'] = images

export_data = {
    'success': True,
    'count': len(articles),
    'articles': articles,
    'backup_type': 'complete',
    'backup_date': __import__('datetime').datetime.now().isoformat()
}

with open('BACKUP_DIR/export.json', 'w', encoding='utf-8') as f:
    json.dump(export_data, f, indent=2, ensure_ascii=False)

print(f"JSON-Export erstellt: {len(articles)} Artikel")
PYTHON_SCRIPT
    sed -i "s|BACKUP_DIR|$BACKUP_DIR|g" "$BACKUP_DIR/export.json" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} JSON-Export erstellt"
else
    echo -e "${BLUE}ℹ${NC} Python nicht verfügbar - JSON-Export übersprungen"
fi

# 4. Backup komprimieren
echo -e "\n${BLUE}[4/4]${NC} Komprimiere Backup..."
tar -czf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR"
BACKUP_SIZE=$(du -h "${BACKUP_DIR}.tar.gz" | cut -f1)
rm -rf "$BACKUP_DIR"

# Zusammenfassung
echo ""
echo -e "${BLUE}=== Backup abgeschlossen ===${NC}"
echo -e "Datei: ${GREEN}${BACKUP_DIR}.tar.gz${NC} ($BACKUP_SIZE)"
echo ""
echo "Inhalt:"
echo "  - articles.db (SQLite-Datenbank)"
echo "  - images/ (Alle Bilder)"
echo "  - export.json (JSON-Export)"
echo ""
echo -e "${BLUE}Wiederherstellung:${NC}"
echo "  tar -xzf ${BACKUP_DIR}.tar.gz"
echo "  cp ${BACKUP_DIR}/articles.db database/"
echo "  cp -r ${BACKUP_DIR}/images/* media/images/"
