import os
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import re

from utils import custom_logger

logger = custom_logger(__name__)
JACKETT_API_URL = os.getenv("JACKETT_API_URL" "")
JACKETT_API_KEY = os.getenv("JACKETT_API_KEY", "")


def search_audiobook(query):
    params = {
        "apikey": JACKETT_API_KEY,
        "Query": query,
        "Category": "audiobooks"
    }
    logger.info(f"Searching for {query}...")
    response = requests.get(str(JACKETT_API_URL), params=params)
    if response.status_code != 200:
        logger.error("Error fetching results from Jackett:", response.text)
        return []
    results = response.json()
    logger.info(f"Found {len(results.get('Results', []))} results for {query}")
    return results.get("Results", [])
