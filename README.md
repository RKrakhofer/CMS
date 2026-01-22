# CMS - Article & Image Database

SQLite-based Content Management System for managing articles (Markdown) and images with Flask web interface.

## 🚀 Quick Start

### Option 1: Docker (recommended)

```bash
# Build and start
./deploy.sh

# Or manually:
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**URLs:**
- **Reader (Public):** http://localhost:5001/reader/
- **Admin:** http://localhost:5001/admin/

### Option 2: Local (Development)

### 1. Virtual Environment & Dependencies
```bash
# Create virtual environment
python3 -m venv .venv

# Activate
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install packages
pip install -r requirements.txt
```

### 2. Initialize database
```bash
python scripts/init_db.py
```

### 3. Start web interface
```bash
python start_web.py
```

**URLs:**
- **Reader (Public):** http://localhost:5000/reader/
- **Admin:** http://localhost:5000/admin/

## 🌐 Web Interface Features

- ✅ **Article Overview** - All articles at a glance
- ✅ **Create/Edit Articles** - With Markdown editor
- ✅ **Markdown Rendering** - Automatic conversion in all views
- ✅ **Reader View** - Public article view without admin interface
- ✅ **Tag Filtering** - Clickable tags to filter articles by topics
- ✅ **Image Upload** - Drag & drop support
- ✅ **Watermark** - Automatic logo on images
- ✅ **Search** - Full-text search over title and content
- ✅ **Filter** - By publication status
- ✅ **Tags** - Categorization and filtering
- ✅ **WhatsApp Export** - Articles as WhatsApp-formatted texts
- ✅ **JSON API** - Export and import of articles
- ✅ **Responsive Design** - Mobile-friendly
- ✅ **Proxy Support** - Works behind reverse proxies with APP_PREFIX
- ✅ **Configurable** - Site title, base URL and prefix via environment variables

## ⚙️ Configuration

CMS can be configured via environment variables:

### Available Options

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_PREFIX` | Sub-path for deployment (e.g. `/cms`) | `` (empty) |
| `SITE_TITLE` | Website name (appears in logo, title, footer) | `CMS` |
| `BASE_URL` | Base URL for external links | `http://localhost:5001` |
| `SECRET_KEY` | Flask secret key for sessions | `dev-secret-key-change-in-production` |

### Example docker-compose.yml

```yaml
environment:
  - APP_PREFIX=/cms
  - SITE_TITLE=My News
  - BASE_URL=https://news.example.com
  - SECRET_KEY=your-secret-key-here
```

### Example direct start

```bash
APP_PREFIX=/news SITE_TITLE="Tech News" python start_web.py
```

## 📁 Structure

```
CMS/
├── database/
│   └── articles.db         # SQLite database
├── media/
│   └── images/            # Stored images
├── scripts/
│   ├── init_db.py         # Initialize DB
│   ├── import_article.py  # Single article
│   └── batch_import.py    # Bulk import
└── src/
    └── db_manager.py      # Database manager
```

## 💾 Database Schema

### Table: articles
- `id` - Primary key
- `title` - Article title
- `content` - Markdown content
- `author` - Author
- `created_at` - Creation date
- `updated_at` - Update date
- `published` - Published (0/1)
- `tags` - JSON array of tags

### Table: images
- `id` - Primary key
- `article_id` - Reference to articles
- `filename` - Filename
- `filepath` - Relative path
- `alt_text` - Alt text
- `caption` - Caption
- `uploaded_at` - Upload date

## 🔧 Usage

### Security Logging

All security-relevant events are automatically logged:

**Log Files:**
- `logs/security.log` - Admin actions, uploads, API calls
- `logs/app.log` - General application events

**Log Rotation:**
- `security.log` - Max 10MB, rotates to 5 backup files (security.log.1 to .5)
- `app.log` - Max 5MB, rotates to 3 backup files (app.log.1 to .3)
- Oldest logs are automatically deleted

**Logged Events:**
- ✅ Article create/update/delete (with IP, User-Agent)
- ✅ Image uploads and deletions
- ✅ API export/import requests
- ✅ Errors and warnings

