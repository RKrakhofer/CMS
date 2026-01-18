"""
Flask Web Interface für FakeDaily
"""
import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime

# Pfad zum src-Ordner hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import markdown

from db_manager import DatabaseManager
from image_processor import ImageProcessor
from whatsapp_formatter import WhatsAppFormatter

# ===== Logging Setup =====
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Security Logger für sicherheitsrelevante Events
security_logger = logging.getLogger('fakedaily.security')
security_logger.setLevel(logging.INFO)

# Timed Rotating File Handler für Security-Log (DSGVO: 30 Tage Aufbewahrung)
security_handler = TimedRotatingFileHandler(
    LOG_DIR / 'security.log',
    when='midnight',      # Rotation um Mitternacht
    interval=1,           # Täglich
    backupCount=30,       # 30 Tage Aufbewahrung (DSGVO-konform)
    encoding='utf-8'
)
security_handler.setLevel(logging.INFO)
security_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(remote_addr)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
security_handler.setFormatter(security_formatter)
security_logger.addHandler(security_handler)

# App Logger für allgemeine Events
app_logger = logging.getLogger('fakedaily.app')
app_logger.setLevel(logging.INFO)

# Timed Rotating File Handler für App-Log (DSGVO: 30 Tage Aufbewahrung)
app_handler = TimedRotatingFileHandler(
    LOG_DIR / 'app.log',
    when='midnight',      # Rotation um Mitternacht
    interval=1,           # Täglich
    backupCount=30,       # 30 Tage Aufbewahrung (DSGVO-konform)
    encoding='utf-8'
)
app_handler.setLevel(logging.INFO)
app_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
app_handler.setFormatter(app_formatter)
app_logger.addHandler(app_handler)

# Console Handler für Development
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(app_formatter)
app_logger.addHandler(console_handler)

def anonymize_ip(ip_address):
    """Anonymisiert IP-Adresse gemäß DSGVO (letztes Oktett auf 0)"""
    if not ip_address or ip_address == 'unknown':
        return 'unknown'
    try:
        parts = ip_address.split('.')
        if len(parts) == 4:  # IPv4
            parts[-1] = '0'
            return '.'.join(parts)
        elif ':' in ip_address:  # IPv6
            parts = ip_address.split(':')
            # Letzte 64 Bit anonymisieren
            return ':'.join(parts[:4]) + '::0'
        return 'anonymized'
    except:
        return 'anonymized'

def simplify_user_agent(user_agent):
    """Reduziert User-Agent auf Browser-Typ (DSGVO-konform)"""
    if not user_agent:
        return 'unknown'
    ua_lower = user_agent.lower()
    if 'firefox' in ua_lower:
        return 'Firefox'
    elif 'chrome' in ua_lower and 'edg' not in ua_lower:
        return 'Chrome'
    elif 'edg' in ua_lower:
        return 'Edge'
    elif 'safari' in ua_lower and 'chrome' not in ua_lower:
        return 'Safari'
    elif 'opera' in ua_lower or 'opr' in ua_lower:
        return 'Opera'
    elif 'bot' in ua_lower or 'crawler' in ua_lower:
        return 'Bot'
    return 'Other'

def log_security_event(message, level=logging.INFO, user_agent=None):
    """Helper für DSGVO-konforme Security-Logs mit anonymisierter IP und vereinfachtem User-Agent"""
    anonymized_ip = anonymize_ip(request.remote_addr if request else None)
    extra = {
        'remote_addr': anonymized_ip
    }
    msg = message
    if user_agent:
        simplified_ua = simplify_user_agent(user_agent)
        msg += f" - Browser: {simplified_ua}"
    security_logger.log(level, msg, extra=extra)

# App-Prefix für Sub-Path-Deployment (z.B. /fakedaily)
APP_PREFIX = os.environ.get('APP_PREFIX', '').rstrip('/')

# Site-Konfiguration
SITE_TITLE = os.environ.get('SITE_TITLE', 'FakeDaily')
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5001')  # Für externe Links (z.B. in JSON-Export)

