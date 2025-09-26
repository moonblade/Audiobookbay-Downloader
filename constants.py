import os

JACKETT_API_URL = os.getenv("JACKETT_API_URL" "")
JACKETT_API_KEY = os.getenv("JACKETT_API_KEY", "")

# Torrent client configuration
TORRENT_CLIENT_TYPE = os.getenv("TORRENT_CLIENT_TYPE", "transmission")  # transmission, decypharr
TRANSMISSION_URL = os.getenv("TRANSMISSION_URL", "")
TRANSMISSION_USER = os.getenv("TRANSMISSION_USER", "")
TRANSMISSION_PASS = os.getenv("TRANSMISSION_PASS", "")
DECYPHARR_URL = os.getenv("DECYPHARR_URL", "")
DECYPHARR_API_KEY = os.getenv("DECYPHARR_API_KEY", "")

LABEL = os.getenv("LABEL", "audiobook")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "YWRtaW4=")
ADMIN_ID = os.getenv("ADMIN_ID", "e0617896-4560-193c-cc34-653683f99c35")
DB_PATH = os.getenv("DB_PATH", "/tmp")
# DB_PATH/users.json returns a json of type [{"username": "user1", "password": "cGFzc3dvcmQ=", "role": "user", "id": "userapikey"}]

DELETE_AFTER_DAYS = int(os.getenv("DELETE_AFTER_DAYS", 14))
STRICTLY_DELETE_AFTER_DAYS = int(os.getenv("STRICTLY_DELETE_AFTER_DAYS", 30))

# Beets
BEETS_DIR = os.getenv("BEETSDIR", "/config")
BEETS_INPUT_PATH = os.getenv("BEETS_INPUT_PATH", "/beetsinput")
BEETS_COMPLETE_LABEL = os.getenv("BEETS_COMPLETE_LABEL", "beets")
USE_BEETS_IMPORT = os.getenv("USE_BEETS_IMPORT", "false").lower() == "true" and TORRENT_CLIENT_TYPE == "transmission"        
BEETS_ERROR_LABEL = os.getenv("BEETS_ERROR_LABEL", "beetserror")
ADMIN_USER_DICT = {"role": "admin"}
