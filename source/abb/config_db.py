import os
from typing import Any, Dict, Optional
from tinydb import TinyDB, Query

_config_db: Optional[TinyDB] = None
CONFIG_DOC_TYPE = "app_config"

def _get_db() -> TinyDB:
    """Lazy initialization of config database."""
    global _config_db
    if _config_db is None:
        db_path = os.getenv("DB_PATH", "/tmp")
        _config_db = TinyDB(os.path.join(db_path, "app_config.json"))
    return _config_db


def get_config(key: str, default: Any = None) -> Any:
    """Get a config value from DB, returns default if not found."""
    db = _get_db()
    q = Query()
    entry = db.get((q.doc_type == CONFIG_DOC_TYPE) & (q.key == key))
    if entry:
        return entry.get("value", default)
    return default


def set_config(key: str, value: Any) -> None:
    """Set a config value in DB."""
    db = _get_db()
    q = Query()
    existing = db.get((q.doc_type == CONFIG_DOC_TYPE) & (q.key == key))
    if existing:
        db.update({"value": value}, (q.doc_type == CONFIG_DOC_TYPE) & (q.key == key))
    else:
        db.insert({"doc_type": CONFIG_DOC_TYPE, "key": key, "value": value})


def get_all_configs() -> Dict[str, Any]:
    """Get all config values from DB as a dictionary."""
    db = _get_db()
    q = Query()
    entries = db.search(q.doc_type == CONFIG_DOC_TYPE)
    return {entry["key"]: entry["value"] for entry in entries}


def delete_config(key: str) -> bool:
    """Delete a config value from DB. Returns True if deleted."""
    db = _get_db()
    q = Query()
    removed = db.remove((q.doc_type == CONFIG_DOC_TYPE) & (q.key == key))
    return len(removed) > 0


def get_config_with_env_fallback(key: str, env_var: str, default: Any = None, type_cast: type = str) -> Any:
    """Get config value with priority: DB > env var > default."""
    db_value = get_config(key)
    if db_value is not None:
        return db_value
    
    env_value = os.getenv(env_var)
    if env_value is not None:
        if type_cast == bool:
            return env_value.lower() == "true"
        elif type_cast == int:
            try:
                return int(env_value)
            except ValueError:
                return default
        return env_value
    
    return default


CONFIG_SCHEMA = {
    "jackett_api_url": {"env": "JACKETT_API_URL", "default": "", "type": str, "label": "Jackett API URL", "group": "jackett", "sensitive": False},
    "jackett_api_key": {"env": "JACKETT_API_KEY", "default": "", "type": str, "label": "Jackett API Key", "group": "jackett", "sensitive": True},
    
    "torrent_client_type": {"env": "TORRENT_CLIENT_TYPE", "default": "transmission", "type": str, "label": "Torrent Client Type", "group": "torrent", "sensitive": False, "options": ["transmission", "qbittorrent", "decypharr"]},
    
    "transmission_url": {"env": "TRANSMISSION_URL", "default": "", "type": str, "label": "Transmission URL", "group": "transmission", "sensitive": False},
    "transmission_user": {"env": "TRANSMISSION_USER", "default": "", "type": str, "label": "Transmission Username", "group": "transmission", "sensitive": False},
    "transmission_pass": {"env": "TRANSMISSION_PASS", "default": "", "type": str, "label": "Transmission Password", "group": "transmission", "sensitive": True},
    
    "qbittorrent_url": {"env": "QBITTORRENT_URL", "default": "", "type": str, "label": "qBittorrent URL", "group": "qbittorrent", "sensitive": False},
    "qbittorrent_username": {"env": "QBITTORRENT_USERNAME", "default": "", "type": str, "label": "qBittorrent Username", "group": "qbittorrent", "sensitive": False},
    "qbittorrent_password": {"env": "QBITTORRENT_PASSWORD", "default": "", "type": str, "label": "qBittorrent Password", "group": "qbittorrent", "sensitive": True},
    "qbittorrent_category": {"env": "QBITTORRENT_CATEGORY", "default": "", "type": str, "label": "qBittorrent Category", "group": "qbittorrent", "sensitive": False},
    
    "decypharr_url": {"env": "DECYPHARR_URL", "default": "", "type": str, "label": "Decypharr URL", "group": "decypharr", "sensitive": False},
    "decypharr_api_key": {"env": "DECYPHARR_API_KEY", "default": "", "type": str, "label": "Decypharr API Key", "group": "decypharr", "sensitive": True},
    
    "label": {"env": "LABEL", "default": "audiobook", "type": str, "label": "Torrent Label", "group": "torrent", "sensitive": False},
    "delete_after_days": {"env": "DELETE_AFTER_DAYS", "default": 14, "type": int, "label": "Delete After Days", "group": "cleanup", "sensitive": False},
    "strictly_delete_after_days": {"env": "STRICTLY_DELETE_AFTER_DAYS", "default": 30, "type": int, "label": "Force Delete After Days", "group": "cleanup", "sensitive": False},
    
    "use_beets_import": {"env": "USE_BEETS_IMPORT", "default": False, "type": bool, "label": "Enable Beets Import", "group": "beets", "sensitive": False},
    "beets_input_path": {"env": "BEETS_INPUT_PATH", "default": "/beetsinput", "type": str, "label": "Beets Input Path", "group": "beets", "sensitive": False},
    
    "goodreads_enabled": {"env": "GOODREADS_ENABLED", "default": False, "type": bool, "label": "Enable Goodreads", "group": "goodreads", "sensitive": False},
    
    "title": {"env": "TITLE", "default": "Audiobook Search", "type": str, "label": "App Title", "group": "app", "sensitive": False},
}


def get_effective_config(key: str) -> Any:
    """Get the effective value for a config key using DB > env > default priority."""
    if key not in CONFIG_SCHEMA:
        return None
    
    schema = CONFIG_SCHEMA[key]
    return get_config_with_env_fallback(
        key=key,
        env_var=schema["env"],
        default=schema["default"],
        type_cast=schema["type"]
    )


def get_all_effective_configs() -> Dict[str, Any]:
    """Get all effective config values."""
    return {key: get_effective_config(key) for key in CONFIG_SCHEMA}


def get_config_schema() -> Dict[str, Any]:
    """Get the config schema for UI rendering."""
    return CONFIG_SCHEMA