# Flask-App initialisieren mit korrektem static_url_path
app = Flask(__name__, static_url_path=f'{APP_PREFIX}/static' if APP_PREFIX else '/static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Proxy-Unterstützung für X-Forwarded-* Headers
app.wsgi_app = ProxyFix(
    app.wsgi_app, 
    x_for=1,      # X-Forwarded-For
    x_proto=1,    # X-Forwarded-Proto
    x_host=1,     # X-Forwarded-Host
    x_prefix=1    # X-Forwarded-Prefix
)

# APPLICATION_ROOT setzen wenn Prefix vorhanden
if APP_PREFIX:
    app.config['APPLICATION_ROOT'] = APP_PREFIX

# Konfiguration
UPLOAD_FOLDER = BASE_DIR / 'media' / 'images'
LOGO_PATH = BASE_DIR / 'logo.png'  # Optional
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Database Manager initialisieren
db = DatabaseManager()

# Markdown-Konverter
md = markdown.Markdown(extensions=['fenced_code', 'tables', 'nl2br'])

# Context Processor für globale Template-Variablen
@app.context_processor
def inject_globals():
    return {
        'SITE_TITLE': SITE_TITLE,
        'APP_PREFIX': APP_PREFIX
    }

def allowed_file(filename):
    """Prüft ob Datei-Extension erlaubt ist"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ===== Routes =====

# Root zeigt Reader (Public)
@app.route(f'{APP_PREFIX}/')
def root():
    """Root-Route -> Reader-Startseite"""
    return redirect(url_for('reader_index'))

# ===== Admin Routes =====

@app.route(f'{APP_PREFIX}/admin')
@app.route(f'{APP_PREFIX}/admin/')
def index():
    """Startseite - Artikel-Liste"""
    published_only = request.args.get('published', 'all')
    search_query = request.args.get('q', '')
    sort_by = request.args.get('sort', 'id')
    sort_order = request.args.get('order', 'desc')
    
    if search_query:
        articles = db.search_articles(search_query)
    elif published_only == 'yes':
        articles = db.get_all_articles(published_only=True)
    else:
        articles = db.get_all_articles()
    
    # Sortierung anwenden
    def get_sort_key(article):
        if sort_by == 'id':
            return article.get('id', 0)
        elif sort_by == 'status':
            return article.get('published', False)
        elif sort_by == 'title':
            return article.get('title', '').lower()
        elif sort_by == 'tags':
            tags = article.get('tags', [])
            return len(tags) if tags else 0
        elif sort_by == 'date':
            return article.get('created_at', '')
        return 0
    
    reverse = (sort_order == 'desc')
    articles = sorted(articles, key=get_sort_key, reverse=reverse)
    
    # Markdown zu HTML für Excerpts konvertieren
    for article in articles:
        excerpt_text = article['content'][:200]
        md.reset()
        article['excerpt_html'] = md.convert(excerpt_text)
    
    return render_template('index.html', 
                         articles=articles, 
                         search_query=search_query,
                         sort_by=sort_by,
                         sort_order=sort_order)


@app.route(f'{APP_PREFIX}/admin/article/<int:article_id>')
def view_article(article_id):
    """Artikel ansehen"""
    article = db.get_article(article_id)
    if not article:
        flash('Artikel nicht gefunden', 'error')
        return redirect(url_for('index'))
    
    # Markdown zu HTML konvertieren
    md.reset()
    article['content_html'] = md.convert(article['content'])
    
    # Bilder laden
    images = db.get_images_for_article(article_id)
    
    return render_template('view_article.html', article=article, images=images)


@app.route(f'{APP_PREFIX}/admin/article/new', methods=['GET', 'POST'])
def new_article():
    """Neuen Artikel erstellen"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        author = request.form.get('author')
        published = request.form.get('published') == 'on'
        tags_str = request.form.get('tags', '')
        tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        
        if not title or not content:
            flash('Titel und Inhalt sind erforderlich', 'error')
            return render_template('edit_article.html', article=None)
        
        # Artikel erstellen
        article_id = db.add_article(
            title=title,
            content=content,
            author=author,
            published=published,
            tags=tags
        )
        
        # Security Log
        log_security_event(
            f"Article created: ID={article_id}, Title='{title}', Published={published}",
            user_agent=request.headers.get('User-Agent', 'unknown')
        )
        
        # Bilder hochladen
        uploaded_images = []
        if 'images' in request.files:
            uploaded_images = upload_images(article_id, request.files.getlist('images'))
        
        if uploaded_images:
            flash(f'Artikel erstellt! {len(uploaded_images)} Bild(er) hochgeladen.', 'success')
        else:
            flash('Artikel erfolgreich erstellt!', 'success')
        return redirect(url_for('edit_article', article_id=article_id))
    
    return render_template('edit_article.html', article=None)


@app.route(f'{APP_PREFIX}/admin/article/<int:article_id>/edit', methods=['GET', 'POST'])
def edit_article(article_id):
    """Artikel bearbeiten"""
    article = db.get_article(article_id)
    if not article:
        flash('Artikel nicht gefunden', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        author = request.form.get('author')
        published = request.form.get('published') == 'on'
        tags_str = request.form.get('tags', '')
        tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        created_at = request.form.get('created_at')
        
        if not title or not content:
            flash('Titel und Inhalt sind erforderlich', 'error')
            return render_template('edit_article.html', article=article)
        
        # Artikel aktualisieren
        db.update_article(
            article_id,
            title=title,
            content=content,
            author=author,
            published=published,
            tags=tags,
            created_at=created_at
        )
        
        # Security Log
        log_security_event(
            f"Article updated: ID={article_id}, Title='{title}', Published={published}",
            user_agent=request.headers.get('User-Agent', 'unknown')
        )
        
        # Neue Bilder hochladen
        uploaded_images = []
        if 'images' in request.files:
            uploaded_images = upload_images(article_id, request.files.getlist('images'))
        
        if uploaded_images:
            flash(f'Artikel aktualisiert! {len(uploaded_images)} Bild(er) hochgeladen.', 'success')
        else:
            flash('Artikel erfolgreich aktualisiert!', 'success')
        return redirect(url_for('edit_article', article_id=article_id))
    
    # Tags als String
    article['tags_str'] = ', '.join(article.get('tags', []) or [])
    
    # created_at für datetime-local Input formatieren
    if article.get('created_at'):
        from datetime import datetime
        try:
            # SQLite format: '2024-01-17 10:30:45' -> HTML5 format: '2024-01-17T10:30'
            dt = datetime.strptime(article['created_at'], '%Y-%m-%d %H:%M:%S')
            article['created_at_input'] = dt.strftime('%Y-%m-%dT%H:%M')
        except:
            article['created_at_input'] = ''
    else:
        # Falls kein Timestamp vorhanden, aktuellen Zeitpunkt verwenden
        from datetime import datetime
        article['created_at_input'] = datetime.now().strftime('%Y-%m-%dT%H:%M')
    
    images = db.get_images_for_article(article_id)
    
    return render_template('edit_article.html', article=article, images=images)


@app.route(f'{APP_PREFIX}/admin/article/<int:article_id>/delete', methods=['POST'])
def delete_article(article_id):
    """Artikel löschen"""
    # Bilder löschen
    images = db.get_images_for_article(article_id)
    for img in images:
        img_path = BASE_DIR / img['filepath']
        if img_path.exists():
            img_path.unlink()
    
    # Artikel löschen
    if db.delete_article(article_id):
        log_security_event(
            f"Article deleted: ID={article_id}",
            level=logging.WARNING,
            user_agent=request.headers.get('User-Agent', 'unknown')
        )
        flash('Artikel gelöscht', 'success')
    else:
        log_security_event(
            f"Failed to delete article: ID={article_id}",
            level=logging.ERROR,
            user_agent=request.headers.get('User-Agent', 'unknown')
        )
        flash('Fehler beim Löschen', 'error')
    
    return redirect(url_for('index'))


@app.route(f'{APP_PREFIX}/admin/image/<int:image_id>/delete', methods=['POST'])
def delete_image(image_id):
    """Bild löschen"""
    # Bild-Info holen
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filepath FROM images WHERE id = ?", (image_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        # Datei löschen
        img_path = BASE_DIR / result['filepath']
        if img_path.exists():
            img_path.unlink()
        
        # Aus DB löschen
        if db.delete_image(image_id):
            log_security_event(
                f"Image deleted: ID={image_id}, File={result['filepath']}",
                level=logging.WARNING,
                user_agent=request.headers.get('User-Agent', 'unknown')
            )
            flash('Bild gelöscht', 'success')
        else:
            flash('Fehler beim Löschen aus DB', 'error')
    else:
        flash('Bild nicht gefunden', 'error')
    
    return redirect(request.referrer or url_for('index'))


@app.route(f'{APP_PREFIX}/media/images/<path:filename>')
def serve_image(filename):
    """Bilder ausliefern"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ===== API Routes =====

@app.route(f'{APP_PREFIX}/admin/api/upload/images/<int:article_id>', methods=['POST'])
def api_upload_images(article_id):
    """
    API-Endpoint zum Hochladen von Bildern für einen Artikel
    
    Usage:
        curl -X POST "http://localhost:5001/admin/api/upload/images/1" \
          -F "images=@/path/to/image1.jpg" \
          -F "images=@/path/to/image2.png" \
          -F "add_watermark=true"
    
    Form-Data:
        - images: file(s) - Eine oder mehrere Bilddateien (PNG, JPG, JPEG, GIF, WebP)
        - add_watermark: string (optional) - "true"/"1"/"yes"/"on" für Logo-Wasserzeichen
    
    Returns:
        JSON response with uploaded images list and errors
    """
    # Prüfen ob Artikel existiert
    article = db.get_article(article_id)
    if not article:
        return jsonify({
            'success': False,
            'error': 'Artikel nicht gefunden'
        }), 404
    
    # Prüfen ob Dateien vorhanden
    if 'images' not in request.files:
        return jsonify({
            'success': False,
            'error': 'Keine Dateien hochgeladen'
        }), 400
    
    files = request.files.getlist('images')
    
    if not files or all(f.filename == '' for f in files):
        return jsonify({
            'success': False,
            'error': 'Keine Dateien ausgewählt'
        }), 400
    
    # Wasserzeichen-Option (optional, default: false)
    add_watermark = request.form.get('add_watermark', 'false').lower() in ['true', '1', 'yes', 'on']
    
    # ImageProcessor initialisieren wenn Logo vorhanden und gewünscht
    img_processor = None
    if add_watermark and LOGO_PATH.exists():
        img_processor = ImageProcessor(logo_path=str(LOGO_PATH))
    
    uploaded = []
    errors = []
    
    for file in files:
        if file and file.filename:
            if not allowed_file(file.filename):
                errors.append(f"Ungültige Dateiendung: {file.filename}")
                continue
            
            try:
                filename = secure_filename(file.filename)
                
                # Eindeutiger Dateiname
                new_filename = f"{article_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                filepath = app.config['UPLOAD_FOLDER'] / new_filename
                
                # Datei speichern
                file.save(filepath)
                
                # Wasserzeichen hinzufügen
                if img_processor:
                    try:
                        img_processor.add_watermark(
                            image_path=str(filepath),
                            output_path=str(filepath),
                            position="bottom-right",
                            logo_size_ratio=0.15,
                            margin=20
                        )
                    except Exception as e:
                        errors.append(f"Logo-Fehler für {filename}: {str(e)}")
                
                # In DB eintragen
                relative_path = f"media/images/{new_filename}"
                db.add_image(
                    article_id=article_id,
                    filename=new_filename,
                    filepath=relative_path
                )
                
                # Security Log
                log_security_event(
                    f"Image uploaded via API: ArticleID={article_id}, File={new_filename}, Watermark={bool(img_processor)}",
                    user_agent=request.headers.get('User-Agent', 'unknown')
                )
                
                uploaded.append({
                    'filename': new_filename,
                    'original_filename': filename,
                    'url': url_for('serve_image', filename=new_filename, _external=True)
                })
                
            except Exception as e:
                errors.append(f"Fehler bei {file.filename}: {str(e)}")
    
    # Response erstellen
    response = {
        'success': len(uploaded) > 0,
        'uploaded': len(uploaded),
        'errors': errors,
        'images': uploaded
    }
    
    status_code = 200 if len(uploaded) > 0 else 400
    
    return jsonify(response), status_code


@app.route(f'{APP_PREFIX}/admin/article/<int:article_id>/whatsapp')
def whatsapp_export(article_id):
    """Artikel für WhatsApp exportieren"""
    article = db.get_article(article_id)
    if not article:
        flash('Artikel nicht gefunden', 'error')
        return redirect(url_for('index'))
    
    # WhatsApp-formatierter Text
    whatsapp_text = WhatsAppFormatter.format_article(
        title=article['title'],
        content=article['content'],
        author=article.get('author')
    )
    
    # Bilder laden
    images = db.get_images_for_article(article_id)
    
    return render_template('whatsapp_export.html', 
                          article=article, 
                          whatsapp_text=whatsapp_text,
                          images=images)


def upload_images(article_id, files):
    """Hilfsfunktion zum Hochladen von Bildern"""
    add_watermark = request.form.get('add_watermark') == 'on'
    uploaded = []
    
    # ImageProcessor initialisieren wenn Logo vorhanden
    img_processor = None
    if add_watermark and LOGO_PATH.exists():
        img_processor = ImageProcessor(logo_path=str(LOGO_PATH))
    
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Eindeutiger Dateiname
            new_filename = f"{article_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            filepath = app.config['UPLOAD_FOLDER'] / new_filename
            
            # Datei speichern
            file.save(filepath)
            
            # Wasserzeichen hinzufügen
            if img_processor:
                try:
                    img_processor.add_watermark(
                        image_path=str(filepath),
                        output_path=str(filepath),
                        position="bottom-right",
                        logo_size_ratio=0.15,
                        margin=20
                    )
                except Exception as e:
                    flash(f'Warnung: Logo konnte nicht hinzugefügt werden: {e}', 'warning')
            
            # In DB eintragen
            relative_path = f"media/images/{new_filename}"
            db.add_image(
                article_id=article_id,
                filename=new_filename,
                filepath=relative_path
            )
            
            # Security Log
            log_security_event(
                f"Image uploaded: ArticleID={article_id}, File={new_filename}, Watermark={bool(img_processor)}",
                user_agent=request.headers.get('User-Agent', 'unknown')
            )
            
            uploaded.append(new_filename)
    
    return uploaded


# ===== API Endpoints (Admin) =====

@app.route(f'{APP_PREFIX}/admin/api/export/articles')
def export_articles_json():
    """Exportiert alle Artikel als JSON"""
    log_security_event(
        f"API: Export articles requested - Count will be determined",
        user_agent=request.headers.get('User-Agent', 'unknown')
    )
    
    articles = db.get_all_articles()
    
    # Bilder für jeden Artikel laden
    for article in articles:
        images = db.get_images_for_article(article['id'])
        article['images'] = [
            {
                'id': img['id'],
                'filename': img['filename'],
                'alt_text': img.get('alt_text'),
                'caption': img.get('caption'),
                'url': url_for('serve_image', filename=img['filename'], _external=True)
            }
            for img in images
        ]
    
    return jsonify({
        'success': True,
        'count': len(articles),
        'articles': articles
    })


@app.route(f'{APP_PREFIX}/admin/api/import/articles', methods=['POST'])
def import_articles_json():
    """Importiert Artikel aus JSON
    
    Importiert einen Artikel nur wenn:
    - Der Titel noch nicht in der DB ist, ODER
    - Der Titel existiert, aber updated_at im Import neuer ist
    """
    if not request.json:
        return jsonify({'success': False, 'error': 'Kein JSON-Body'}), 400
    
    data = request.json
    articles_to_import = data.get('articles', [])
    
    if not articles_to_import:
        return jsonify({'success': False, 'error': 'Keine Artikel zum Importieren'}), 400
    
    imported = 0
    updated = 0
    skipped = 0
    errors = []
    
    for article_data in articles_to_import:
        try:
            title = article_data.get('title')
            if not title:
                errors.append('Artikel ohne Titel übersprungen')
                skipped += 1
                continue
            
            # Prüfen ob Artikel mit diesem Titel bereits existiert
            existing = db.get_article_by_title(title)
            
            if existing:
                # Timestamps vergleichen
                import_updated = article_data.get('updated_at', article_data.get('created_at'))
                existing_updated = existing.get('updated_at', existing.get('created_at'))
                
                if import_updated and existing_updated:
                    # Vergleiche Timestamps
                    import_dt = datetime.fromisoformat(import_updated)
                    existing_dt = datetime.fromisoformat(existing_updated)
                    
                    if import_dt > existing_dt:
                        # Import ist neuer - aktualisieren
                        db.update_article(
                            existing['id'],
                            title=article_data.get('title'),
                            content=article_data.get('content'),
                            author=article_data.get('author'),
                            published=article_data.get('published', False),
                            tags=article_data.get('tags')
                        )
                        updated += 1
                    else:
                        # Existing ist neuer oder gleich - überspringen
                        skipped += 1
                else:
                    # Kein Timestamp-Vergleich möglich - überspringen
                    skipped += 1
            else:
                # Neuer Artikel - hinzufügen
                db.add_article(
                    title=article_data.get('title'),
                    content=article_data.get('content', ''),
                    author=article_data.get('author'),
                    published=article_data.get('published', False),
                    tags=article_data.get('tags'),
                    created_at=article_data.get('created_at')
                )
                imported += 1
                
        except Exception as e:
            errors.append(f"Fehler bei '{article_data.get('title', 'unbekannt')}': {str(e)}")
            skipped += 1
    
    # Security Log
    log_security_event(
        f"API: Import completed - Imported={imported}, Updated={updated}, Skipped={skipped}, Errors={len(errors)}",
        level=logging.WARNING if errors else logging.INFO,
        user_agent=request.headers.get('User-Agent', 'unknown')
    )
    
    return jsonify({
        'success': True,
        'imported': imported,
        'updated': updated,
        'skipped': skipped,
        'errors': errors
    })


# ===== Template Filters =====

@app.template_filter('datetime')
def format_datetime(value):
    """Formatiert Datetime-String"""
    if not value:
        return ''
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime('%d.%m.%Y %H:%M')
    except:
        return value


# ===== Reader Routes (Public) =====

@app.route(f'{APP_PREFIX}/public/')
@app.route(f'{APP_PREFIX}/reader/')
def reader_index():
    """Reader-Interface - Nur veröffentlichte Artikel"""
    search_query = request.args.get('q', '')
    
    if search_query:
        # Suche, aber nur in veröffentlichten
        all_results = db.search_articles(search_query)
        articles = [a for a in all_results if a.get('published')]
    else:
        articles = db.get_all_articles(published_only=True)
    
    # Markdown zu HTML für Excerpts konvertieren
    for article in articles:
        # Nur ersten Teil konvertieren für Performance
        excerpt_text = article['content'][:300]
        article['excerpt_html'] = md.convert(excerpt_text)
        # Markdown-Renderer zurücksetzen für nächsten Artikel
        md.reset()
    
    return render_template('reader_index.html', articles=articles)


@app.route(f'{APP_PREFIX}/public/tag/<tag>')
@app.route(f'{APP_PREFIX}/reader/tag/<tag>')
def reader_tag(tag):
    """Reader-Interface - Artikel nach Tag gefiltert"""
    # Nur veröffentlichte Artikel mit diesem Tag
    articles = db.get_articles_by_tag(tag, published_only=True)
    
    # Markdown zu HTML für Excerpts konvertieren
    for article in articles:
        excerpt_text = article['content'][:300]
        article['excerpt_html'] = md.convert(excerpt_text)
        md.reset()
    
    return render_template('reader_index.html', articles=articles, current_tag=tag)


@app.route(f'{APP_PREFIX}/public/article/<int:article_id>')
@app.route(f'{APP_PREFIX}/reader/article/<int:article_id>')
def reader_article(article_id):
    """Reader-Interface - Einzelner Artikel"""
    article = db.get_article(article_id)
    
    # Nur veröffentlichte Artikel anzeigen
    if not article or not article.get('published'):
        flash('Artikel nicht gefunden oder nicht veröffentlicht', 'error')
        return redirect(url_for('reader_index'))
    
    # Markdown zu HTML konvertieren
    md.reset()
    article['content_html'] = md.convert(article['content'])
    
    # Bilder laden
    images = db.get_images_for_article(article_id)
    
    return render_template('reader_article.html', article=article, images=images)


if __name__ == '__main__':
    # Sicherstellen dass Upload-Ordner existiert
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # Log App Start
    app_logger.info(f"FakeDaily starting - APP_PREFIX={APP_PREFIX}, SITE_TITLE={SITE_TITLE}")
    
    # Server starten
    app.run(debug=True, host='0.0.0.0', port=5000)
