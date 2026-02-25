import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from .constants import DB_PATH
from tinydb import TinyDB, Query

# Database for Goodreads configuration and processed books
goodreadsdb = TinyDB(os.path.join(DB_PATH, "goodreads.json"))

# Config table stores: user_id, shelf, poll_interval, enabled, last_poll
# Processed table stores: book_id, title, author, added_date, downloaded_date, torrent_id, status

CONFIG_DOC_ID = "config"


def get_config() -> Dict[str, Any]:
    """Get Goodreads configuration from database."""
    entry = goodreadsdb.get(Query().doc_type == CONFIG_DOC_ID)
    if entry:
        return {
            "user_id": entry.get("user_id", ""),
            "shelf": entry.get("shelf", "to-read"),
            "poll_interval": entry.get("poll_interval", 60),
            "enabled": entry.get("enabled", False),
            "last_poll": entry.get("last_poll"),
            "last_poll_status": entry.get("last_poll_status"),
            "last_poll_message": entry.get("last_poll_message"),
        }
    return {
        "user_id": "",
        "shelf": "to-read",
        "poll_interval": 60,
        "enabled": False,
        "last_poll": None,
        "last_poll_status": None,
        "last_poll_message": None,
    }


def save_config(
    user_id: str,
    shelf: str = "to-read",
    poll_interval: int = 60,
    enabled: bool = False
) -> Dict[str, Any]:
    """Save Goodreads configuration to database."""
    config_data = {
        "doc_type": CONFIG_DOC_ID,
        "user_id": user_id,
        "shelf": shelf,
        "poll_interval": poll_interval,
        "enabled": enabled,
    }
    
    existing = goodreadsdb.get(Query().doc_type == CONFIG_DOC_ID)
    if existing:
        # Preserve last_poll info when updating config
        config_data["last_poll"] = existing.get("last_poll")
        config_data["last_poll_status"] = existing.get("last_poll_status")
        config_data["last_poll_message"] = existing.get("last_poll_message")
        goodreadsdb.update(config_data, Query().doc_type == CONFIG_DOC_ID)
    else:
        goodreadsdb.insert(config_data)
    
    return get_config()


def update_poll_status(status: str, message: str = "") -> None:
    """Update the last poll status."""
    goodreadsdb.update(
        {
            "last_poll": datetime.utcnow().isoformat(),
            "last_poll_status": status,
            "last_poll_message": message,
        },
        Query().doc_type == CONFIG_DOC_ID
    )


def get_processed_book(book_id: str) -> Optional[Dict[str, Any]]:
    """Get a processed book by its Goodreads book ID."""
    return goodreadsdb.get(Query().book_id == book_id)


def get_all_processed_books() -> List[Dict[str, Any]]:
    """Get all processed books."""
    return goodreadsdb.search(Query().doc_type == "processed_book")


def add_processed_book(
    book_id: str,
    title: str,
    author: str,
    status: str = "downloaded",
    torrent_name: str = "",
    error_message: str = ""
) -> Dict[str, Any]:
    """Add a book to the processed list."""
    book_data = {
        "doc_type": "processed_book",
        "book_id": book_id,
        "title": title,
        "author": author,
        "added_date": datetime.utcnow().isoformat(),
        "status": status,  # "downloaded", "no_results", "error"
        "torrent_name": torrent_name,
        "error_message": error_message,
    }
    
    existing = get_processed_book(book_id)
    if existing:
        goodreadsdb.update(book_data, Query().book_id == book_id)
    else:
        goodreadsdb.insert(book_data)
    
    return book_data


def delete_processed_book(book_id: str) -> bool:
    """Delete a processed book (allows re-download)."""
    removed = goodreadsdb.remove(Query().book_id == book_id)
    return len(removed) > 0


def clear_all_processed_books() -> int:
    """Clear all processed books (allows re-downloading everything)."""
    removed = goodreadsdb.remove(Query().doc_type == "processed_book")
    return len(removed)
