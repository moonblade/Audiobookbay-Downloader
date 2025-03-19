import os

BEETS_DIR = os.getenv("BEETSDIR", "/config")
BEETS_INPUT_PATH = os.getenv("BEETS_INPUT_PATH", "/beetsinput")
BEETS_COMPLETE_LABEL = os.getenv("BEETS_COMPLETE_LABEL", "beets")
BEETS_ERROR_LABEL = os.getenv("BEETS_ERROR_LABEL", "beetserror")
ADMIN_USER = {"role": "admin"}

JACKETT_API_URL = os.getenv("JACKETT_API_URL" "")
JACKETT_API_KEY = os.getenv("JACKETT_API_KEY", "")
TRANSMISSION_URL = os.getenv("TRANSMISSION_URL", "")
TRANSMISSION_USER = os.getenv("TRANSMISSION_USER", "")
TRANSMISSION_PASS = os.getenv("TRANSMISSION_PASS", "")
LABEL = os.getenv("LABEL", "audiobook")

