import os

from .models import User
from .config_db import get_effective_config

DB_PATH = os.getenv("DB_PATH", "/tmp")

JACKETT_API_URL = get_effective_config("jackett_api_url")
JACKETT_API_KEY = get_effective_config("jackett_api_key")

TORRENT_CLIENT_TYPE = get_effective_config("torrent_client_type")
TRANSMISSION_URL = get_effective_config("transmission_url")
TRANSMISSION_USER = get_effective_config("transmission_user")
TRANSMISSION_PASS = get_effective_config("transmission_pass")
DECYPHARR_URL = get_effective_config("decypharr_url")
DECYPHARR_API_KEY = get_effective_config("decypharr_api_key")
QBITTORRENT_URL = get_effective_config("qbittorrent_url")
QBITTORRENT_USERNAME = get_effective_config("qbittorrent_username")
QBITTORRENT_PASSWORD = get_effective_config("qbittorrent_password")
QBITTORRENT_CATEGORY = get_effective_config("qbittorrent_category")

LABEL = get_effective_config("label")

# Internal admin user for background operations (beets, auto-delete)
ADMIN_USER_DICT = User(username="admin", role="admin", id="admin")

DELETE_AFTER_DAYS = get_effective_config("delete_after_days")
STRICTLY_DELETE_AFTER_DAYS = get_effective_config("strictly_delete_after_days")

BEETS_DIR = os.getenv("BEETSDIR", "/config")
BEETS_INPUT_PATH = get_effective_config("beets_input_path")
BEETS_COMPLETE_LABEL = os.getenv("BEETS_COMPLETE_LABEL", "beets")
USE_BEETS_IMPORT = get_effective_config("use_beets_import") and TORRENT_CLIENT_TYPE != "decypharr"
BEETS_ERROR_LABEL = os.getenv("BEETS_ERROR_LABEL", "beetserror")

SESSION_KEY = os.getenv("SESSION_KEY", "cp5oLmSZozoLZWHq")
TITLE = get_effective_config("title")
AUTH_MODE = os.getenv("AUTH_MODE", "none")

GOODREADS_ENABLED = get_effective_config("goodreads_enabled")
