import requests
from constants import JACKETT_API_KEY  #, JACKETT_API_URLS  # expect JACKETT_API_URLS to be a list
from utils import custom_logger
import os

logger = custom_logger(__name__)



def get_jackett_urls():
    urls = []
    for key, value in os.environ.items():
        if key.startswith("JACKETT_API_URL"):
            urls.append(value)
    # sort for consistency (important if ordering matters)
    urls.sort()
    return urls

JACKETT_API_URLS = get_jackett_urls()



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
    """
    Search for audiobooks using multiple Jackett API URLs.
    Combine and deduplicate results.
    """
    params = {
        "apikey": JACKETT_API_KEY,
        "Query": query,
        "Category": "audiobooks"
    }
    all_results = []
    seen_ids = set()

    # Ensure JACKETT_API_URLS is a list, e.g. [JACKETT_API_URL, JACKETT_API_URL1, ...]
    for url in JACKETT_API_URLS:
        logger.info(f"Searching for {query} on {url}...")
        try:
            response = requests.get(str(url), params=params)
            if response.status_code != 200:
                logger.error(f"Error fetching results from {url}: {response.text}")
                continue

            results = response.json()
            for item in results.get("Results", []):
                # Deduplicate by Jackett's 'Guid' field, adjust if needed
                result_id = item.get("Guid") or item.get("Title")
                if result_id and result_id not in seen_ids:
                    all_results.append(item)
                    seen_ids.add(result_id)
        except Exception as e:
            logger.error(f"Search failed for {url}: {e}")
            continue

    logger.info(f"Found {len(all_results)} total results for {query} across all Jackett servers")
    return all_results