**Example Log Entry:**
```
2026-01-16 20:15:32 - cms.security - INFO - [192.168.1.100] Article created: ID=42, Title='Breaking News', Published=True - UA: Mozilla/5.0...
2026-01-16 20:16:05 - cms.security - WARNING - [192.168.1.100] Article deleted: ID=41
2026-01-16 20:17:22 - cms.security - INFO - [10.0.0.5] Image uploaded: ArticleID=42, File=42_20260116_201722_photo.jpg, Watermark=True
```

### Python API

```python
from src.db_manager import DatabaseManager

db = DatabaseManager()

# Create article
article_id = db.add_article(
    title="My Article",
    content="# Headline\n\nText...",
    author="John Doe",
    published=True,
    tags=["news", "important"]
)

# Get article
article = db.get_article(article_id)
all_articles = db.get_all_articles()

# Update article
db.update_article(article_id, title="New Title", published=True)

# Add image
db.add_image(
    article_id=article_id,
    filename="image.jpg",
    filepath="media/images/image.jpg",
    alt_text="Description"
)

# Search
results = db.search_articles("search term")
```

### REST API

#### Export Articles

```bash
# Export all articles as JSON
curl http://localhost:5001/admin/api/export/articles

# Formatted with jq
curl http://localhost:5001/admin/api/export/articles | jq
```

**Response:**
```json
{
  "success": true,
  "count": 10,
  "articles": [
    {
      "id": 1,
      "title": "Article Title",
      "content": "# Markdown\n\nContent...",
      "author": "Author",
      "created_at": "2026-01-16T10:00:00",
      "updated_at": "2026-01-16T12:00:00",
      "published": 1,
      "tags": ["tag1", "tag2"],
      "images": [
        {
          "id": 1,
          "filename": "image.jpg",
          "alt_text": "Description",
          "caption": "Caption",
          "url": "http://localhost:5001/images/image.jpg"
        }
      ]
    }
  ]
}
```

#### Import Articles

```bash
# Import articles from JSON
curl -X POST http://localhost:5001/admin/api/import/articles \
  -H "Content-Type: application/json" \
  -d '{
    "articles": [
      {
        "title": "New Article",
        "content": "# Markdown\n\nContent...",
        "author": "Author",
        "published": true,
        "tags": ["tag1", "tag2"],
        "created_at": "2026-01-16T10:00:00",
        "updated_at": "2026-01-16T12:00:00"
      }
    ]
  }'
```

**Import Logic:**
- Article is **newly created** if the title doesn't exist yet
- Article is **updated** if the title exists AND `updated_at` in import is newer
- Article is **skipped** if a newer/same version already exists

**Response:**
```json
{
  "success": true,
  "imported": 5,   // Newly added articles
  "updated": 2,    // Updated articles
  "skipped": 3,    // Skipped articles
  "errors": []     // Any errors
}
```

### Upload Images (API)

**Endpoint:** `POST /admin/api/upload/images/<article_id>`

**Example:**
```bash
# Upload single image
curl -X POST "http://localhost:5001/admin/api/upload/images/1" \
  -F "images=@/path/to/image1.jpg"

# Upload multiple images simultaneously
curl -X POST "http://localhost:5001/admin/api/upload/images/1" \
  -F "images=@/path/to/image1.jpg" \
  -F "images=@/path/to/image2.png"

# With watermark (logo)
curl -X POST "http://localhost:5001/admin/api/upload/images/1" \
  -F "images=@/path/to/image1.jpg" \
  -F "add_watermark=true"
```

**Response:**
```json
{
  "success": true,
  "uploaded": 2,
  "errors": [],
  "images": [
    {
      "filename": "1_20260117_123456_image1.jpg",
      "original_filename": "image1.jpg",
      "url": "http://localhost:5001/media/images/1_20260117_123456_image1.jpg"
    }
  ]
}
```

**Notes:**
- Allowed file types: PNG, JPG, JPEG, GIF, WebP
- Maximum file size: 16MB per image
- Images are automatically renamed: `<article_id>_<timestamp>_<filename>`
- Optional: `add_watermark=true` adds logo (requires logo.png in project directory)

### Public Reader Interface

```
http://localhost:5001/                  # Redirect to /reader/
http://localhost:5001/reader/           # All published articles
http://localhost:5001/reader/article/1  # Single article
http://localhost:5001/reader/tag/Politics # Articles filtered by tag
http://localhost:5001/public/           # Alternative route
```

