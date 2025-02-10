import os
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import re

from utils import custom_logger

logger = custom_logger(__name__)
JACKETT_API_URL = os.getenv("JACKETT_API_URL" "")
JACKETT_API_KEY = os.getenv("JACKETT_API_KEY", "")
TRANSMISSION_URL = os.getenv("TRANSMISSION_URL", "")
TRANSMISSION_USER = os.getenv("TRANSMISSION_USER", "")
TRANSMISSION_PASS = os.getenv("TRANSMISSION_PASS", "")

def get_jackett_magnet(url):
    response = requests.get(url, allow_redirects=False)
    if response.status_code in [301, 302]:
        return response.headers.get("Location", url)
    return url

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

def add_to_transmission(torrent_url):
    torrent_url = get_jackett_magnet(torrent_url)
    session_response = requests.get(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS))
    session_id = session_response.headers.get("X-Transmission-Session-Id")
    
    if not session_id:
        print("Failed to get Transmission session ID")
        return False
    
    payload = {
        "method": "torrent-add",
        "arguments": {"filename": torrent_url}
    }
    headers = {"X-Transmission-Session-Id": session_id}
    
    response = requests.post(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS), json=payload, headers=headers)
    return response.status_code == 200

