(() => {
  const initial = window.__INITIAL_DATA__ || {};
  const base = (window.APP_PREFIX || '').replace(/\/$/, '');

  const app = Vue.createApp({
    data() {
      return {
        page: initial.page || 'unknown',
        articles: initial.articles || [],
        current_tag: initial.current_tag || null,
        searchQuery: '',
        viewMode: localStorage.getItem('adminViewMode') || 'grid',
        sortBy: localStorage.getItem('adminSortBy') || 'id',
        sortOrder: localStorage.getItem('adminSortOrder') || 'desc',
        // For edit page
        article: initial.article || null,
        images: initial.images || [],
        whatsapp_text: initial.whatsapp_text || '',
        form: {
          title: (initial.article && initial.article.title) || '',
          author: (initial.article && initial.article.author) || '',
          content: (initial.article && initial.article.content) || '',
          tags_str: (initial.article && (initial.article.tags || []).join(', ')) || '',
          created_at_input: (initial.article && initial.article.created_at) ? (initial.article.created_at.replace(' ', 'T').slice(0,16)) : '',
          published: !!(initial.article && initial.article.published),
          add_watermark: false
        }
        ,
        formSubmitting: false,
        uploadProgress: 0,
        toasts: []
      };
    },
    computed: {
      filteredArticles() {
        const q = (this.searchQuery || '').toLowerCase().trim();
        let list = this.articles.slice();
        if (q) {
          list = list.filter(a => {
            return (a.title || '').toLowerCase().includes(q) || (a.content || '').toLowerCase().includes(q) || (a.tags || []).join(' ').toLowerCase().includes(q);
          });
        }

        // sorting
        const dir = this.sortOrder === 'asc' ? 1 : -1;
        list.sort((a,b) => {
          let va, vb;
          switch (this.sortBy) {
            case 'id':
              va = Number(a.id || 0); vb = Number(b.id || 0); break;
            case 'status':
            case 'published':
              va = a.published ? 1 : 0; vb = b.published ? 1 : 0; break;
            case 'title':
              va = (a.title || '').toLowerCase(); vb = (b.title || '').toLowerCase(); break;
            case 'tags':
              va = (a.tags || []).join(',').toLowerCase(); vb = (b.tags || []).join(',').toLowerCase(); break;
            case 'date':
              va = a.created_at ? new Date(a.created_at).getTime() : 0; vb = b.created_at ? new Date(b.created_at).getTime() : 0; break;
            default:
              va = (a[this.sortBy] || '').toString(); vb = (b[this.sortBy] || '').toString();
          }
          if (va < vb) return -1 * dir;
          if (va > vb) return 1 * dir;
          return 0;
        });

        return list;
      }
    },
    methods: {
      copyPreTextClient(e) {
        const text = (this.whatsapp_text || '').toString();
        // Prefer modern Clipboard API
        if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
          try {
            if (navigator.permissions && navigator.permissions.query) {
              navigator.permissions.query({ name: 'clipboard-write' }).then(() => {
                navigator.clipboard.writeText(text).then(() => {
                  this.showToast('Text in Zwischenablage kopiert', 'success');
                }).catch(err => {
                  console.error('clipboard.writeText failed', err);
                  if (window && typeof window.copyPreText === 'function') window.copyPreText('whatsapp-text', e.target);
                  else this.copyMarkdown(text);
                });
              }).catch(() => {
                navigator.clipboard.writeText(text).then(() => {
                  this.showToast('Text in Zwischenablage kopiert', 'success');
                }).catch(err => {
                  console.error('clipboard.writeText failed', err);
                  if (window && typeof window.copyPreText === 'function') window.copyPreText('whatsapp-text', e.target);
                  else this.copyMarkdown(text);
                });
              });
            } else {
              navigator.clipboard.writeText(text).then(() => {
                this.showToast('Text in Zwischenablage kopiert', 'success');
              }).catch(err => {
                console.error('clipboard.writeText failed', err);
                if (window && typeof window.copyPreText === 'function') window.copyPreText('whatsapp-text', e.target);
                else this.copyMarkdown(text);
              });
            }
            return;
          } catch (err) {
            console.error('clipboard API error', err);
          }
        }

        // fallback to global helper or markdown copy
        if (window && typeof window.copyPreText === 'function') {
          window.copyPreText('whatsapp-text', e.target);
        } else {
          this.copyMarkdown(text);
        }
      },
      async copyImageClient(img, e) {
        const url = this.imageUrl(img);
        // Try Clipboard API with image support first
        if (navigator.clipboard && navigator.clipboard.write && typeof ClipboardItem !== 'undefined') {
          try {
            if (navigator.permissions && navigator.permissions.query) {
              try { await navigator.permissions.query({ name: 'clipboard-write' }); } catch (permErr) { /* ignore */ }
            }
            const resp = await fetch(url, { credentials: 'same-origin' });
            const blob = await resp.blob();
            if (!blob.type || !blob.type.startsWith('image/')) throw new Error('Invalid image type');
            await navigator.clipboard.write([new ClipboardItem({ [blob.type]: blob })]);
            this.showToast('Bild in Zwischenablage kopiert', 'success');
            return;
          } catch (err) {
            console.error('Clipboard image write failed', err);
            // fall through to open tab fallback
          }
        }

        // Fallback: open image in new tab so user can copy/save manually
        try {
          window.open(url, '_blank', 'noopener');
          this.showToast('Bild in neuem Tab geöffnet — bitte speichern oder kopieren', 'info');
        } catch (err2) {
          // last resort: trigger a download link
          try {
            const a = document.createElement('a');
            a.href = url;
            a.target = '_blank';
            a.rel = 'noopener';
            if (img && img.filename) a.download = img.filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            this.showToast('Bild-Download gestartet', 'info');
          } catch (err3) {
            console.error('All image copy fallbacks failed', err3);
            this.showToast('Kopieren nicht unterstützt auf diesem Gerät', 'error');
          }
        }
      },
      /**
       * Return a usable image URL for an image object.
       *
       * Note: the server now populates `img.url` for images, but we keep
       * a client-side fallback to `APP_PREFIX + '/media/images/' + filename`
       * for robustness (older APIs, missing fields, or edge cases).
       */
      imageUrl(img) {
        if (img && img.url) return img.url;
        const fname = (img && img.filename) ? img.filename : '';
        return this.base + '/media/images/' + fname;
      },
      articleViewUrl(id) { return `${base}/admin/article/${id}`; },
      articleEditUrl(id) { return `${base}/admin/article/${id}/edit`; },
      articleWhatsappUrl(id) { return `${base}/admin/article/${id}/whatsapp`; },
      readerArticleUrl(id) { return `${base}/reader/article/${id}`; },
      setView(mode) {
        this.viewMode = mode;
        localStorage.setItem('adminViewMode', mode);
      }
      ,
      // Update URL (no reload) to reflect view mode so bookmarks and server-side expectations remain
      updateUrlViewParam(mode) {
        try {
          const url = new URL(window.location.href);
          if (mode === 'list' || mode === 'cards') {
            url.searchParams.set('view', mode);
            // ensure sort params present
            url.searchParams.set('sort', this.sortBy || localStorage.getItem('adminSortBy') || 'id');
            url.searchParams.set('order', this.sortOrder || localStorage.getItem('adminSortOrder') || 'desc');
          } else {
            url.searchParams.delete('view');
            url.searchParams.delete('sort');
            url.searchParams.delete('order');
          }
          window.history.replaceState({}, '', url.toString());
        } catch (e) {
          // ignore
        }
      }
      ,
      setSort(field) {
        if (this.sortBy === field) {
          this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
          this.sortBy = field;
          // sensible defaults
          this.sortOrder = field === 'id' ? 'desc' : 'asc';
        }
        localStorage.setItem('adminSortBy', this.sortBy);
        localStorage.setItem('adminSortOrder', this.sortOrder);
      }
      ,
      goToArticle(id) {
        window.location.href = this.articleViewUrl(id);
      }
      ,
        async enrichArticlesWithImages() {
        try {
          const resp = await fetch(`${base}/admin/api/export/articles`, { credentials: 'same-origin' });
          if (!resp.ok) return;
          const data = await resp.json();
          if (!data || !data.articles) return;
          const map = {};
          data.articles.forEach(a => { map[a.id] = a; });
          this.articles = this.articles.map(a => {
            const ext = map[a.id];
            if (ext && ext.images && ext.images.length) {
              a.images = ext.images;
              a.thumbnail = (ext.images[0].url ? ext.images[0].url : (base + '/media/images/' + (ext.images[0].filename || '')));
            } else {
              a.images = a.images || [];
              a.thumbnail = a.thumbnail || null;
            }
            return a;
          });
        } catch (e) {
          console.error('Failed to enrich articles with images', e);
        }
      },

      showToast(message, type='info') {
        const id = Date.now() + Math.random();
        this.toasts.push({ id, message, type });
        setTimeout(() => { this.toasts = this.toasts.filter(t => t.id !== id); }, 4000);
      }
      ,
      // submit the create/edit form via AJAX
      async submitForm() {
        const vm = this;
        const isEdit = vm.article && vm.article.id;
        const url = isEdit ? `${base}/admin/article/${vm.article.id}/edit` : `${base}/admin/article/new`;

        const fd = new FormData();
        fd.append('title', vm.form.title || '');
        fd.append('content', vm.form.content || '');
        fd.append('author', vm.form.author || '');
        fd.append('published', vm.form.published ? 'on' : 'off');
        fd.append('tags', vm.form.tags_str || '');
        fd.append('created_at', vm.form.created_at_input || '');
        if (vm.form.add_watermark) fd.append('add_watermark', 'on');

        const input = vm.$refs.images;
        if (input && input.files) {
          for (let i = 0; i < input.files.length; i++) fd.append('images', input.files[i]);
        }

        // Use XHR to get upload progress
        try {
          vm.formSubmitting = true;
          vm.uploadProgress = 0;
          const xhr = new XMLHttpRequest();
          xhr.open('POST', url, true);
          xhr.withCredentials = true;
          xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
              vm.uploadProgress = Math.round((e.loaded / e.total) * 100);
            }
          };
          xhr.onload = function() {
            vm.formSubmitting = false;
            vm.uploadProgress = 0;
            if (xhr.status >= 200 && xhr.status < 300) {
              vm.showToast('Artikel gespeichert', 'success');
              // Follow redirect if provided by server
              if (xhr.responseURL && xhr.responseURL !== window.location.href) window.location.href = xhr.responseURL; else window.location.reload();
            } else {
              vm.showToast('Fehler beim Speichern', 'error');
            }
          };
          xhr.onerror = function() {
            vm.formSubmitting = false;
            vm.uploadProgress = 0;
            vm.showToast('Netzwerkfehler beim Speichern', 'error');
          };
          xhr.send(fd);
        } catch (e) {
          vm.formSubmitting = false;
          vm.uploadProgress = 0;
          console.error(e);
          vm.showToast('Fehler beim Speichern', 'error');
        }
      },

      async deleteImage(imageId) {
        if (!confirm('Bild löschen?')) return;
        try {
          const resp = await fetch(`${base}/admin/image/${imageId}/delete`, { method: 'POST', credentials: 'same-origin', redirect: 'follow' });
          if (resp.ok) window.location.reload(); else alert('Fehler beim Löschen');
        } catch (e) { console.error(e); alert('Fehler beim Löschen'); }
      }
      ,
      async deleteArticle(articleId) {
        if (!confirm('Artikel wirklich löschen?')) return;
        try {
          const resp = await fetch(`${base}/admin/article/${articleId}/delete`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Accept': 'text/html' }
          });
          if (resp.ok) {
            // Remove article from local list if present
            this.articles = (this.articles || []).filter(a => String(a.id) !== String(articleId));
            this.showToast('Artikel gelöscht', 'success');
            // If we are currently viewing that article, navigate back to admin list
            if (this.page === 'view_article' && this.article && String(this.article.id) === String(articleId)) {
              window.location.href = base + '/admin';
            }
          } else {
            const text = await resp.text().catch(() => 'Fehler');
            this.showToast('Fehler beim Löschen', 'error');
            console.error('Delete failed', resp.status, text);
          }
        } catch (e) {
          console.error(e);
          this.showToast('Netzwerkfehler beim Löschen', 'error');
        }
      }
    },
    template: `
      <div>
        <div class="toast-container">
          <div v-for="t in toasts" :key="t.id" :class="['toast', t.type]">{{ t.message }}</div>
        </div>
        <template v-if="page === 'admin_index'">
          <div class="header-section">
            <h1>Artikel-Verwaltung (Vue)</h1>
            <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;">
              <input v-model="searchQuery" placeholder="Artikel durchsuchen..." class="search-input" />
              <a :href="base + '/admin/article/new'" class="btn btn-primary">✏️ Neuer Artikel</a>
              <a :href="base + '/reader/'" class="btn btn-secondary">👁️ Reader</a>
              <div class="view-toggle" style="margin-left:auto">
                <button class="btn btn-sm" :class="{ 'active': viewMode === 'grid' }" @click="setView('grid')">Grid</button>
                <button class="btn btn-sm" :class="{ 'active': viewMode === 'list' }" @click="setView('list')">Liste</button>
              </div>
            </div>
          </div>

          <div v-if="filteredArticles.length">
            <div v-if="viewMode === 'grid'" class="articles-grid">
              <div v-for="article in filteredArticles" :key="article.id" class="article-card" style="cursor:pointer;" @click="goToArticle(article.id)" tabindex="0" @keydown.enter="goToArticle(article.id)">
                <div v-if="article.thumbnail" style="margin-bottom:8px;text-align:center;">
                  <img :src="article.thumbnail" alt="thumbnail" class="article-thumb">
                </div>
                <div class="article-header"><h2><a :href="articleViewUrl(article.id)" @click.stop>{{ article.title }}</a></h2>
                  <span v-if="article.published" class="badge badge-success" title="Veröffentlicht" aria-label="Veröffentlicht">✓</span>
                  <span v-else class="badge badge-draft" title="Entwurf" aria-label="Entwurf">○</span>
                </div>
                <div class="article-preview" v-html="article.excerpt_html || ''"></div>
                <div class="article-actions">
                  <a :href="articleViewUrl(article.id)" class="btn btn-sm" title="Ansehen" aria-label="Ansehen" @click.stop><span class="icon">👁️</span></a>
                  <a :href="articleEditUrl(article.id)" class="btn btn-sm btn-secondary" title="Bearbeiten" aria-label="Bearbeiten" @click.stop><span class="icon">✏️</span></a>
                  <a :href="articleWhatsappUrl(article.id)" class="btn btn-sm btn-secondary" title="WhatsApp Export" aria-label="WhatsApp Export" @click.stop><span class="icon">📱</span></a>
                  <a href="#" class="btn btn-sm btn-danger" title="Löschen" aria-label="Löschen" @click.stop.prevent="deleteArticle(article.id)"><span class="icon">🗑️</span></a>
                </div>
              </div>
            </div>
            <div v-else class="articles-list">
              <table class="articles-table">
                <thead>
                  <tr>
                    <th><a href="#" class="sort-header" @click.prevent="setSort('id')">ID <span v-if="sortBy==='id'">{{ sortOrder==='asc' ? '▲' : '▼' }}</span></a></th>
                    <th><a href="#" class="sort-header" @click.prevent="setSort('status')">Status <span v-if="sortBy==='status' || sortBy==='published'">{{ sortOrder==='asc' ? '▲' : '▼' }}</span></a></th>
                    <th><a href="#" class="sort-header" @click.prevent="setSort('title')">Titel <span v-if="sortBy==='title'">{{ sortOrder==='asc' ? '▲' : '▼' }}</span></a></th>
                    <th><a href="#" class="sort-header" @click.prevent="setSort('tags')">Tags <span v-if="sortBy==='tags'">{{ sortOrder==='asc' ? '▲' : '▼' }}</span></a></th>
                    <th><a href="#" class="sort-header" @click.prevent="setSort('date')">Datum <span v-if="sortBy==='date'">{{ sortOrder==='asc' ? '▲' : '▼' }}</span></a></th>
                    <th>Aktionen</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="article in filteredArticles" :key="article.id">
                    <td>{{ article.id }}</td>
                    <td>
                      <span v-if="article.published" class="badge badge-success" title="Veröffentlicht" aria-label="Veröffentlicht">✓</span>
                      <span v-else class="badge badge-draft" title="Entwurf" aria-label="Entwurf">○</span>
                    </td>
                    <td><a :href="articleViewUrl(article.id)">{{ article.title }}</a></td>
                    <td>{{ (article.tags || []).slice(0,3).join(', ') }}</td>
                    <td>{{ article.created_at }}</td>
                    <td>
                      <a :href="articleViewUrl(article.id)" class="btn btn-sm" title="Ansehen" aria-label="Ansehen"><span class="icon">👁️</span></a>
                      <a :href="articleEditUrl(article.id)" class="btn btn-sm btn-secondary" title="Bearbeiten" aria-label="Bearbeiten"><span class="icon">✏️</span></a>
                      <a :href="articleWhatsappUrl(article.id)" class="btn btn-sm btn-secondary" title="WhatsApp Export" aria-label="WhatsApp Export"><span class="icon">📱</span></a>
                      <a href="#" class="btn btn-sm btn-danger" title="Löschen" aria-label="Löschen" @click.prevent="deleteArticle(article.id)"><span class="icon">🗑️</span></a>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div v-else class="empty-state">
            <p>Keine Artikel gefunden.</p>
            <a :href="base + '/admin/article/new'" class="btn btn-primary">Ersten Artikel erstellen</a>
          </div>
        </template>

        <template v-else-if="page === 'reader_index'">
          <div class="reader-header">
            <div style="display:flex;align-items:center;gap:0.75rem;justify-content:center;flex-wrap:wrap;">
              <h1 style="margin:0;">Aktuelle Artikel</h1>
              <span v-if="current_tag" class="tag-filter-badge">Filter: <strong style="margin-left:0.4rem;">{{ current_tag }}</strong>
                <a :href="base + '/reader'" class="clear-filter clear-filter-inline" title="Filter entfernen" aria-label="Filter entfernen">✕</a>
              </span>
            </div>
            <div style="margin-bottom:8px;">
              <input v-model="searchQuery" placeholder="Suchen..." class="search-input-small" />
            </div>
          </div>
          <div v-if="filteredArticles.length" class="articles-list">
            <article v-for="article in filteredArticles" :key="article.id" class="article-card">
              <div class="article-header"><h2><a :href="readerArticleUrl(article.id)">{{ article.title }}</a></h2>
                <time class="article-date">{{ article.created_at }}</time>
              </div>
              <div class="article-excerpt markdown-content" v-html="article.excerpt_html || ''"></div>
              <div class="article-tags" v-if="article.tags">
                <a v-for="tag in article.tags" :key="tag" :href="(current_tag && current_tag.toLowerCase() === tag.toLowerCase()) ? '#' : (base + '/reader/tag/' + encodeURIComponent(tag))" class="tag">{{ tag }}</a>
              </div>
            </article>
          </div>
          <div v-else class="empty-state"><p>Keine Artikel verfügbar.</p></div>
        </template>
        <template v-else-if="page === 'reader_article'">
          <article class="article-view">
            <div class="article-view-header">
              <h1>{{ article.title }}</h1>
              <div class="article-view-meta">
                <span v-if="article.author">👤 {{ article.author }}</span>
                <span>📅 {{ article.created_at }}</span>
                <span v-if="article.updated_at && article.updated_at !== article.created_at">✏️ Aktualisiert: {{ article.updated_at }}</span>
                <span v-if="article.published" class="badge badge-success">Veröffentlicht</span>
                <span v-else class="badge badge-draft">Entwurf</span>
              </div>

              <div v-if="article.tags && article.tags.length" class="article-tags">
                <span v-for="t in article.tags" :key="t" class="tag">{{ t }}</span>
              </div>
            </div>

            <div v-if="images && images.length" class="article-images">
              <div v-for="img in images" :key="img.id" class="image-container">
                <img :src="imageUrl(img)" :alt="img.alt_text || ''">
                <p v-if="img.caption" class="image-caption">{{ img.caption }}</p>
              </div>
            </div>

            <div class="article-content markdown-content" v-html="article.content_html || ''"></div>

            <div class="article-view-actions">
              <a :href="base + '/reader'" class="btn btn-secondary" title="Zurück zur Übersicht" aria-label="Zurück">↩️</a>
            </div>
          </article>
        </template>
        <template v-else-if="page === 'edit_article'">
          <div class="editor-container">
            <h1>{{ article && article.id ? 'Artikel bearbeiten' : 'Neuer Artikel' }}</h1>

            <form @submit.prevent="submitForm" enctype="multipart/form-data" class="article-form">
              <div class="form-group">
                <label for="title">Titel *</label>
                <input id="title" v-model="form.title" required class="form-control">
              </div>

              <div class="form-group">
                <label for="author">Autor</label>
                <input id="author" v-model="form.author" class="form-control">
              </div>

              <div class="form-group">
                <label for="content">Inhalt (Markdown) *</label>
                <textarea id="content" v-model="form.content" rows="20" required class="form-control code-editor"></textarea>
                <small class="help-text">Markdown-Syntax: **fett**, *kursiv*, # Überschrift, [Link](url), ![Bild](url)</small>
              </div>

              <div class="form-group">
                <label for="tags">Tags (komma-getrennt)</label>
                <input id="tags" v-model="form.tags_str" class="form-control" placeholder="news, tech, wichtig">
              </div>

              <div class="form-group">
                <label for="created_at">Erstellungsdatum</label>
                <input id="created_at" v-model="form.created_at_input" type="datetime-local" class="form-control">
                <small class="help-text">Datum und Uhrzeit der Artikelerstellung</small>
              </div>

              <div class="form-group">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="form.published">
                  Veröffentlicht
                </label>
              </div>

              <div class="form-group">
                <label for="images">Bilder hochladen</label>
                <input id="images" ref="images" type="file" multiple accept="image/*" class="form-control">
                <small class="help-text">JPG, PNG, GIF, WebP (max 16MB pro Bild)</small>
              </div>

              <div class="form-group">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="form.add_watermark">
                  Logo/Wasserzeichen zu Bildern hinzufügen
                </label>
                <small class="help-text">Benötigt logo.png im Projektordner</small>
              </div>

              <div class="form-actions">
                <a :href="article && article.id ? (base + '/admin/article/' + article.id) : (base + '/admin')" class="btn btn-secondary" title="Abbrechen" aria-label="Abbrechen">↩️</a>
                <button type="submit" class="btn btn-primary" title="Speichern" aria-label="Speichern" :disabled="formSubmitting">
                  <span v-if="!formSubmitting">💾</span>
                  <span v-else>Speichern... {{ uploadProgress }}%</span>
                </button>
              </div>
              <div v-if="formSubmitting" class="upload-progress"><div class="bar" :style="{width: uploadProgress + '%'}"></div></div>
            </form>

            <div v-if="images && images.length" class="existing-images">
              <h3>Vorhandene Bilder</h3>
              <div class="images-grid">
                <div v-for="img in images" :key="img.id" class="image-item">
                  <img :src="imageUrl(img)" :alt="img.alt_text || ''">
                  <div class="image-markdown">
                    <code class="markdown-code">{{ '![Bild](' + imageUrl(img) + ')' }}</code>
                    <button type="button" class="btn btn-sm btn-copy" @click.prevent="copyMarkdown('![Bild](' + imageUrl(img) + ')')">📋</button>
                  </div>
                  <form :action="base + '/admin/image/' + img.id + '/delete'" method="POST" @submit.prevent="deleteImage(img.id)" style="margin-top:0.5rem;">
                    <button type="submit" class="btn btn-sm btn-danger" style="width:100%">🗑️</button>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </template>

        <template v-else-if="page === 'view_article'">
          <div class="article-view">
            <div class="article-view-header">
              <h1>{{ article.title }}</h1>
              <div class="article-view-meta">
                <span v-if="article.author && article.author !== 'None'">👤 {{ article.author }}</span>
                <span>📅 {{ article.created_at }}</span>
                <span v-if="article.updated_at && article.updated_at !== article.created_at">✏️ Aktualisiert: {{ article.updated_at }}</span>
                <span v-if="article.published" class="badge badge-success">Veröffentlicht</span>
                <span v-else class="badge badge-draft">Entwurf</span>
              </div>

              <div v-if="article.tags" class="article-tags">
                <span v-for="t in article.tags" :key="t" class="tag">{{ t }}</span>
              </div>
            </div>

            <div v-if="images && images.length" class="article-images">
              <div v-for="img in images" :key="img.id" class="image-container">
                <img :src="imageUrl(img)" :alt="img.alt_text || ''">
                <p v-if="img.caption" class="image-caption">{{ img.caption }}</p>
              </div>
            </div>

            <div class="article-content markdown-content" v-html="article.content_html || ''"></div>

            <div class="article-view-actions">
              <a :href="base + '/admin'" class="btn btn-secondary" title="Zurück zur Übersicht" aria-label="Zurück">↩️</a>
              <a :href="base + '/admin/article/' + article.id + '/edit'" class="btn btn-primary" title="Bearbeiten" aria-label="Bearbeiten">✏️</a>
              <a :href="base + '/admin/article/' + article.id + '/whatsapp'" class="btn btn-success" title="WhatsApp Export" aria-label="WhatsApp Export">📱</a>
              <form :action="base + '/admin/article/' + article.id + '/delete'" method="POST" style="display:inline;" @submit.prevent="() => { if(confirm('Wirklich löschen?')) { window.location.href = base + '/admin/article/' + article.id + '/delete'; } }">
                <button type="submit" class="btn btn-danger" title="Löschen" aria-label="Löschen">🗑️</button>
              </form>
            </div>
          </div>
        </template>

        <template v-else-if="page === 'whatsapp_export'">
          <div class="editor-container">
            <h1>WhatsApp Export</h1>
            <div class="form-group">
              <label>Vorgeschlagener Text</label>
              <pre id="whatsapp-text" class="form-control" style="white-space:pre-wrap;">{{ whatsapp_text || '' }}</pre>
              <button class="btn btn-sm" @click.prevent="copyPreTextClient($event)">📋 Kopieren</button>
            </div>
            <div v-if="images && images.length" class="export-images">
              <h3>Bilder</h3>
              <div v-for="(img, idx) in images" :key="img.id || idx" class="image-item">
                <img :src="imageUrl(img)" :alt="img.alt_text || ''">
                <div class="image-actions">
                  <button class="btn btn-sm" @click.prevent="copyImageClient(img, $event)">📋 Bild kopieren</button>
                </div>
              </div>
            </div>
            <div class="form-actions">
              <a :href="base + '/admin'" class="btn btn-secondary">↩️ Zurück</a>
            </div>
          </div>
        </template>

        <template v-else>
          <div>Unsupported page for Vue frontend.</div>
        </template>
      </div>
    `
  });

  // submit/delete moved into component methods above

  app.mixin({
    data() {
      return {
        base
      };
    },
    methods: {
      copyMarkdown(text) {
        navigator.clipboard.writeText(text).then(() => alert('Markdown kopiert')).catch(() => alert('Kopieren fehlgeschlagen'));
      }
    }
  });

  // Only mount Vue for pages where we implemented Vue UI.
  // For server-rendered pages like view/edit/whatsapp, leave the original HTML intact.
  const mountPages = ['admin_index','reader_index', 'reader_article', 'edit_article', 'view_article', 'whatsapp_export'];
  let vm = null;
  if (mountPages.includes(initial.page)) {
    vm = app.mount('#vue-app');
    // expose the app instance for external callers
    window.__VUE_APP__ = vm;

    // global showToast helper
    window.showToast = function(message, type='info') {
      if (window.__VUE_APP__ && typeof window.__VUE_APP__.showToast === 'function') {
        window.__VUE_APP__.showToast(message, type);
      } else {
        // fallback
        console.info('Toast:', type, message);
        alert(message);
      }
    };

    // Consume server-provided flashes if present
    try {
      const serverToasts = window.__SERVER_TOASTS__ || [];
      if (serverToasts && serverToasts.length && vm && typeof vm.showToast === 'function') {
        serverToasts.forEach(item => {
          let category = 'info';
          let message = '';
          if (Array.isArray(item)) { category = item[0] || 'info'; message = item[1] || ''; }
          else if (item && typeof item === 'object') { category = item.category || item.type || 'info'; message = item.message || item.msg || item.text || ''; }
          else { message = String(item); }
          if (message) vm.showToast(message, category);
        });
      }
    } catch (e) {
      console.error('Error processing server toasts', e);
    }
    // Enrich admin index with images/thumbnails from API
    if (initial.page === 'admin_index' && vm && typeof vm.enrichArticlesWithImages === 'function') {
      vm.enrichArticlesWithImages();
    }
    // Ensure view mode reflects URL param (or fallback to localStorage)
    try {
      const urlp = new URL(window.location.href).searchParams;
      const urlView = urlp.get('view');
      if (urlView) {
        vm.viewMode = urlView;
        localStorage.setItem('adminViewMode', urlView);
      } else {
        const saved = localStorage.getItem('adminViewMode');
        if (saved) vm.viewMode = saved;
      }
    } catch (e) {
      // ignore
    }
  } else {
    // Do not mount Vue — preserve server-rendered template
    console.info('Vue not mounted for page:', initial.page);
  }
})();
