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
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Kopiere requirements zuerst (für besseres Caching)
COPY requirements.txt .
COPY requirements-dev.txt .

# Optional: install dev/test tools only when building with
# --build-arg INSTALL_DEV=true. Default is false to keep
# production images minimal and free of test tooling.
ARG INSTALL_DEV=false

# Install production dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install development/test dependencies only when requested
RUN if [ "$INSTALL_DEV" = "true" ] ; then \
            pip install --no-cache-dir -r requirements-dev.txt ; \
        else \
            echo "Skipping dev dependencies" ; \
        fi

# Kopiere Anwendungscode
COPY src/ src/
COPY web/ web/
COPY start_web.py .
COPY explain_tags.py .

# Erstelle notwendige Verzeichnisse
RUN mkdir -p database media/images logs

# Exponiere Port
EXPOSE 5001

# Setze Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Starte Flask-App (DB wird automatisch beim ersten Start von app.py initialisiert)
CMD ["python", "start_web.py"]
