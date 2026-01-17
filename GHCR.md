# CMS - GitHub Container Registry

## 📦 Docker Image

Das CMS Docker Image wird automatisch zu GitHub Container Registry (GHCR) gepusht.

### Pull Image

```bash
docker pull ghcr.io/DEIN-USERNAME/cms:latest
```

### Verfügbare Tags

- `latest` - Neuester Build vom main Branch
- `v1.0.0` - Spezifische Version (Semantic Versioning)
- `main-sha-abc123` - Build von spezifischem Commit

### Verwendung

```bash
# Mit docker run
docker run -p 5001:5001 \
  -v ./database:/app/database \
  -v ./media:/app/media \
  -v ./logo.png:/app/logo.png:ro \
  ghcr.io/DEIN-USERNAME/cms:latest

# Mit docker-compose (docker-compose.yml anpassen)
services:
  cms-app:
    image: ghcr.io/DEIN-USERNAME/cms:latest
    # ... rest der Config
```

### Build-Prozess

Der Build-Workflow wird automatisch ausgelöst bei:
- **Push zu `main`** - Erstellt Image mit Tag `latest`
- **Tag `v*`** - Erstellt versioniertes Image (z.B. `v1.0.0`)
- **Pull Request** - Baut Image zur Validierung (kein Push)
- **Manual Trigger** - Über GitHub Actions UI

### Multi-Architektur Support

Das Image wird für folgende Architekturen gebaut:
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64/v8)

Funktioniert auf:
- ✅ Standard x86 Server
- ✅ Raspberry Pi 4/5
- ✅ Apple Silicon (M1/M2/M3)
- ✅ ARM-basierte Cloud-Instanzen

### Artifact Attestation

Jedes Image enthält eine Build-Provenance-Attestierung für:
- Supply Chain Security
- Verifizierbare Build-Prozesse
- SLSA Compliance

## 🚀 Release erstellen

```bash
# Tag erstellen
git tag v1.0.0
git push origin v1.0.0

# Automatischer Build startet
# Image verfügbar als:
# - ghcr.io/DEIN-USERNAME/fakedaily:v1.0.0
# - ghcr.io/DEIN-USERNAME/fakedaily:1.0
# - ghcr.io/DEIN-USERNAME/fakedaily:1
```

## 🔒 Permissions

Das Image ist standardmäßig öffentlich. Um es privat zu machen:
1. Gehe zu Package Settings auf GitHub
2. Change package visibility → Private
