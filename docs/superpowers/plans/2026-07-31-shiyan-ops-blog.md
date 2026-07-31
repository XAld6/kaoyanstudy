# 十堰运维札记 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy a lightweight Chinese technical blog with browser-based administration to the user's NAT VPS.

**Architecture:** A FastAPI application renders public and admin pages and stores content in SQLite. Nginx serves static uploads and reverse-proxies requests to a localhost-only Uvicorn process managed by systemd. The application code is developed in an isolated Git worktree, then copied to `/opt/shiyan-blog/app` on the VPS.

**Tech Stack:** Python 3.10, FastAPI, Uvicorn, Jinja2, SQLite, `markdown-it-py`, Bleach, Pillow, pytest, Nginx, systemd, vanilla HTML/CSS/JavaScript.

---

## File structure

```text
01_projects/shiyan-ops-blog/
  app/
    __init__.py
    auth.py
    config.py
    database.py
    main.py
    markdown.py
    schemas.py
    services/posts.py
    static/
      app.js
      styles.css
      images/route-observation.webp
    templates/
      base.html
      home.html
      article.html
      archive.html
      tags.html
      about.html
      not_found.html
      admin_login.html
      admin_dashboard.html
      admin_posts.html
      admin_editor.html
      admin_media.html
  deploy/
    backup.sh
    nginx.conf
    shiyan-blog.service
    shiyan-blog-backup.service
    shiyan-blog-backup.timer
  scripts/
    create_admin.py
    seed_content.py
  tests/
    conftest.py
    test_auth.py
    test_posts.py
    test_markdown.py
    test_media.py
    test_deploy.py
  .gitignore
  README.md
  requirements.txt
  pytest.ini
```

### Task 1: Create an isolated development worktree

**Files:**
- Create: `D:/xm-worktrees/shiyan-ops-blog/` through `git worktree`
- Read: `D:/xm/docs/superpowers/specs/2026-07-31-shiyan-ops-blog-design.md`

- [ ] **Step 1: Create the feature branch and worktree without touching the dirty primary worktree**

```powershell
git worktree add -b codex/shiyan-ops-blog D:/xm-worktrees/shiyan-ops-blog master
```

Expected: a new `codex/shiyan-ops-blog` worktree contains the approved design and plan documents.

- [ ] **Step 2: Verify worktree isolation**

```powershell
git -C D:/xm-worktrees/shiyan-ops-blog status --short --branch
```

Expected: branch is `codex/shiyan-ops-blog` and working tree is clean.

- [ ] **Step 3: Commit no application code in this task**

Expected: the first code commit happens only after a failing test is written.

### Task 2: Establish the application configuration and SQLite schema with tests

**Files:**
- Create: `01_projects/shiyan-ops-blog/app/config.py`
- Create: `01_projects/shiyan-ops-blog/app/database.py`
- Create: `01_projects/shiyan-ops-blog/app/__init__.py`
- Create: `01_projects/shiyan-ops-blog/tests/conftest.py`
- Create: `01_projects/shiyan-ops-blog/tests/test_posts.py`
- Create: `01_projects/shiyan-ops-blog/requirements.txt`
- Create: `01_projects/shiyan-ops-blog/pytest.ini`

- [ ] **Step 1: Write database initialization tests before implementation**

```python
def test_initialize_database_creates_required_tables(tmp_path):
    database_path = tmp_path / "blog.db"
    initialize_database(database_path)

    with connect_database(database_path) as connection:
        names = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert {"users", "sessions", "posts", "tags", "post_tags", "media"} <= names


def test_database_enables_wal_mode(tmp_path):
    database_path = tmp_path / "blog.db"
    initialize_database(database_path)

    with connect_database(database_path) as connection:
        mode = connection.execute("PRAGMA journal_mode").fetchone()[0]

    assert mode.lower() == "wal"
```

- [ ] **Step 2: Run the failing tests**

```powershell
python -m pytest tests/test_posts.py -q
```

Expected: FAIL because `app.database` does not exist.

- [ ] **Step 3: Implement deterministic settings and schema setup**

