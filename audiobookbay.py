import requests
from constants import JACKETT_API_KEY, JACKETT_API_URL
from utils import custom_logger

logger = custom_logger(__name__)

def get_jackett_magnet(url):
    """Convert URL to magnet link if needed"""
    try:
        if url.startswith("magnet:"):
            return url
        response = requests.get(url, allow_redirects=False)
        if response.status_code in [301, 302]:
            return response.headers.get("Location", url)
    except Exception as e:
        logger.error(f"Error fetching magnet URL: {e}")
        return url
    return url

def search_audiobook(query):
    """Search for audiobooks using Jackett API"""
    params = {
        "apikey": JACKETT_API_KEY,
        "Query": query,
        "Category": "audiobooks"
    }
    logger.info(f"Searching for {query}...")

    try:
        response = requests.get(str(JACKETT_API_URL), params=params)
        if response.status_code != 200:
            logger.error("Error fetching results from Jackett:", response.text)
            return []

        results = response.json()
        logger.info(f"Found {len(results.get('Results', []))} results for {query}")
        return results.get("Results", [])
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []

