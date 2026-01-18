# Multi-stage build für optimale Image-Größe
FROM python:3.12-slim

# Setze Arbeitsverzeichnis
WORKDIR /app

# Installiere System-Abhängigkeiten für Pillow und CLI-Tools
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    fonts-liberation \
    bash \
    sqlite3 \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Kopiere requirements zuerst (für besseres Caching)
COPY requirements.txt .

# Installiere Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere Anwendungscode
COPY src/ src/
COPY web/ web/
COPY scripts/ scripts/
COPY start_web.py .

# Erstelle notwendige Verzeichnisse
RUN mkdir -p database media/images

# Exponiere Port
EXPOSE 5001

# Setze Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Initialisiere Datenbank beim Start und starte dann Flask-App
CMD python scripts/init_db.py && python start_web.py
