import feedparser
import re
import json
import requests
from typing import List, Dict, Any, Optional, Tuple
from .audiobookbay import search_audiobook
from .torrent_service import add_torrent
from .models import User
from .goodreads_db import (
    get_config, update_poll_status,
    get_processed_book, add_processed_book,
    get_enabled_configs
)
from .utils import custom_logger
from .constants import OLLAMA_URL, OLLAMA_MODEL

logger = custom_logger(__name__)

GOODREADS_RSS_URL = "https://www.goodreads.com/review/list_rss/{user_id}?shelf={shelf}&sort=date_added&order=d&per_page=200&page={page}"


def build_rss_url(user_id: str, shelf: str, page: int = 1) -> str:
    return GOODREADS_RSS_URL.format(user_id=user_id, shelf=shelf, page=page)


def fetch_goodreads_shelf(goodreads_user_id: str, shelf: str, max_pages: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch all books from a Goodreads shelf with pagination.
    Returns books sorted by date_added descending (latest first).
    """
    all_books = []
    page = 1
    
    while page <= max_pages:
        url = build_rss_url(goodreads_user_id, shelf, page)
        logger.info(f"Fetching Goodreads RSS page {page}: {url}")
        
        try:
            feed = feedparser.parse(url)
            
            if feed.bozo:
                logger.error(f"RSS parse error on page {page}: {feed.bozo_exception}")
                break
            
            if not feed.entries:
                logger.info(f"No more entries on page {page}, stopping pagination")
                break
            
            for entry in feed.entries:
                book = {
                    "book_id": entry.get("book_id", ""),
                    "title": entry.get("title", ""),
                    "author": entry.get("author_name", ""),
                    "isbn": entry.get("isbn", ""),
                    "image_url": entry.get("book_image_url", ""),
                    "date_added": entry.get("user_date_added", ""),
                }
                all_books.append(book)
            
            logger.info(f"Page {page}: fetched {len(feed.entries)} books (total: {len(all_books)})")
            
            if len(feed.entries) < 200:
                break
            
            page += 1
            
        except Exception as e:
            logger.error(f"Failed to fetch Goodreads RSS page {page}: {e}")
            break
    
    logger.info(f"Total books fetched from shelf '{shelf}': {len(all_books)}")
    return all_books


def _strip_series(title: str) -> str:
    """Remove trailing series info like '(Old Man's War, #1)' from a title."""
    # Remove anything in parentheses at the end that looks like series info
    return re.sub(r'\s*\([^)]*#\d+[^)]*\)\s*$', '', title).strip()


def build_search_queries(title: str, author: str) -> List[str]:
    """
    Build a list of search queries to try in order.
    AudiobookBay responds better to some combinations than others.
    Strategy: prefer specific (title+author) over broad (author-only).
    """
    raw_title = title.strip()
    clean_title = _strip_series(raw_title)  # e.g. strip '(Old Man's War, #1)'
    clean_author = author.strip()

    queries = []

    # 1. Clean title + author (most specific, no series noise)
    if clean_author and clean_title != raw_title:
        queries.append(f"{clean_title} {clean_author}")

    # 2. Raw title + author
    if clean_author:
        queries.append(f"{raw_title} {clean_author}")

    # 3. Clean title only
    if clean_title not in queries:
        queries.append(clean_title)

    # 4. Raw title only (if different from clean)
    if raw_title != clean_title and raw_title not in queries:
        queries.append(raw_title)

    # 5. First 4 words of clean title + author (strips subtitles like "A Novel", ":")
    title_words = clean_title.split()
    if len(title_words) > 4 and clean_author:
        short_with_author = f"{' '.join(title_words[:4])} {clean_author}"
        if short_with_author not in queries:
            queries.append(short_with_author)

    # 6. First 4 words of clean title alone
    if len(title_words) > 4:
        short_title = " ".join(title_words[:4])
        if short_title not in queries:
            queries.append(short_title)

    # 7. Author only — last resort, least specific
    if clean_author and clean_author not in queries:
        queries.append(clean_author)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)
    return unique


def get_llm_search_queries(title: str, author: str) -> List[str]:
    """
    Ask the local LLM for alternative AudiobookBay search terms when
    standard queries have already failed.
    Returns a list of new query strings to try (may be empty on failure).
    """
    prompt = (
        f'I am searching for the audiobook "{title}" by "{author}" on AudiobookBay '
        f'but all my search attempts have failed. '
        f'Suggest up to 5 alternative short search queries I could try — '
        f'for example: a shorter title, an alternate title, the author name alone, '
        f'series name, or common alternate spellings. '
        f'Reply with ONLY a JSON array of strings, no explanation. Example: ["query1", "query2"]'
    )
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.2},
            },
            timeout=30,
        )
        if response.status_code != 200:
            logger.warning(f"LLM returned HTTP {response.status_code} for '{title}'")
            return []
        content = response.json().get("message", {}).get("content", "")
        # Extract JSON array from response (LLM may wrap it in markdown)
        match = re.search(r'\[.*?\]', content, re.DOTALL)
        if not match:
            logger.warning(f"LLM response had no JSON array for '{title}': {content[:200]}")
            return []
        queries = json.loads(match.group())
        if not isinstance(queries, list):
            return []
        queries = [str(q).strip() for q in queries if str(q).strip()]
        logger.info(f"LLM suggested {len(queries)} alternative queries for '{title}': {queries}")
        return queries
    except Exception as e:
        logger.warning(f"LLM query failed for '{title}': {e}")
        return []