```python
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    content_markdown TEXT NOT NULL,
    content_html TEXT NOT NULL,
    cover_path TEXT,
    status TEXT NOT NULL CHECK(status IN ('draft', 'published')),
    published_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, slug TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS post_tags (
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);
CREATE TABLE IF NOT EXISTS media (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    mime_type TEXT NOT NULL,
    size INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
"""

def initialize_database(path: Path) -> None:
    with connect_database(path) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.executescript(SCHEMA)
```

Implementation details: use `sqlite3.Row`, foreign keys, unique `slug` values, `status` constrained to `draft` and `published`, and UTC ISO-8601 timestamps.

- [ ] **Step 4: Run the database tests**

```powershell
python -m pytest tests/test_posts.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the schema baseline**

```powershell
git add 01_projects/shiyan-ops-blog
git commit -m "feat: add blog database schema"
```

### Task 3: Implement Markdown sanitation and post lifecycle with TDD

**Files:**
- Create: `01_projects/shiyan-ops-blog/app/markdown.py`
- Create: `01_projects/shiyan-ops-blog/app/services/posts.py`
- Create: `01_projects/shiyan-ops-blog/app/schemas.py`
- Create: `01_projects/shiyan-ops-blog/tests/test_markdown.py`
- Modify: `01_projects/shiyan-ops-blog/tests/test_posts.py`

- [ ] **Step 1: Write rendering and post lifecycle tests**

```python
def test_render_markdown_removes_scripts_and_keeps_code_block():
    html = render_markdown("# title\n\n<script>alert(1)</script>\n\n```bash\necho ok\n```")

    assert "<h1>title</h1>" in html
    assert "<pre><code class=\"language-bash\">" in html
    assert "<script" not in html


def test_published_post_is_visible_but_draft_is_not(repository):
    repository.create_post(title="Draft", slug="draft", content_markdown="draft", status="draft")
    repository.create_post(title="Live", slug="live", content_markdown="live", status="published")

    assert [post.slug for post in repository.list_public_posts()] == ["live"]
```

- [ ] **Step 2: Run tests to verify failure**

```powershell
python -m pytest tests/test_markdown.py tests/test_posts.py -q
```

Expected: FAIL because renderer and repository are missing.

- [ ] **Step 3: Implement a sanitized renderer and post repository**

```python
def render_markdown(source: str) -> str:
    rendered = markdown_it.render(source)
    return bleach.clean(rendered, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, protocols=["http", "https", "mailto"])

def list_public_posts(self, query: str = "", tag: str = "") -> list[Post]:
    return self._fetch_posts(status="published", query=query, tag=tag)
```

Implementation details: render on create/update, validate title and content lengths, normalize tags, retain the existing `published_at` when editing a published post, and return `None` for missing posts rather than exposing database errors.

- [ ] **Step 4: Run lifecycle tests**

```powershell
python -m pytest tests/test_markdown.py tests/test_posts.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit post services**

```powershell
git add 01_projects/shiyan-ops-blog
git commit -m "feat: add sanitized post publishing"
```

### Task 4: Implement administrator authentication with tests

**Files:**
- Create: `01_projects/shiyan-ops-blog/app/auth.py`
- Create: `01_projects/shiyan-ops-blog/scripts/create_admin.py`
- Create: `01_projects/shiyan-ops-blog/tests/test_auth.py`
- Modify: `01_projects/shiyan-ops-blog/app/database.py`

- [ ] **Step 1: Write authentication tests**

```python
def test_password_hash_round_trip():
    encoded = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("wrong", encoded)


def test_session_token_is_not_stored_in_plain_text(auth_service):
    raw_token = auth_service.create_session(user_id=1)
    stored = auth_service.read_session_record(user_id=1)

    assert raw_token != stored["token_hash"]
    assert auth_service.resolve_session(raw_token).user_id == 1
```

- [ ] **Step 2: Run the failure check**

```powershell
python -m pytest tests/test_auth.py -q
```

Expected: FAIL because `app.auth` is absent.

- [ ] **Step 3: Implement password and session primitives**

```python
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"{salt.hex()}${digest.hex()}"

def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    save_token_hash(user_id, sha256(token.encode()).hexdigest(), expires_at=utc_now_plus_days(14))
    return token
```

