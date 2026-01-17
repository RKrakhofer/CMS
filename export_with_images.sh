#!/bin/bash
#
# FakeDaily Export Script
# Exportiert alle Artikel als JSON und lädt zugehörige Bilder herunter
#

set -e

# Konfiguration
SERVER_URL="${1:-http://localhost:5001}"
EXPORT_DIR="${2:-export_$(date +%Y%m%d_%H%M%S)}"
IMAGES_DIR="$EXPORT_DIR/images"
JSON_FILE="$EXPORT_DIR/articles.json"

# Farben für Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== CMS Export ===${NC}"
echo -e "Server: ${GREEN}$SERVER_URL${NC}"
echo -e "Export-Verzeichnis: ${GREEN}$EXPORT_DIR${NC}"
echo ""

# Export-Verzeichnis erstellen
mkdir -p "$IMAGES_DIR"

# 1. JSON-Export holen
echo -e "${BLUE}[1/2]${NC} Hole JSON-Export..."
if curl -f -s "$SERVER_URL/admin/api/export/articles" -o "$JSON_FILE"; then
    ARTICLE_COUNT=$(jq -r '.count' "$JSON_FILE")
    echo -e "${GREEN}✓${NC} $ARTICLE_COUNT Artikel exportiert → $JSON_FILE"
else
    echo -e "${RED}✗${NC} Fehler beim Abrufen des JSON-Exports"
    exit 1
fi

# 2. Bilder extrahieren und herunterladen
echo -e "\n${BLUE}[2/2]${NC} Lade Bilder herunter..."

# Mapping-Datei für Artikel-ID -> Bilder erstellen
MAPPING_FILE="$EXPORT_DIR/image_mapping.json"

# Extrahiere alle Bild-URLs aus dem JSON
IMAGE_URLS=$(jq -r '.articles[].images[]?.url // empty' "$JSON_FILE")

