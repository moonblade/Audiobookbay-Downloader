import feedparser
from typing import List, Dict, Any, Optional
from audiobookbay import search_audiobook
from torrent_service import add_torrent
from models import User
from goodreads_db import (
    get_config, save_config, update_poll_status,
    get_processed_book, add_processed_book, get_all_processed_books
)
from utils import custom_logger

logger = custom_logger(__name__)

GOODREADS_RSS_URL = "https://www.goodreads.com/review/list_rss/{user_id}?shelf={shelf}"


def build_rss_url(user_id: str, shelf: str) -> str:
    return GOODREADS_RSS_URL.format(user_id=user_id, shelf=shelf)


def fetch_goodreads_shelf(user_id: str, shelf: str) -> List[Dict[str, Any]]:
    url = build_rss_url(user_id, shelf)
    logger.info(f"Fetching Goodreads RSS: {url}")
    
    try:
        feed = feedparser.parse(url)
        
        if feed.bozo:
            logger.error(f"RSS parse error: {feed.bozo_exception}")
            return []
        
        books = []
        for entry in feed.entries:
            book = {
                "book_id": entry.get("book_id", ""),
                "title": entry.get("title", ""),
                "author": entry.get("author_name", ""),
                "isbn": entry.get("isbn", ""),
                "image_url": entry.get("book_image_url", ""),
                "date_added": entry.get("user_date_added", ""),
            }
            books.append(book)
        
        logger.info(f"Found {len(books)} books on shelf '{shelf}'")
        return books
        
    except Exception as e:
        logger.error(f"Failed to fetch Goodreads RSS: {e}")
        return []


def download_best_match(title: str, user: User) -> Optional[Dict[str, Any]]:
    results = search_audiobook(title)
    
    if not results:
        logger.info(f"No results found for: {title}")
        return None
    
    best_match = results[0]
    torrent_url = best_match.get("MagnetUri") or best_match.get("Link")
    
    if not torrent_url:
        logger.error(f"No torrent URL found for: {title}")
        return None
    
    logger.info(f"Downloading best match for '{title}': {best_match.get('Title')}")
    
    try:
        success = add_torrent(torrent_url, user)
        if success:
            return {
                "title": best_match.get("Title"),
                "size": best_match.get("Size"),
                "url": torrent_url
            }
    except Exception as e:
        logger.error(f"Failed to add torrent for '{title}': {e}")
    
    return None


def poll_and_download() -> Dict[str, Any]:
    config = get_config()
    
    if not config.get("enabled"):
        logger.info("Goodreads polling is disabled")
        return {"status": "disabled", "message": "Polling is disabled"}
    
    user_id = config.get("user_id")
    shelf = config.get("shelf", "to-read")
    
    if not user_id:
        logger.warning("Goodreads user_id not configured")
        update_poll_status("error", "User ID not configured")
        return {"status": "error", "message": "User ID not configured"}
    
    logger.info(f"Starting Goodreads poll for user {user_id}, shelf '{shelf}'")
    
    try:
        books = fetch_goodreads_shelf(user_id, shelf)
        
        if not books:
            update_poll_status("success", "No books found on shelf")
            return {"status": "success", "message": "No books on shelf", "processed": 0}
        
        system_user = User(username="goodreads", role="admin", id="goodreads-auto")
        
        new_downloads = 0
        skipped = 0
        no_results = 0
        errors = 0
        
        for book in books:
            book_id = book.get("book_id")
            title = book.get("title")
            author = book.get("author", "")
            
            if not book_id or not title:
                continue
            
            existing = get_processed_book(book_id)
            if existing:
                skipped += 1
                continue
            
            result = download_best_match(title, system_user)
            
            if result:
                add_processed_book(
                    book_id=book_id,
                    title=title,
                    author=author,
                    status="downloaded",
                    torrent_name=result.get("title", "")
                )
                new_downloads += 1
            else:
                add_processed_book(
                    book_id=book_id,
                    title=title,
                    author=author,
                    status="no_results"
                )
                no_results += 1
        
        message = f"Downloaded: {new_downloads}, No results: {no_results}, Skipped: {skipped}"
        update_poll_status("success", message)
        logger.info(f"Poll complete: {message}")
        
        return {
            "status": "success",
            "message": message,
            "new_downloads": new_downloads,
            "no_results": no_results,
            "skipped": skipped
        }
        
    except Exception as e:
        error_msg = f"Poll failed: {str(e)}"
        logger.error(error_msg)
        update_poll_status("error", error_msg)
        return {"status": "error", "message": error_msg}


def validate_goodreads_config(user_id: str, shelf: str) -> Dict[str, Any]:
    if not user_id:
        return {"valid": False, "message": "User ID is required"}
    
    books = fetch_goodreads_shelf(user_id, shelf)
    
    if books:
        return {
            "valid": True,
            "message": f"Found {len(books)} books on shelf '{shelf}'",
            "book_count": len(books)
        }
    else:
        return {
            "valid": False,
            "message": f"Could not fetch books. Check user ID ({user_id}) and shelf name ({shelf})"
        }