Implementation details: use constant-time digest comparison, HttpOnly cookies set by the route layer, a 14-day expiration, CSRF token derived from the signed session secret, and a CLI that asks for the initial password through stdin without writing it to a file.

- [ ] **Step 4: Run authentication tests**

```powershell
python -m pytest tests/test_auth.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit authentication**

```powershell
git add 01_projects/shiyan-ops-blog
git commit -m "feat: add admin authentication"
```

### Task 5: Build the public and administrative web surfaces

**Files:**
- Create: `01_projects/shiyan-ops-blog/app/main.py`
- Create: `01_projects/shiyan-ops-blog/app/templates/*.html`
- Create: `01_projects/shiyan-ops-blog/app/static/styles.css`
- Create: `01_projects/shiyan-ops-blog/app/static/app.js`
- Create: `01_projects/shiyan-ops-blog/tests/test_web.py`

- [ ] **Step 1: Write HTTP route tests**

```python
def test_home_renders_published_post(client, seeded_post):
    response = client.get("/")

    assert response.status_code == 200
    assert seeded_post.title in response.text
    assert "十堰运维札记" in response.text


def test_admin_write_route_requires_login(client):
    response = client.post("/api/admin/posts", json={"title": "x"})

    assert response.status_code == 401


def test_article_route_hides_draft(client, seeded_draft):
    response = client.get(f"/posts/{seeded_draft.slug}")

    assert response.status_code == 404
```

- [ ] **Step 2: Run the failure check**

```powershell
python -m pytest tests/test_web.py -q
```

Expected: FAIL because the FastAPI app is absent.

- [ ] **Step 3: Implement templates and routes**

```python
app = FastAPI()
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
def home(request: Request, query: str = "", tag: str = "") -> HTMLResponse:
    posts = repository.list_public_posts(query=query, tag=tag)
    return templates.TemplateResponse("home.html", {"request": request, "posts": posts})

@app.get("/posts/{slug}", response_class=HTMLResponse)
def article(request: Request, slug: str) -> HTMLResponse:
    post = repository.get_public_post(slug)
    if post is None:
        return templates.TemplateResponse("not_found.html", {"request": request}, status_code=404)
    return templates.TemplateResponse("article.html", {"request": request, "post": post})
```

Implementation details: use the confirmed field-notes visual system, local cover image assets, semantic HTML, responsive CSS at 390px and 1440px, no external font/CDN dependence, an accessible mobile navigation button, code-copy buttons, search, tags, `about`, 404, and protected admin pages for dashboard, posts, editor and media.

- [ ] **Step 4: Run route tests**

```powershell
python -m pytest tests/test_web.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit web UI**

```powershell
git add 01_projects/shiyan-ops-blog
git commit -m "feat: add blog public and admin interface"
```

### Task 6: Implement media handling, seed content and local validation

**Files:**
- Create: `01_projects/shiyan-ops-blog/tests/test_media.py`
- Create: `01_projects/shiyan-ops-blog/scripts/seed_content.py`
- Create: `01_projects/shiyan-ops-blog/app/static/images/route-observation.webp`
- Modify: `01_projects/shiyan-ops-blog/app/main.py`
- Modify: `01_projects/shiyan-ops-blog/app/services/posts.py`

- [ ] **Step 1: Write upload validation tests**

```python
def test_image_upload_rejects_non_image(client, authenticated_cookie):
    response = client.post(
        "/api/admin/media",
        files={"file": ("note.txt", b"not an image", "text/plain")},
        cookies=authenticated_cookie,
    )

    assert response.status_code == 415


def test_image_upload_stores_random_name(client, authenticated_cookie, png_bytes):
    response = client.post(
        "/api/admin/media",
        files={"file": ("cover.png", png_bytes, "image/png")},
        cookies=authenticated_cookie,
    )

    assert response.status_code == 201
    assert response.json()["path"].startswith("/uploads/")
    assert "cover.png" not in response.json()["path"]
```

- [ ] **Step 2: Run the failure check**

```powershell
python -m pytest tests/test_media.py -q
```

Expected: FAIL because upload endpoint is absent.

- [ ] **Step 3: Implement media validation and fixtures**

```python
if upload.content_type not in {"image/jpeg", "image/png", "image/webp"}:
    raise HTTPException(status_code=415, detail="Only JPEG, PNG, and WebP images are allowed")
if len(payload) > 5 * 1024 * 1024:
    raise HTTPException(status_code=413, detail="Image exceeds 5 MB")
```

Implementation details: inspect file dimensions with Pillow before storing, generate a random filename, prevent deletion when a media item is referenced by a post, generate the local route-observation cover image, and seed the three approved Chinese articles only when the database has no posts.

- [ ] **Step 4: Run all application tests**

```powershell
python -m pytest -q
```

Expected: PASS with no skipped failures.

- [ ] **Step 5: Run local server and visual checks**

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Expected: homepage, article page, login page, dashboard, editor and mobile navigation render without console errors.

- [ ] **Step 6: Commit media and seed content**

```powershell
git add 01_projects/shiyan-ops-blog
git commit -m "feat: add blog media and starter articles"
```

### Task 7: Prepare deployment artifacts and test their syntax

**Files:**
- Create: `01_projects/shiyan-ops-blog/deploy/nginx.conf`
- Create: `01_projects/shiyan-ops-blog/deploy/shiyan-blog.service`
- Create: `01_projects/shiyan-ops-blog/deploy/shiyan-blog-backup.service`
- Create: `01_projects/shiyan-ops-blog/deploy/shiyan-blog-backup.timer`
- Create: `01_projects/shiyan-ops-blog/deploy/backup.sh`
- Create: `01_projects/shiyan-ops-blog/README.md`

- [ ] **Step 1: Write deployment artifact assertions**

```python
def test_systemd_service_binds_only_localhost():
    unit = Path("deploy/shiyan-blog.service").read_text(encoding="utf-8")
    assert "--host 127.0.0.1" in unit
    assert "User=shiyanblog" in unit


def test_nginx_proxy_targets_local_app():
    config = Path("deploy/nginx.conf").read_text(encoding="utf-8")
    assert "proxy_pass http://127.0.0.1:8000" in config
    assert "client_max_body_size 5m" in config
```

- [ ] **Step 2: Run the failure check**

```powershell
python -m pytest tests/test_deploy.py -q
```

Expected: FAIL because deployment files are absent.

- [ ] **Step 3: Create explicit Nginx, systemd and backup files**

```ini
[Service]
User=shiyanblog
Group=shiyanblog
WorkingDirectory=/opt/shiyan-blog/app
EnvironmentFile=/etc/shiyan-blog/blog.env
ExecStart=/opt/shiyan-blog/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers
Restart=on-failure
```

Implementation details: Nginx must listen on `80`, serve `/uploads/` from `/opt/shiyan-blog/uploads/`, set `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and a restrictive same-origin CSP; backup script must use SQLite `.backup` when `sqlite3` is available, copy media metadata, retain the 7 newest dated backups, and exit nonzero on failure.

- [ ] **Step 4: Run deployment artifact tests**

```powershell
python -m pytest tests/test_deploy.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit deployment artifacts**

```powershell
git add 01_projects/shiyan-ops-blog
git commit -m "feat: add nat vps deployment configuration"
```

### Task 8: Provision and deploy to the NAT VPS

**Files:**
- Copy: `01_projects/shiyan-ops-blog/` to `/opt/shiyan-blog/app/`
- Create remotely: `/etc/shiyan-blog/blog.env`
- Create remotely: `/opt/shiyan-blog/data/blog.db`
- Create remotely: `/opt/shiyan-blog/uploads/`
- Install remotely: `nginx`, `python3-venv`, `sqlite3`

- [ ] **Step 1: Recheck package locks and port ownership before changing the server**

```bash
dpkg --audit
fuser /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock
ss -lntup | grep -E ':(80|8000)\b'
```

Expected: no package repair required; no process holds `80` or `8000`.

- [ ] **Step 2: Install only required operating-system packages**

```bash
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y nginx python3-venv sqlite3
```

Expected: packages install successfully without changing SSH configuration.

- [ ] **Step 3: Create a dedicated service account and directories**

```bash
useradd --system --home /opt/shiyan-blog --shell /usr/sbin/nologin shiyanblog
install -d -o shiyanblog -g shiyanblog -m 0750 /opt/shiyan-blog/data /opt/shiyan-blog/uploads /opt/shiyan-blog/backups
install -d -o root -g shiyanblog -m 0750 /etc/shiyan-blog
```

Expected: `shiyanblog` has no shell login and owns mutable application data.

- [ ] **Step 4: Upload application files and create the virtual environment**

```bash
python3 -m venv /opt/shiyan-blog/venv
/opt/shiyan-blog/venv/bin/pip install --upgrade pip
/opt/shiyan-blog/venv/bin/pip install -r /opt/shiyan-blog/app/requirements.txt
```

Expected: `/opt/shiyan-blog/venv/bin/uvicorn` exists.

- [ ] **Step 5: Create random runtime secrets and the initial administrator**

```bash
umask 077
printf 'BLOG_SECRET_KEY=%s\n' "$(openssl rand -hex 32)" > /etc/shiyan-blog/blog.env
printf 'BLOG_DATABASE_PATH=/opt/shiyan-blog/data/blog.db\n' >> /etc/shiyan-blog/blog.env
printf 'BLOG_UPLOADS_DIR=/opt/shiyan-blog/uploads\n' >> /etc/shiyan-blog/blog.env
/opt/shiyan-blog/venv/bin/python scripts/create_admin.py --username admin
```

Expected: password is entered interactively on the server and never printed or stored in shell history.

- [ ] **Step 6: Seed the starter articles and install service configuration**

```bash
/opt/shiyan-blog/venv/bin/python scripts/seed_content.py
install -m 0644 deploy/shiyan-blog.service /etc/systemd/system/shiyan-blog.service
install -m 0644 deploy/nginx.conf /etc/nginx/sites-available/shiyan-blog
ln -s /etc/nginx/sites-available/shiyan-blog /etc/nginx/sites-enabled/shiyan-blog
rm -f /etc/nginx/sites-enabled/default
```

Expected: app content initializes once; Nginx has one explicit blog virtual host.

- [ ] **Step 7: Start services and enable backups**

```bash
systemctl daemon-reload
systemctl enable --now shiyan-blog.service nginx.service shiyan-blog-backup.timer
nginx -t
systemctl reload nginx
```

Expected: `shiyan-blog`, `nginx`, and the backup timer are active.

- [ ] **Step 8: Commit deployment documentation changes, if any**

```powershell
git add 01_projects/shiyan-ops-blog
git commit -m "docs: record blog deployment"
```

### Task 9: Verify the deployed blog and NAT exposure

**Files:**
- Modify if needed: `01_projects/shiyan-ops-blog/README.md`

- [ ] **Step 1: Verify internal HTTP and health endpoints**

```bash
curl -fsS http://127.0.0.1/ | grep -F '十堰运维札记'
curl -fsS http://127.0.0.1/health
systemctl is-active shiyan-blog nginx shiyan-blog-backup.timer
sqlite3 /opt/shiyan-blog/data/blog.db 'PRAGMA integrity_check;'
```

Expected: home page title is present, health returns JSON, all units are `active`, and integrity check returns `ok`.

- [ ] **Step 2: Verify that app port is not publicly bound**

```bash
ss -lntup | grep -E ':(80|8000)\b'
```

Expected: Nginx binds `0.0.0.0:80`; Uvicorn binds only `127.0.0.1:8000`.

- [ ] **Step 3: Verify public NAT mapping from the local machine**

```powershell
Test-NetConnection -ComputerName 160.202.238.53 -Port 18080
curl.exe -I http://160.202.238.53:18080/
```

Expected: TCP succeeds and HTTP returns `200`. The NAT provider panel must map public `18080/TCP` to VPS `80/TCP` before this external test can pass.

- [ ] **Step 4: Test administrator workflow in a browser**

1. Open `/admin/login` through the mapped port.
2. Log in with the password set during deployment.
3. Create a draft, preview it, publish it, view it publicly, then delete it.
4. Upload a PNG or WebP under 5MB and confirm its media URL resolves.

Expected: all actions complete without server errors; draft is never visible at a public URL.

- [ ] **Step 5: Capture desktop and mobile screenshots and commit final application changes**

```powershell
python -m pytest -q
git status --short
```

Expected: all tests pass and only intentional blog project changes remain before the final commit.