**Tag Filtering:**
- Clickable tags in reader view
- Shows only articles with selected tag
- Active tag is visually highlighted (darker + ✓)
- "Remove filter" button to reset

**Proxy-Ready:**
The `/reader/` interface is fully proxy-compatible and works with:
- X-Forwarded-For, X-Forwarded-Proto, X-Forwarded-Host, X-Forwarded-Prefix
- **APP_PREFIX environment variable** for easy sub-path deployment (e.g. `/cms`)
- Automatic URL generation via `url_for()` - works in any context

**Example - Deploy app under /cms:**
```bash
# In docker-compose.yml:
environment:
  - APP_PREFIX=/cms

# URLs are automatically:
# https://your-domain.com/cms/           -> Redirect to /reader/
# https://your-domain.com/cms/reader/    -> Public reader
# https://your-domain.com/cms/admin/     -> Admin interface
```

See example Nginx config below in "Reverse Proxy Setup" section.

### WhatsApp Export

Export article as WhatsApp-formatted text:
```
http://localhost:5001/admin/article/1/whatsapp
```

## 💾 Export & Backup

### Export with Images (Script)

The `export_with_images.sh` script exports all articles as JSON and automatically downloads associated images:

```bash
# Export from localhost
./export_with_images.sh

# Export from another server
./export_with_images.sh http://stage:5001/cms

# With custom export directory
./export_with_images.sh http://stage:5001/cms my_export
```

**What the script does:**
1. Calls `/admin/api/export/articles`
2. Saves JSON to `export_TIMESTAMP/articles.json`
3. Downloads all referenced images to `export_TIMESTAMP/images/`
4. Shows import command for another server

**Output:**
```
export_20260116_123456/
├── articles.json          # All articles with metadata
└── images/                # Downloaded images
    ├── image1.jpg
    └── image2.jpg
```

### Import with Images (Script)

The `import_with_images.sh` script imports an export directory to another server:

```bash
# Import to localhost
./import_with_images.sh export_20260116_123456

# Import to another server
./import_with_images.sh export_20260116_123456 http://production:5001/cms
```

**What the script does:**
1. Reads `articles.json` from export directory
2. Imports all articles via `/admin/api/import/articles`
3. Shows statistics (new/updated/skipped)
4. Informs about images (must be manually copied to `media/images/` directory)

**Note about images:**
The import API only imports article metadata. Images must be copied separately:
```bash
# Copy images to target system
cp export_20260116_123456/images/* /path/to/cms/media/images/

# Or via rsync to remote server
rsync -av export_20260116_123456/images/ server:/path/to/cms/media/images/
```

### Backup (Script)

Complete backup with database and images:

```bash
./backup.sh
```

Creates a compressed archive with:
- SQLite database (`articles.db`)
- All images (`images/`)
- JSON export for interoperability

## 📝 Import Formats

### JSON
```json
[
  {
    "title": "Article Title",
    "content": "# Markdown\n\nContent...",
    "author": "Author",
    "published": true,
    "tags": ["tag1", "tag2"]
  }
]
```

### CSV
```csv
title,content,author,published,tags
"Title 1","# Content","Author",true,"tag1,tag2"
```

## 🔄 Reverse Proxy Setup

CMS is fully proxy-compatible and respects all standard forwarded headers.

### Method 1: APP_PREFIX (recommended for simple setups)

Set the `APP_PREFIX` environment variable in `docker-compose.yml`:

```yaml
environment:
  - APP_PREFIX=/cms
  - SITE_TITLE=My News  # Optional: Change site title
  - BASE_URL=https://my-domain.com  # Optional: For external links
```

Or when starting directly:
```bash
APP_PREFIX=/cms SITE_TITLE="My News" python start_web.py
```

**What happens:**
- Flask automatically configures all routes under `/cms`
- Static files (CSS/JS) are served under `/cms/static/`
- `url_for()` automatically generates correct paths with prefix

Then simple Nginx config:
```nginx
location /cms/ {
    proxy_pass http://localhost:5001/cms/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Important: Allow file uploads up to 16MB
    client_max_body_size 16M;
}
```

### Method 2: X-Forwarded-Prefix (more flexible)

Without APP_PREFIX - Nginx sets the prefix:
```nginx
location /news/ {
    proxy_pass http://localhost:5001/;
    proxy_set_header X-Forwarded-Prefix /news;
    # ... other headers ...
    
    # Important: Allow file uploads up to 16MB
    client_max_body_size 16M;
}
```

