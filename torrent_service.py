import time
from typing import Optional, List, Dict, Any
from models import User, TorrentClientType
from torrent import create_torrent_client, TorrentClientInterface
from constants import (
    LABEL, DELETE_AFTER_DAYS, STRICTLY_DELETE_AFTER_DAYS, 
    BEETS_COMPLETE_LABEL, BEETS_ERROR_LABEL
)
from audiobookbay import get_jackett_magnet
from utils import custom_logger

logger = custom_logger(__name__)

class TorrentService:
    """Service class to handle all torrent operations"""

    def __init__(self, client_type: TorrentClientType = TorrentClientType.transmission, **client_kwargs):
        self.client_type = client_type
        self.client: TorrentClientInterface = create_torrent_client(client_type, **client_kwargs)
        logger.info(f"Initialized TorrentService with {client_type.value} client")

    def get_torrents(self, user: User, torrent_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get torrents for a user"""
        try:
            return self.client.get_torrents(user, torrent_id)
        except Exception as e:
            logger.error(f"Error getting torrents: {e}")
            return []

    def add_torrent(self, torrent_url: str, user: User, label: str = None) -> bool:
        """Add torrent from URL/magnet link"""
        try:
            if label is None:
                label = LABEL

            # Convert to magnet if needed
            torrent_url = get_jackett_magnet(torrent_url)
            return self.client.add_torrent(torrent_url, user, label)
        except Exception as e:
            logger.error(f"Error adding torrent: {e}")
            return False

    def delete_torrent(self, torrent_id: int, user: User, delete_data: bool = True) -> bool:
        """Delete a torrent"""
        try:
            return self.client.delete_torrent(str(torrent_id), user, delete_data)
        except Exception as e:
            logger.error(f"Error deleting torrent {torrent_id}: {e}")
            return False

    def pause_torrent(self, torrent_id: int, user: User) -> bool:
        """Pause a torrent"""
        try:
            return self.client.pause_torrent(str(torrent_id), user)
        except Exception as e:
            logger.error(f"Error pausing torrent {torrent_id}: {e}")
            return False

    def resume_torrent(self, torrent_id: int, user: User) -> bool:
        """Resume/play a torrent"""
        try:
            return self.client.resume_torrent(str(torrent_id), user)
        except Exception as e:
            logger.error(f"Error resuming torrent {torrent_id}: {e}")
            return False

    def add_label_to_torrent(self, torrent_id: int, user: User, label: str) -> bool:
        """Add label to torrent"""
        try:
            return self.client.add_label_to_torrent(str(torrent_id), user, label)
        except Exception as e:
            logger.error(f"Error adding label to torrent {torrent_id}: {e}")
            return False

    def remove_label_from_torrent(self, torrent_id: int, user: User, label: str) -> bool:
        """Remove label from torrent"""
        try:
            return self.client.remove_label_from_torrent(str(torrent_id), user, label)
        except Exception as e:
            logger.error(f"Error removing label from torrent {torrent_id}: {e}")
            return False

    def remove_label_from_torrent_with_hash(self, hash_string: str, user: User, label: str) -> bool:
        """Remove label from torrent by hash"""
        try:
            # For Transmission, find torrent by hash first
            if self.client_type == TorrentClientType.transmission:
                torrents = self.client.get_torrents(user)
                matching_torrents = [t for t in torrents if t.get("hash_string") == hash_string]
                if matching_torrents:
                    return self.client.remove_label_from_torrent(str(matching_torrents[0]["id"]), user, label)
                return False

            # For other clients that might use hash directly as ID
            return self.client.remove_label_from_torrent(hash_string, user, label)
        except Exception as e:
            logger.error(f"Error removing label from torrent with hash {hash_string}: {e}")
            return False

    def delete_old_torrents(self) -> None:
        """Delete old completed torrents"""
        try:
            self.client.delete_old_torrents()
        except Exception as e:
            logger.error(f"Error deleting old torrents: {e}")

# Global torrent service instance - will be initialized at startup
torrent_service: Optional[TorrentService] = None

def get_torrent_service() -> TorrentService:
    """Get the global torrent service instance"""
    if torrent_service is None:
        raise RuntimeError("TorrentService not initialized. Call init_torrent_service() first.")
    return torrent_service

def init_torrent_service(client_type: TorrentClientType = TorrentClientType.transmission, **client_kwargs) -> TorrentService:
    """Initialize the global torrent service instance"""
    global torrent_service
    torrent_service = TorrentService(client_type, **client_kwargs)
    return torrent_service

# Convenience functions that use the global service
def get_torrents(user: User, torrent_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get torrents for a user"""
    return get_torrent_service().get_torrents(user, torrent_id)

def add_torrent(torrent_url: str, user: User, label: str = None) -> bool:
    """Add torrent from URL/magnet link"""
    return get_torrent_service().add_torrent(torrent_url, user, label)

def delete_torrent(torrent_id: int, user: User, delete_data: bool = True) -> bool:
    """Delete a torrent"""
    return get_torrent_service().delete_torrent(torrent_id, user, delete_data)

def pause_torrent(torrent_id: int, user: User) -> bool:
    """Pause a torrent"""
    return get_torrent_service().pause_torrent(torrent_id, user)

def resume_torrent(torrent_id: int, user: User) -> bool:
    """Resume/play a torrent"""
    return get_torrent_service().resume_torrent(torrent_id, user)

def add_label_to_torrent(torrent_id: int, user: User, label: str) -> bool:
    """Add label to torrent"""
    return get_torrent_service().add_label_to_torrent(torrent_id, user, label)

def remove_label_from_torrent(torrent_id: int, user: User, label: str) -> bool:
    """Remove label from torrent"""
    return get_torrent_service().remove_label_from_torrent(torrent_id, user, label)

def remove_label_from_torrent_with_hash(hash_string: str, user: User, label: str) -> bool:
    """Remove label from torrent by hash"""
    return get_torrent_service().remove_label_from_torrent_with_hash(hash_string, user, label)

def delete_old_torrents() -> None:
    """Delete old completed torrents"""
    get_torrent_service().delete_old_torrents()

