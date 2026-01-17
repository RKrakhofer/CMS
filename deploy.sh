#!/bin/bash

# CMS Docker Build & Deploy Script

set -e

echo "======================================"
echo "🐳 FakeDaily Docker Build"
echo "======================================"

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Image Name
IMAGE_NAME="fakedaily"
VERSION=$(date +%Y%m%d-%H%M%S)

echo -e "\n${BLUE}📦 Building Docker Image...${NC}"
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