### Nginx (recommended)

```nginx
# Standard setup (root path)
location / {
    proxy_pass http://localhost:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    
    # Important: Allow file uploads up to 16MB
    client_max_body_size 16M;
}

# With sub-path (e.g. /news/)
location /news/ {
    proxy_pass http://localhost:5001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Prefix /news;
    
    # Important: Allow file uploads up to 16MB
    client_max_body_size 16M;
}
```

### Apache

```apache
<Location /reader>
    ProxyPass http://localhost:5001/reader
    ProxyPassReverse http://localhost:5001/reader
    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-Prefix "/reader"
</Location>
```

### Traefik

```yaml
http:
  routers:
    cms:
      rule: "Host(`news.example.com`)"
      service: cms
      middlewares:
        - forward-headers
  
  services:
    cms:
      loadBalancer:
        servers:
          - url: "http://localhost:5001"
  
  middlewares:
    forward-headers:
      headers:
        customRequestHeaders:
          X-Forwarded-Proto: "https"
```

## 🎯 Features

- ✅ **Flask Web Interface** - Comfortable browser management
- ✅ **Reader Interface** - Public article view (`/public/` or `/reader/`)
- ✅ **Tag System** - Categorization with clickable filtering
- ✅ SQLite database (portable, no server needed)
- ✅ **Markdown Rendering** - Automatic HTML conversion with extensions
- ✅ Image management (filesystem + DB references)
- ✅ **Logo/Watermark automatically on images**
- ✅ Image processing (resize, thumbnails)
- ✅ Publication status
- ✅ **JSON API for export/import** - Synchronization between instances
- ✅ Batch import (JSON/CSV)
- ✅ **WhatsApp Export** - Formatted texts for messaging
- ✅ Full-text search (Unicode-aware)
- ✅ **Proxy Support** - APP_PREFIX for sub-path deployment
- ✅ **Security Logging** - Rotating logs for admin actions
- ✅ Python API

## 🔒 Security

⚠️ **IMPORTANT:** CMS has **no built-in authentication**. The `/admin/` path **MUST be protected in the reverse proxy!**

**See [OWASP10_Report.md](OWASP10_Report.md) for:**
- Complete security analysis (OWASP Top 10)
- Nginx/Apache configuration examples with HTTP Basic Auth
- Security best practices
- Action items before production deployment

**Quick tip for Nginx:**
```nginx
location /admin/ {
    auth_basic "CMS Admin";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:5001/admin/;
}
```

## 📦 Dependencies

```bash
# Create virtual environment
python3 -m venv .venv

# Activate
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install packages
pip install -r requirements.txt
```

**Required:**
- Python 3.8+
- Pillow (image processing)

## 🖼️ Image Processing

### Add Logo/Watermark

```python
from src.image_processor import ImageProcessor

processor = ImageProcessor(logo_path="logo.png")

# Place logo on image
processor.add_watermark(
    image_path="image.jpg",
    output_path="image_with_logo.jpg",
    position="bottom-right",    # bottom-right, bottom-left, top-right, top-left, center
    logo_size_ratio=0.15,       # Logo = 15% of image width
    opacity=255,                # Transparency (0-255)
    margin=20                   # Distance from edge
)
```

### Automatically on Import

```python
from scripts.import_article import import_article

import_article(
    title="Article with Logo",
    content="# Content",
    image_paths=["image1.jpg", "image2.jpg"],
    logo_path="logo.png",
    add_watermark=True,
    watermark_position="bottom-right"
)
```

### Test

```bash
# Image processing test
python scripts/test_images.py
```

## 🧪 API Tests

### Setup

```bash
cd tests/
pip install -r requirements.txt
```

### Run Tests

**Local Tests:**
```bash
# Against localhost:5001
pytest test_api.py -v
```

**Stage Tests:**
```bash
# Against stage:5001/cms
pytest test_stage.py -v

# Or with environment variables
CMS_URL=http://stage:5001 CMS_PREFIX=/cms python test_api.py
```

**Test Coverage:**
- Export/Import API
- Reader interface
- Tag filtering
- APP_PREFIX functionality
- Static files with proxy

See details in [tests/README.md](tests/README.md)
