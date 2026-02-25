# AUDIOBOOKBAY DOWNLOADER

**Generated:** 2026-02-21
**Commit:** 3331338
**Branch:** main

## OVERVIEW

FastAPI web app for searching AudiobookBay via Jackett and managing torrent downloads with optional Beets library integration. Supports Transmission, qBittorrent, and Decypharr torrent clients.

## STRUCTURE

```
abb/
├── main.py              # FastAPI app entry point, routes, auth
├── torrent.py           # Torrent client implementations (Transmission, qBittorrent, Decypharr)
├── torrent_service.py   # Service layer wrapping torrent clients
├── audiobookbay.py      # Jackett search integration
├── beetsapi.py          # Beets music library auto-import
├── models.py            # Pydantic models (User, TorrentRequest, enums)
├── constants.py         # Environment variable loading
├── db.py                # TinyDB for beets candidate storage
├── utils.py             # Logging utility
├── static/              # Web UI (Alpine.js + Tailwind)
├── secrets/             # Environment files (git-crypt encrypted)
└── example/             # Docker example configs
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add API endpoint | main.py | All routes defined here |
| Modify torrent behavior | torrent.py | Abstract class + implementations |
| Change search logic | audiobookbay.py | Jackett API integration |
| Add/modify env vars | constants.py | All env vars loaded here |
| Database operations | db.py | TinyDB for beets candidates |
| Auth logic | main.py:authenticate() | Authentik headers or no-auth mode |
| Frontend changes | static/index.html | Alpine.js app, single file |
| Beets import logic | beetsapi.py | Custom ImportSession subclass |

## CODE MAP

### Entry Points
- `main.py` - FastAPI app (`uvicorn main:app`)
- `abb.py` - Legacy CLI script (in .gitignore, not production)

### Core Classes
| Symbol | Location | Purpose |
|--------|----------|---------|
| `TorrentClientInterface` | torrent.py:18 | Abstract base for torrent clients |
| `TransmissionClient` | torrent.py:61 | Transmission RPC implementation |
| `DecypharrClient` | torrent.py:396 | Decypharr API implementation |
| `TorrentService` | torrent_service.py:14 | Service layer singleton |
| `ProgrammaticImportSession` | beetsapi.py:21 | Custom beets importer |

### Key Functions
| Function | Location | Purpose |
|----------|----------|---------|
| `authenticate` | main.py:78 | Auth dispatcher (authentik/none) |
| `search_audiobook` | audiobookbay.py:20 | Jackett API search |
| `autoimport` | beetsapi.py:147 | Process completed torrents |
| `create_torrent_client` | torrent.py:588 | Factory for client instances |

## CONVENTIONS

- **Auth modes**: Only `authentik` and `none` supported. Local auth removed.
- **Torrent labels**: All torrents tagged with `LABEL` env var (default: "audiobook")
- **User tracking**: Transmission torrents tagged with `username:{user}` and user ID
- **Beets labels**: `beets` (complete), `beetserror` (needs manual selection)
- **Logging**: Use `custom_logger(__name__)` from utils.py

## ANTI-PATTERNS

- **DO NOT** add local/database authentication - removed intentionally
- **DO NOT** use `abb.py` - legacy CLI, ignored by git
- **NEVER** hardcode API keys - use constants.py env loading
- **AVOID** direct TorrentClient instantiation - use torrent_service functions

## TESTING / LOCAL DEV

- **Do all test runs in `/tmp`** (e.g. `/tmp/abb-test/`) and keep the repo root clean.
- Do **not** commit generated configs, downloads, or container state directories (qBittorrent/Jackett configs, downloads, etc.).

## COMMANDS

```bash
# Development
make venv              # Create virtualenv
make requirements      # Install deps
make run               # Start dev server (port 9000)

# Docker
make build             # Build Docker image
docker-compose -f docker-compose.full.yml up -d  # Full stack

# Environment
cp secrets/dev.env.sample secrets/dev.env  # Then edit with real values
```

## NOTES

- **Secrets**: `secrets/dev.env` is git-crypt encrypted. CI uses `GIT_CRYPT_KEY` secret.
- **Beets integration**: Works with Transmission and qBittorrent (`USE_BEETS_IMPORT=true`). Not supported with Decypharr (no label/file APIs).
- **Decypharr limitations**: pause/resume/labels not implemented - returns False/warning
- **Frontend**: Single-page Alpine.js app, no build step. CDN dependencies.
- **Session**: Uses Starlette `SessionMiddleware` with `SESSION_KEY` env var
- **Torrent deletion policy**: Auto-delete after `DELETE_AFTER_DAYS` (ratio >1.0) or `STRICTLY_DELETE_AFTER_DAYS` (forced)
