# Nuke Asset Browser v2.0.0

A modern, full-featured draft asset browser for Foundry Nuke 16+, built with PySide6.

Browse, search, save, manage, and import `.nk` templates directly from Nuke's Node Graph — no external panels needed.

---

## Features

- **Browse** — Grid view with thumbnail previews, favorite stars, status badges
- **Search** — Real-time text search across name, tags, and file path (300ms debounce)
- **Filter** — Sidebar with type, author, tag, status, and sort filters
- **Save** — Save Node Graph selections as named draft templates with metadata
- **Delete & Favorite** — Context-menu or UI actions with confirmation and toast feedback
- **Drag & Drop** — Drag a card into Nuke's Node Graph to import the `.nk` template
- **Dark Theme** — Full dark UI, built-in, no extra configs required

## Architecture

```
asset_browser/
├── core/           # Data models, thumbnail pipeline, search engine
├── db/             # Storage backends (JSON, PostgreSQL)
├── ui/             # PySide6 widgets, dialogs, theme system
│   ├── dialogs/    # Save, settings, error dialogs
│   └── widgets/    # Cards, sidebar, search bar, toast, grid
├── utils/          # Config manager, logging
└── tests/          # Pytest suite (37+ tests)
```

### Storage Backends

| Backend | Description | Default |
|---------|-------------|---------|
| **JSON** | File-based storage at `~/.nuke/AssetBrowser/drafts.json` | ✅ Yes |
| **PostgreSQL** | Local/remote PG 16+, table `browser.drafts` | Auto-selected when available |

The storage layer auto-detects PostgreSQL connectivity and falls back to JSON.

## Installation

### 1. Place the package

```bash
# Copy to Nuke's python path or your pipeline
cp -r asset_browser /your/pipeline/python/
```

### 2. Add a Nuke menu entry

Create `~/.nuke/menu.py` (or append to existing):

```python
import nuke
nu = nuke

# Add asset_browser to Python path if not already there
import sys
ASSET_BROWSER_ROOT = "/path/to/asset_browser"
if ASSET_BROWSER_ROOT not in sys.path:
    sys.path.insert(0, ASSET_BROWSER_ROOT)

from asset_browser.ui.main_window import MainWindow

def launch_asset_browser():
    global __asset_browser_window
    try:
        __asset_browser_window.show()
        __asset_browser_window.raise_()
    except Exception:
        __asset_browser_window = MainWindow()
        __asset_browser_window.show()

nu.menu("Nuke").addCommand("Asset Browser", launch_asset_browser)
```

### 3. (Optional) PostgreSQL setup

```sql
-- Create the schema and table
CREATE SCHEMA IF NOT EXISTS browser;
CREATE TABLE IF NOT EXISTS browser.drafts (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    draft_type  TEXT NOT NULL DEFAULT 'comp',
    author      TEXT NOT NULL DEFAULT 'unknown',
    tags        TEXT[] DEFAULT '{}',
    status      TEXT DEFAULT 'wip',
    description TEXT DEFAULT '',
    path        TEXT NOT NULL,
    thumbnail   TEXT,
    favorite    BOOLEAN DEFAULT FALSE,
    use_count   INTEGER DEFAULT 0,
    visibility  TEXT DEFAULT 'private',
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);
```

## Usage

### Main Window

| Area | Function |
|------|----------|
| **Search bar** | Type name, tag, or path — searches automatically after 300ms pause |
| **Sidebar (right)** | Filter by type, author, status, tag; sort by latest/hottest |
| **Thumbnail grid** | Click to select, double-click to activate (hook-ready) |
| **Drag** | Drag card into Nuke Node Graph to import `.nk` |

### Actions

| Action | How |
|--------|-----|
| **Save draft** | Click **📤 Upload** button |
| **Delete draft** | Right-click → **Delete**, confirm in dialog |
| **Toggle favorite** | Click ⭐ star on card |
| **Edit draft** | Right-click → **Edit** (opens save dialog pre-filled) |

### Status Badges

| Badge | Meaning |
|-------|---------|
| 🔴 **WIP** | Work in progress |
| 🟡 **Review** | Ready for review |
| 🟢 **Final** | Final/approved |

## Configuration

Settings are stored at `~/.nuke/AssetBrowser/settings.json`:

```json
{
  "thumbnail_size": 128,
  "theme": "dark",
  "filters": {
    "show_deleted": false,
    "default_view": "grid"
  }
}
```

Open **Settings** from the gear icon in the top bar.

## Key Bindings

| Key | Action |
|-----|--------|
| `Ctrl+F` / `Cmd+F` | Focus search bar |
| `Delete` | Delete selected draft |
| `Escape` | Close dialog / clear search |

## Development

### Requirements

- Python 3.11+
- PySide6
- Nuke 16+ (runtime)
- psycopg2 2.9+ (optional, for PostgreSQL)

### Running tests

```bash
cd asset_browser
conda run -p env pytest tests/ -q
```

## License

Internal pipeline tool — proprietary.