def _try_queries(queries: List[str], title: str, user: User) -> Optional[Dict[str, Any]]:
    """Try a list of search queries in order; return on first successful torrent add."""
    for query in queries:
        results = search_audiobook(query)
        if not results:
            logger.info(f"Query '{query}' returned no results")
            continue
        logger.info(f"Query '{query}' returned {len(results)} results")
        best_match = results[0]
        torrent_url = best_match.get("MagnetUri") or best_match.get("Link")
        if not torrent_url:
            logger.warning(f"No torrent URL in first result for query '{query}', skipping")
            continue
        logger.info(f"Downloading best match for '{title}' via query '{query}': {best_match.get('Title')}")
        try:
            success = add_torrent(torrent_url, user)
            if success:
                return {
                    "title": best_match.get("Title"),
                    "size": best_match.get("Size"),
                    "url": torrent_url
                }
        except Exception as e:
            logger.error(f"Failed to add torrent for '{title}' (query: '{query}'): {e}")
    return None


def download_best_match(title: str, user: User, author: str = "") -> Optional[Dict[str, Any]]:
    queries = build_search_queries(title, author)
    logger.info(f"Trying {len(queries)} standard queries for '{title}' by '{author}': {queries}")

    result = _try_queries(queries, title, user)
    if result:
        return result

    # All standard queries exhausted — ask LLM for alternatives
    logger.info(f"Standard queries exhausted for '{title}' — asking LLM for alternatives")
    llm_queries = get_llm_search_queries(title, author)
    if llm_queries:
        result = _try_queries(llm_queries, title, user)
        if result:
            return result

    logger.info(f"All queries (standard + LLM) exhausted for '{title}' — no match found")
    return None


def poll_and_download_for_user(user_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Poll and download books for a specific user based on their config."""
    goodreads_user_id = config.get("goodreads_user_id")
    shelf = config.get("shelf", "to-read")
    
    if not goodreads_user_id:
        logger.warning(f"Goodreads user_id not configured for user {user_id}")
        update_poll_status(user_id, "error", "Goodreads User ID not configured")
        return {"status": "error", "message": "Goodreads User ID not configured", "user_id": user_id}
    
    logger.info(f"Starting Goodreads poll for user {user_id}, goodreads_user_id {goodreads_user_id}, shelf '{shelf}'")
    
    try:
        books = fetch_goodreads_shelf(goodreads_user_id, shelf)
        
        if not books:
            update_poll_status(user_id, "success", "No books found on shelf")
            return {"status": "success", "message": "No books on shelf", "processed": 0, "user_id": user_id}
        
        torrent_user = User(username=f"goodreads-{user_id}", role="admin", id=user_id)
        
        new_downloads = 0
        skipped = 0
        no_results = 0
        
        for book in books:
            book_id = book.get("book_id")
            title = book.get("title")
            author = book.get("author", "")
            
            if not book_id or not title:
                continue
            
            existing = get_processed_book(user_id, book_id)
            if existing:
                skipped += 1
                continue
            
            result = download_best_match(title, torrent_user, author=author)
            
            if result:
                add_processed_book(
                    user_id=user_id,
                    book_id=book_id,
                    title=title,
                    author=author,
                    status="downloaded",
                    torrent_name=result.get("title", "")
                )
                new_downloads += 1
            else:
                add_processed_book(
                    user_id=user_id,
                    book_id=book_id,
                    title=title,
                    author=author,
                    status="no_results"
                )
                no_results += 1
        
        message = f"Downloaded: {new_downloads}, No results: {no_results}, Skipped: {skipped}"
        update_poll_status(user_id, "success", message)
        logger.info(f"Poll complete for user {user_id}: {message}")
        
        return {
            "status": "success",
            "message": message,
            "user_id": user_id,
            "new_downloads": new_downloads,
            "no_results": no_results,
            "skipped": skipped
        }
        
    except Exception as e:
        error_msg = f"Poll failed: {str(e)}"
        logger.error(f"Poll failed for user {user_id}: {error_msg}")
        update_poll_status(user_id, "error", error_msg)
        return {"status": "error", "message": error_msg, "user_id": user_id}


def poll_and_download() -> Dict[str, Any]:
    """Poll and download books for all enabled users."""
    enabled_configs = get_enabled_configs()
    
    if not enabled_configs:
        logger.info("No enabled Goodreads configurations found")
        return {"status": "disabled", "message": "No enabled configurations", "results": []}
    
    results = []
    total_downloads = 0
    total_errors = 0
    
    for config in enabled_configs:
        user_id = config.get("user_id")
        if not user_id:
            continue
            
        result = poll_and_download_for_user(user_id, config)
        results.append(result)
        
        if result.get("status") == "success":
            total_downloads += result.get("new_downloads", 0)
        else:
            total_errors += 1
    
    return {
        "status": "success",
        "message": f"Polled {len(results)} users, {total_downloads} new downloads, {total_errors} errors",
        "results": results,
        "total_users": len(results),
        "total_downloads": total_downloads,
        "total_errors": total_errors
    }


def poll_and_download_single_user(user_id: str) -> Dict[str, Any]:
    """Poll and download books for a single specific user."""
    config = get_config(user_id)
    
    if not config.get("enabled"):
        logger.info(f"Goodreads polling is disabled for user {user_id}")
        return {"status": "disabled", "message": "Polling is disabled for this user", "user_id": user_id}
    
    return poll_and_download_for_user(user_id, config)


def validate_goodreads_config(goodreads_user_id: str, shelf: str) -> Dict[str, Any]:
    if not goodreads_user_id:
        return {"valid": False, "message": "Goodreads User ID is required"}
    
    books = fetch_goodreads_shelf(goodreads_user_id, shelf)
    
    if books:
        return {
            "valid": True,
            "message": f"Found {len(books)} books on shelf '{shelf}'",
            "book_count": len(books)
        }
    else:
        return {
            "valid": False,
            "message": f"Could not fetch books. Check Goodreads user ID ({goodreads_user_id}) and shelf name ({shelf})"
        }
