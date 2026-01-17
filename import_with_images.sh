#!/bin/bash
#
# FakeDaily Import Script
# Importiert ein von export_with_images.sh erstelltes Verzeichnis
#

set -e

# Farben für Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Hilfe anzeigen
show_help() {
    echo "Usage: $0 <export_directory> [server_url]"
    echo ""
    echo "Importiert Artikel und Bilder aus einem Export-Verzeichnis"
    echo ""
    echo "Argumente:"
    echo "  export_directory    Pfad zum Export-Verzeichnis (z.B. export_20260116_123456)"
    echo "  server_url          Ziel-Server URL (default: http://localhost:5001)"
    echo ""
    echo "Beispiele:"
    echo "  $0 export_20260116_123456"
    echo "  $0 export_20260116_123456 http://stage:5001/cms"
    exit 1
}

# Parameter prüfen
if [ $# -lt 1 ]; then
    show_help
fi

EXPORT_DIR="$1"
SERVER_URL="${2:-http://localhost:5001}"
JSON_FILE="$EXPORT_DIR/articles.json"
IMAGES_DIR="$EXPORT_DIR/images"

echo -e "${BLUE}=== CMS Import ===${NC}"
echo -e "Export-Verzeichnis: ${GREEN}$EXPORT_DIR${NC}"
echo -e "Ziel-Server: ${GREEN}$SERVER_URL${NC}"
echo ""

# Prüfen ob Export-Verzeichnis existiert
if [ ! -d "$EXPORT_DIR" ]; then
    echo -e "${RED}✗${NC} Export-Verzeichnis nicht gefunden: $EXPORT_DIR"
    exit 1
fi

# Prüfen ob articles.json existiert
if [ ! -f "$JSON_FILE" ]; then
    echo -e "${RED}✗${NC} articles.json nicht gefunden in: $EXPORT_DIR"
    exit 1
fi

# 1. JSON-Import
echo -e "${BLUE}[1/2]${NC} Importiere Artikel..."

response=$(curl -s -X POST "$SERVER_URL/admin/api/import/articles" \
    -H "Content-Type: application/json" \
    -d @"$JSON_FILE")

# Prüfen ob erfolgreich
if echo "$response" | jq -e '.success' > /dev/null 2>&1; then
    imported=$(echo "$response" | jq -r '.imported // 0')
    updated=$(echo "$response" | jq -r '.updated // 0')
    skipped=$(echo "$response" | jq -r '.skipped // 0')
    errors=$(echo "$response" | jq -r '.errors | length // 0')
    
    echo -e "${GREEN}✓${NC} Import erfolgreich:"
    echo -e "  - Neu importiert: $imported"
    echo -e "  - Aktualisiert: $updated"
    echo -e "  - Übersprungen: $skipped"
    
    if [ "$errors" -gt 0 ]; then
        echo -e "  - ${RED}Fehler: $errors${NC}"
        echo "$response" | jq -r '.errors[]' | while read -r error; do
            echo -e "    ${RED}→${NC} $error"
        done
    fi
else
    echo -e "${RED}✗${NC} Import fehlgeschlagen"
    echo "$response" | jq '.' 2>/dev/null || echo "$response"
    exit 1
fi

# 2. Bilder hochladen (optional, falls Verzeichnis existiert)
if [ -d "$IMAGES_DIR" ]; then
    echo -e "\n${BLUE}[2/2]${NC} Lade Bilder hoch..."
    
    image_count=$(ls -1 "$IMAGES_DIR" 2>/dev/null | wc -l)
    
    if [ "$image_count" -eq 0 ]; then
        echo -e "${YELLOW}⚠${NC} Keine Bilder im Export-Verzeichnis gefunden"
    else
        echo -e "Gefundene Bilder: $image_count"
        
        # Mapping-Datei lesen (article_id -> image_files)
        mapping_file="$EXPORT_DIR/image_mapping.json"
        
        if [ -f "$mapping_file" ]; then
            # Bilder pro Artikel hochladen
            uploaded_total=0
            failed_total=0
            
            # Alle Artikel-IDs aus Mapping extrahieren
            article_ids=$(jq -r 'keys[]' "$mapping_file")
            
            for article_id in $article_ids; do
                # Bilder für diesen Artikel holen
                images=$(jq -r ".\"$article_id\"[]" "$mapping_file")
                
                if [ -z "$images" ]; then
                    continue
                fi
                
                echo -e "\n  Artikel ID $article_id:"
                
                # curl-Kommando mit multipart/form-data aufbauen
                curl_cmd="curl -s -X POST \"$SERVER_URL/admin/api/upload/images/$article_id\""
                
                for image in $images; do
                    image_path="$IMAGES_DIR/$image"
                    if [ -f "$image_path" ]; then
                        curl_cmd="$curl_cmd -F \"images=@$image_path\""
                    fi
                done
                
                # API-Request ausführen
                upload_response=$(eval $curl_cmd)
                
                # Response auswerten
                if echo "$upload_response" | jq -e '.success' > /dev/null 2>&1; then
                    uploaded=$(echo "$upload_response" | jq -r '.uploaded // 0')
                    errors=$(echo "$upload_response" | jq -r '.errors | length // 0')
                    
                    echo -e "    ${GREEN}✓${NC} Hochgeladen: $uploaded Bild(er)"
                    uploaded_total=$((uploaded_total + uploaded))
                    
                    if [ "$errors" -gt 0 ]; then
                        echo -e "    ${RED}✗${NC} Fehler: $errors"
                        echo "$upload_response" | jq -r '.errors[]' | while read -r error; do
                            echo -e "      ${RED}→${NC} $error"
                        done
                        failed_total=$((failed_total + errors))
                    fi
                else
                    echo -e "    ${RED}✗${NC} Upload fehlgeschlagen"
                    echo "$upload_response" | jq '.' 2>/dev/null || echo "$upload_response"
                    # Anzahl der Bilder zu failed hinzufügen
                    img_count=$(echo "$images" | wc -w)
                    failed_total=$((failed_total + img_count))
                fi
            done
            
            echo -e "\n${GREEN}✓${NC} Bilder-Upload abgeschlossen:"
            echo -e "  - Erfolgreich: $uploaded_total"
            if [ "$failed_total" -gt 0 ]; then
                echo -e "  - ${RED}Fehlgeschlagen: $failed_total${NC}"
            fi
        else
            echo -e "${YELLOW}⚠${NC} Keine Bild-Zuordnung gefunden (image_mapping.json fehlt)"
            echo -e "  Bilder-Verzeichnis: ${GREEN}$IMAGES_DIR${NC}"
            echo ""
            echo -e "Tipp: Kopiere die Bilder direkt ins media/images/ Verzeichnis:"
            echo -e "  ${BLUE}cp $IMAGES_DIR/* /pfad/zu/cms/media/images/${NC}"
        fi
    fi
else
    echo -e "\n${BLUE}[2/2]${NC} Keine Bilder im Export"
fi

# Zusammenfassung
echo ""
echo -e "${BLUE}=== Import abgeschlossen ===${NC}"
echo -e "Ziel-Server: ${GREEN}$SERVER_URL${NC}"
echo ""
echo -e "${BLUE}Nächste Schritte:${NC}"
echo "  1. Prüfe importierte Artikel: $SERVER_URL/admin/"
if [ -f "$EXPORT_DIR/image_mapping.json" ]; then
    echo "  2. Bilder wurden automatisch hochgeladen und zugeordnet"
else
    echo "  2. Lade Bilder manuell hoch oder kopiere sie ins media/images/ Verzeichnis"
fi
