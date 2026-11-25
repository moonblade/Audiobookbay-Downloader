import requests
from typing import Optional, List
from .constants import JACKETT_API_KEY, JACKETT_API_URL
from .utils import custom_logger
import xml.etree.ElementTree as ET

logger = custom_logger(__name__)

def get_jackett_magnet(url):
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

def get_jackett_indexers(api_url: Optional[str] = None, api_key: Optional[str] = None) -> List[str]:
    """Return list of configured Jackett indexer names."""
    url = api_url or JACKETT_API_URL
    key = api_key or JACKETT_API_KEY
    torznab_url = str(url).rstrip("/").replace("/api/v2.0/indexers/all/results", "") + "/api/v2.0/indexers/all/results/torznab/api"
    params = {
        "apikey": key,
        "t": "indexers",
        "configured": "true"
    }
    try:
        response = requests.get(torznab_url, params=params)
        if response.status_code != 200:
            logger.error(f"Error fetching indexers from Jackett: {response.text}")
            return []
        root = ET.fromstring(response.text)
        indexers = []
        for indexer in root.findall(".//indexer"):
            title_el = indexer.find("title")
            if title_el is not None and title_el.text:
                indexers.append(title_el.text)
        logger.info(f"Found {len(indexers)} configured indexers")
        return sorted(indexers)
    except Exception as e:
        logger.error(f"Failed to fetch indexers: {e}")
        return []


def search_audiobook(query, api_url: Optional[str] = None, api_key: Optional[str] = None, tracker: Optional[str] = None):
    url = api_url or JACKETT_API_URL
    key = api_key or JACKETT_API_KEY
    
    params = {
        "apikey": key,
        "Query": query,
        "Category": "audiobooks"
    }
    logger.info(f"Searching for {query}...")

    try:
        response = requests.get(str(url), params=params)
        if response.status_code != 200:
            logger.error("Error fetching results from Jackett:", response.text)
            return []

        results = response.json()
        all_results = results.get("Results", [])
        if tracker:
            all_results = [r for r in all_results if r.get("Tracker", "") == tracker]
        logger.info(f"Found {len(all_results)} results for {query}" + (f" (tracker: {tracker})" if tracker else ""))
        return all_results
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []
