import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from .constants import DB_PATH
from tinydb import TinyDB, Query

# Database for Goodreads configuration and processed books
goodreadsdb = TinyDB(os.path.join(DB_PATH, "goodreads.json"))

# Config table stores: user_id, goodreads_user_id, shelf, poll_interval, enabled, last_poll
# Processed table stores: user_id, book_id, title, author, added_date, downloaded_date, torrent_id, status

CONFIG_DOC_TYPE = "config"
PROCESSED_DOC_TYPE = "processed_book"
MIGRATION_DOC_TYPE = "migration_status"


def migrate_legacy_data_for_user(user_id: str, is_admin: bool) -> None:
    if not is_admin:
        return
    
    q = Query()
    
    migration_record = goodreadsdb.get(q.doc_type == MIGRATION_DOC_TYPE)
    if migration_record and migration_record.get("completed"):
        return
    
    legacy_config = goodreadsdb.get((q.doc_type == CONFIG_DOC_TYPE) & (~q.user_id.exists()))
    misplaced_configs = goodreadsdb.search(
        (q.doc_type == CONFIG_DOC_TYPE) & 
        (q.user_id.exists()) & 
        (~q.goodreads_user_id.exists())
    )
    legacy_books = goodreadsdb.search((q.doc_type == PROCESSED_DOC_TYPE) & (~q.user_id.exists()))
    
    if legacy_config:
        goodreadsdb.update(
            {"user_id": user_id},
            (q.doc_type == CONFIG_DOC_TYPE) & (~q.user_id.exists())
        )
    
    for config in misplaced_configs:
        old_user_id = config.get("user_id", "")
        if old_user_id and old_user_id.isdigit():
            goodreadsdb.update(
                {"goodreads_user_id": old_user_id, "user_id": user_id},
                (q.doc_type == CONFIG_DOC_TYPE) & (q.user_id == old_user_id)
            )
    
    for book in legacy_books:
        goodreadsdb.update(
            {"user_id": user_id},
            (q.doc_type == PROCESSED_DOC_TYPE) & (q.book_id == book.get("book_id")) & (~q.user_id.exists())
        )
    
    if migration_record:
        goodreadsdb.update({"completed": True}, q.doc_type == MIGRATION_DOC_TYPE)
    else:
        goodreadsdb.insert({"doc_type": MIGRATION_DOC_TYPE, "completed": True})


def get_config(user_id: str) -> Dict[str, Any]:
    """Get Goodreads configuration for a specific user."""
    q = Query()
    entry = goodreadsdb.get((q.doc_type == CONFIG_DOC_TYPE) & (q.user_id == user_id))
    if entry:
        return {
            "user_id": entry.get("user_id", ""),
            "goodreads_user_id": entry.get("goodreads_user_id", ""),
            "shelf": entry.get("shelf", "to-read"),
            "poll_interval": entry.get("poll_interval", 60),
            "enabled": entry.get("enabled", False),
            "last_poll": entry.get("last_poll"),
            "last_poll_status": entry.get("last_poll_status"),
            "last_poll_message": entry.get("last_poll_message"),
        }
    return {
        "user_id": user_id,
        "goodreads_user_id": "",
        "shelf": "to-read",
        "poll_interval": 60,
        "enabled": False,
        "last_poll": None,
        "last_poll_status": None,
        "last_poll_message": None,
    }


def get_all_configs() -> List[Dict[str, Any]]:
    """Get all Goodreads configurations for all users."""
    q = Query()
    configs = goodreadsdb.search(q.doc_type == CONFIG_DOC_TYPE)
    return [
        {
            "user_id": entry.get("user_id", ""),
            "goodreads_user_id": entry.get("goodreads_user_id", ""),
            "shelf": entry.get("shelf", "to-read"),
            "poll_interval": entry.get("poll_interval", 60),
            "enabled": entry.get("enabled", False),
            "last_poll": entry.get("last_poll"),
            "last_poll_status": entry.get("last_poll_status"),
            "last_poll_message": entry.get("last_poll_message"),
        }
        for entry in configs
    ]


def get_enabled_configs() -> List[Dict[str, Any]]:
    """Get all enabled Goodreads configurations."""
    q = Query()
    configs = goodreadsdb.search((q.doc_type == CONFIG_DOC_TYPE) & (q.enabled == True))
    return [
        {
            "user_id": entry.get("user_id", ""),
            "goodreads_user_id": entry.get("goodreads_user_id", ""),
            "shelf": entry.get("shelf", "to-read"),
            "poll_interval": entry.get("poll_interval", 60),
            "enabled": entry.get("enabled", False),
            "last_poll": entry.get("last_poll"),
            "last_poll_status": entry.get("last_poll_status"),
            "last_poll_message": entry.get("last_poll_message"),
        }
        for entry in configs
    ]


def save_config(
    user_id: str,
    goodreads_user_id: str,
    shelf: str = "to-read",
    poll_interval: int = 60,
    enabled: bool = False
) -> Dict[str, Any]:
    """Save Goodreads configuration for a specific user."""
    q = Query()
    config_data = {
        "doc_type": CONFIG_DOC_TYPE,
        "user_id": user_id,
        "goodreads_user_id": goodreads_user_id,
        "shelf": shelf,
        "poll_interval": poll_interval,
        "enabled": enabled,
    }
    
    existing = goodreadsdb.get((q.doc_type == CONFIG_DOC_TYPE) & (q.user_id == user_id))
    if existing:
        config_data["last_poll"] = existing.get("last_poll")
        config_data["last_poll_status"] = existing.get("last_poll_status")
        config_data["last_poll_message"] = existing.get("last_poll_message")
        goodreadsdb.update(config_data, (q.doc_type == CONFIG_DOC_TYPE) & (q.user_id == user_id))
    else:
        goodreadsdb.insert(config_data)
    
    return get_config(user_id)


def update_poll_status(user_id: str, status: str, message: str = "") -> None:
    """Update the last poll status for a specific user."""
    q = Query()
    goodreadsdb.update(
        {
            "last_poll": datetime.utcnow().isoformat(),
            "last_poll_status": status,
            "last_poll_message": message,
        },
        (q.doc_type == CONFIG_DOC_TYPE) & (q.user_id == user_id)
    )


def get_processed_book(user_id: str, book_id: str) -> Optional[Dict[str, Any]]:
    """Get a processed book by its Goodreads book ID for a specific user."""
    q = Query()
    return goodreadsdb.get((q.user_id == user_id) & (q.book_id == book_id) & (q.doc_type == PROCESSED_DOC_TYPE))


def get_all_processed_books(user_id: str) -> List[Dict[str, Any]]:
    """Get all processed books for a specific user."""
    q = Query()
    return goodreadsdb.search((q.doc_type == PROCESSED_DOC_TYPE) & (q.user_id == user_id))


def add_processed_book(
    user_id: str,
    book_id: str,
    title: str,
    author: str,
    status: str = "downloaded",
    torrent_name: str = "",
    error_message: str = ""
) -> Dict[str, Any]:
    """Add a book to the processed list for a specific user."""
    q = Query()
    book_data = {
        "doc_type": PROCESSED_DOC_TYPE,
        "user_id": user_id,
        "book_id": book_id,
        "title": title,
        "author": author,
        "added_date": datetime.utcnow().isoformat(),
        "status": status,  # "downloaded", "no_results", "error"
        "torrent_name": torrent_name,
        "error_message": error_message,
    }
    
    existing = get_processed_book(user_id, book_id)
    if existing:
        goodreadsdb.update(book_data, (q.user_id == user_id) & (q.book_id == book_id))
    else:
        goodreadsdb.insert(book_data)
    
    return book_data


def delete_processed_book(user_id: str, book_id: str) -> bool:
    """Delete a processed book for a specific user (allows re-download)."""
    q = Query()
    removed = goodreadsdb.remove((q.user_id == user_id) & (q.book_id == book_id))
    return len(removed) > 0


def clear_all_processed_books(user_id: str) -> int:
    """Clear all processed books for a specific user (allows re-downloading everything)."""
    q = Query()
    removed = goodreadsdb.remove((q.doc_type == PROCESSED_DOC_TYPE) & (q.user_id == user_id))
    return len(removed)
