#!/usr/bin/env python3
"""
Startet den CMS Web-Server
"""
import sys
from pathlib import Path

# Pfad zum web-Ordner hinzufügen
web_dir = Path(__file__).parent / "web"
sys.path.insert(0, str(web_dir))

from app import app

if __name__ == '__main__':
    import os
    
    # Port aus Umgebungsvariable oder default 5001
    port = int(os.environ.get('PORT', 5001))
    # Host aus Umgebungsvariable oder 0.0.0.0 für Docker
    host = os.environ.get('HOST', '0.0.0.0')
    # Debug-Mode aus Umgebungsvariable
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    print("=" * 60)
    print("🚀 CMS Web Interface")
    print("=" * 60)
    print(f"\n📍 Server läuft auf: http://localhost:{port}")
    print("\n💡 Tipps:")
    print("  - Datenbank wird automatisch beim Start initialisiert")
    print("  - Logo hinzufügen: logo.png im Projektordner")
    print("  - Strg+C zum Beenden\n")
    
    app.run(debug=debug, host=host, port=port)
