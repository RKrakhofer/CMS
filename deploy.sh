#!/bin/bash

# CMS Docker Build & Deploy Script

set -e

echo "======================================"
echo "🐳 FakeDaily Docker Deploy"
echo "======================================"

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Konfiguration
REMOTE_USER="uu"
REMOTE_HOST="stage"
REMOTE_PATH="FakeDaily"

# Deployment-Modus wählen
if [ "$1" == "local" ]; then
    echo -e "${BLUE}📦 Lokales Deployment${NC}\n"
    
    IMAGE_NAME="fakedaily"
    VERSION=$(date +%Y%m%d-%H%M%S)

    echo -e "${BLUE}🔨 Building Docker Image...${NC}"
    docker build -t ${IMAGE_NAME}:latest -t ${IMAGE_NAME}:${VERSION} .

    echo -e "\n${GREEN}✅ Build erfolgreich!${NC}"
    echo -e "   Images: ${IMAGE_NAME}:latest, ${IMAGE_NAME}:${VERSION}"

    echo -e "\n${BLUE}🚀 Starte mit Docker Compose...${NC}"
    docker-compose up -d

    echo -e "\n${GREEN}✅ Container gestartet!${NC}"
    echo -e "\n📍 FakeDaily läuft auf: http://localhost:5001"
    echo -e "\n💡 Befehle:"
    echo -e "   ${BLUE}docker-compose logs -f${NC}        - Logs anzeigen"
    echo -e "   ${BLUE}docker-compose stop${NC}           - Container stoppen"
    echo -e "   ${BLUE}docker-compose restart${NC}        - Container neu starten"
    echo -e "   ${BLUE}docker-compose down${NC}           - Container entfernen"
else
    echo -e "${BLUE}🚀 Remote Deployment zu ${REMOTE_HOST}${NC}\n"
    
    echo -e "${BLUE}📦 Synchronisiere Dateien mit rsync...${NC}"
    rsync -avz --progress \
        --exclude='database/' \
        --exclude='media/' \
        --exclude='import/' \
        --exclude='__pycache__/' \
        --exclude='*.pyc' \
        --exclude='*.log' \
        --exclude='.git/' \
        --exclude='.vscode/' \
        --exclude='backup_*/' \
        --exclude='export_*/' \
        --exclude='test_*.py' \
        --exclude='venv/' \
        --exclude='.env' \
        ./ ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/

    echo -e "\n${GREEN}✅ Dateien synchronisiert${NC}"
    
    echo -e "\n${BLUE}🔄 Starte Container neu (down + up --build)...${NC}"
    ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && docker compose down && docker compose up -d --build"
    
    echo -e "\n${GREEN}✅ Deployment abgeschlossen!${NC}"
    echo -e "\n📍 FakeDaily läuft auf: http://${REMOTE_HOST}.krakhofer.org:5001"
fi
