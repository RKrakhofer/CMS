#!/bin/bash
#
# FakeDaily Test Runner
# Führt Export/Import Loop Tests aus
#

set -e

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Konfiguration
SERVER_URL="${CMS_URL:-http://localhost:5001}"
APP_PREFIX="${CMS_PREFIX:-}"

echo -e "${BLUE}=== FakeDaily Export/Import Loop Tests ===${NC}"
echo -e "Server: ${GREEN}${SERVER_URL}${APP_PREFIX}${NC}"
echo ""

# Prüfen ob pytest installiert ist
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}✗${NC} pytest nicht gefunden"
    echo -e "Installation: ${BLUE}pip install -r requirements.txt${NC}"
    exit 1
fi

# Prüfen ob Server erreichbar ist
echo -e "${BLUE}[1/3]${NC} Prüfe Server-Erreichbarkeit..."
if curl -s -f "${SERVER_URL}${APP_PREFIX}/reader/" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Server erreichbar"
else
    echo -e "${RED}✗${NC} Server nicht erreichbar: ${SERVER_URL}${APP_PREFIX}"
    echo ""
    echo -e "Starte den Server mit:"
    echo -e "  ${BLUE}cd .. && python start_web.py${NC}"
    exit 1
fi

# Test-Modus wählen
TEST_MODE="${1:-all}"

echo -e "\n${BLUE}[2/3]${NC} Führe Tests aus..."

case "$TEST_MODE" in
    "simple")
        echo -e "Modus: ${YELLOW}Einfacher Export/Import Test${NC}"
        pytest test_export_import_loop.py::TestExportImportLoop::test_simple_export_import_loop -v -s
        ;;
    "images")
        echo -e "Modus: ${YELLOW}Test mit Bildern${NC}"
        pytest test_export_import_loop.py::TestExportImportLoop::test_export_import_with_images -v -s
        ;;
    "cycle")
        echo -e "Modus: ${YELLOW}Vollständiger Zyklus${NC}"
        pytest test_export_import_loop.py::TestExportImportLoop::test_full_export_import_cycle -v -s
        ;;
    "integrity")
        echo -e "Modus: ${YELLOW}Datenintegrität${NC}"
        pytest test_export_import_loop.py::TestExportImportLoop::test_export_import_preserves_data_integrity -v -s
        ;;
    "edge")
        echo -e "Modus: ${YELLOW}Edge Cases${NC}"
        pytest test_export_import_loop.py::TestExportImportEdgeCases -v -s
        ;;
    "all")
        echo -e "Modus: ${YELLOW}Alle Export/Import Tests${NC}"
        pytest test_export_import_loop.py -v -s
        ;;
    "api")
        echo -e "Modus: ${YELLOW}Alle API Tests${NC}"
        pytest test_api.py test_export_import_loop.py -v
        ;;
    *)
        echo -e "${RED}✗${NC} Unbekannter Modus: $TEST_MODE"
        echo ""
        echo "Verwendung: $0 [mode]"
        echo ""
        echo "Modi:"
        echo "  simple    - Einfacher Export/Import Test"
        echo "  images    - Test mit Bildupload"
        echo "  cycle     - Vollständiger Zyklus (Export, Delete, Import)"
        echo "  integrity - Datenintegrität (Unicode, Tags, Timestamps)"
        echo "  edge      - Edge Cases und Fehlerbehandlung"
        echo "  all       - Alle Export/Import Tests (default)"
        echo "  api       - Alle Tests (API + Export/Import)"
        exit 1
        ;;
esac

# Status
if [ $? -eq 0 ]; then
    echo -e "\n${BLUE}[3/3]${NC} ${GREEN}✓ Tests erfolgreich${NC}"
    echo ""
    echo -e "${GREEN}Alle Tests bestanden!${NC}"
    echo -e "DB wurde automatisch aufgeräumt (Test-Artikel gelöscht)"
else
    echo -e "\n${BLUE}[3/3]${NC} ${RED}✗ Tests fehlgeschlagen${NC}"
    exit 1
fi