if [ -z "$IMAGE_URLS" ]; then
    echo -e "${YELLOW}⚠${NC} Keine Bilder im Export gefunden"
    # Leeres Mapping erstellen
    echo "{}" > "$MAPPING_FILE"
    
    # Alle Bilder im Backup-Verzeichnis löschen (keine Bilder mehr im Export)
    if [ -d "$IMAGES_DIR" ] && [ "$(ls -A "$IMAGES_DIR" 2>/dev/null)" ]; then
        echo -e "${YELLOW}🗑${NC} Lösche verwaiste Bilder im Backup-Verzeichnis..."
        rm -f "$IMAGES_DIR"/*
        echo -e "${GREEN}✓${NC} Backup-Verzeichnis bereinigt"
    fi
else
    TOTAL_IMAGES=$(echo "$IMAGE_URLS" | wc -l)
    DOWNLOADED=0
    SKIPPED=0
    CACHED=0
    
    echo -e "Gefundene Bilder: $TOTAL_IMAGES"
    
    # Liste aller Bilder im Export sammeln (für Cleanup)
    declare -A EXPORTED_FILES
    
    # Mapping-Object starten
    echo "{" > "$MAPPING_FILE"
    first_article=true
    
    # Für jeden Artikel: ID und Bilder extrahieren
    jq -c '.articles[] | select(.images and (.images | length) > 0) | {id: .id, images: [.images[].url]}' "$JSON_FILE" | while IFS= read -r article_data; do
        article_id=$(echo "$article_data" | jq -r '.id')
        image_urls=$(echo "$article_data" | jq -r '.images[]')
        
        # Komma vor jedem Eintrag außer dem ersten
        if [ "$first_article" = false ]; then
            echo "," >> "$MAPPING_FILE"
        fi
        first_article=false
        
        # Artikel-ID als Key
        echo -n "  \"$article_id\": [" >> "$MAPPING_FILE"
        
        first_image=true
        for image_url in $image_urls; do
            # Prüfen ob URL vom gleichen Server ist
            if [[ "$image_url" == "$SERVER_URL"* ]]; then
                # Dateinamen extrahieren
                filename=$(basename "$image_url")
                output_path="$IMAGES_DIR/$filename"
                
                # Bild nur herunterladen, wenn es nicht existiert (inkrementell)
                if [ -f "$output_path" ]; then
                    echo -e "  ${BLUE}↻${NC} Artikel $article_id: $filename (bereits vorhanden)"
                    ((CACHED++))
                else
                    # Bild herunterladen
                    if curl -f -s "$image_url" -o "$output_path"; then
                        echo -e "  ${GREEN}✓${NC} Artikel $article_id: $filename"
                        ((DOWNLOADED++))
                    else
                        echo -e "  ${RED}✗${NC} Fehler: $filename"
                    fi
                fi
                
                # Zum Mapping hinzufügen
                if [ "$first_image" = false ]; then
                    echo -n "," >> "$MAPPING_FILE"
                fi
                first_image=false
                echo -n "\"$filename\"" >> "$MAPPING_FILE"
                
                # In Liste der exportierten Dateien aufnehmen
                EXPORTED_FILES["$filename"]=1
            else
                echo -e "  ${YELLOW}↷${NC} Übersprungen (anderer Server): $image_url"
                ((SKIPPED++))
            fi
        done
        
        echo -n "]" >> "$MAPPING_FILE"
    done
    
    # Mapping-Datei schließen
    echo -e "\n}" >> "$MAPPING_FILE"
    
    # JSON formatieren
    tmp_file=$(mktemp)
    jq '.' "$MAPPING_FILE" > "$tmp_file" 2>/dev/null && mv "$tmp_file" "$MAPPING_FILE" || rm -f "$tmp_file"
    
    # Verwaiste Bilder löschen (im Backup vorhanden, aber nicht mehr im Export)
    echo ""
    echo -e "${BLUE}🔍${NC} Prüfe auf verwaiste Bilder..."
    DELETED=0
    if [ -d "$IMAGES_DIR" ]; then
        # Exportierte Dateien aus Mapping extrahieren
        EXPORTED_LIST=$(jq -r '.[] | .[]' "$MAPPING_FILE" 2>/dev/null | sort -u)
        
        # Alle Dateien im Images-Verzeichnis durchgehen
        for file in "$IMAGES_DIR"/*; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")
                # Prüfen ob Datei im Export vorkommt
                if ! echo "$EXPORTED_LIST" | grep -q "^${filename}$"; then
                    echo -e "  ${YELLOW}🗑${NC} Lösche verwaistes Bild: $filename"
                    rm -f "$file"
                    ((DELETED++))
                fi
            fi
        done
    fi
    
    echo ""
    echo -e "${GREEN}✓${NC} $DOWNLOADED Bilder heruntergeladen"
    if [ $CACHED -gt 0 ]; then
        echo -e "${BLUE}↻${NC} $CACHED Bilder aus Cache verwendet"
    fi
    if [ $DELETED -gt 0 ]; then
        echo -e "${YELLOW}🗑${NC} $DELETED verwaiste Bilder gelöscht"
    fi
    if [ $SKIPPED -gt 0 ]; then
        echo -e "${YELLOW}⚠${NC} $SKIPPED Bilder übersprungen (anderer Server)"
    fi
    echo -e "${GREEN}✓${NC} Bild-Zuordnung erstellt: image_mapping.json"
fi

# Zusammenfassung
echo ""
echo -e "${BLUE}=== Export abgeschlossen ===${NC}"
echo -e "Speicherort: ${GREEN}$EXPORT_DIR${NC}"
echo ""
echo "Inhalt:"
echo "  - articles.json (JSON-Daten)"
echo "  - images/ ($(ls -1 "$IMAGES_DIR" 2>/dev/null | wc -l) Bilder)"
echo "  - image_mapping.json (Bild-Zuordnungen)"
echo ""
echo -e "${BLUE}Tipp:${NC} Zum Importieren verwende:"
echo "  ./import_with_images.sh $EXPORT_DIR [server_url]"
echo ""
echo "Oder manuell:"
echo "  curl -X POST http://other-server:5001/admin/api/import/articles \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d @$JSON_FILE"
