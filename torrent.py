from abc import abstractmethod, ABC
import requests
import time
from typing import List, Dict, Any, Optional
from models import User, TorrentClientType
from constants import (
    ADMIN_USER_DICT, BEETS_COMPLETE_LABEL, BEETS_ERROR_LABEL, 
    DELETE_AFTER_DAYS, STRICTLY_DELETE_AFTER_DAYS, LABEL,
    TRANSMISSION_PASS, TRANSMISSION_URL, TRANSMISSION_USER, USE_BEETS_IMPORT
)
from auth import get_users
from db import get_candidates
from utils import custom_logger

logger = custom_logger(__name__)


class TorrentClientInterface(ABC):
    """Abstract base class for torrent clients"""

    @abstractmethod
    def get_torrents(self, user: User) -> List[Dict[str, Any]]:
        """Get list of torrents for a user"""
        pass

    @abstractmethod
    def add_torrent(self, torrent_url: str, user: User, label: str = None) -> bool:
        """Add a torrent from URL/magnet link"""
        pass

    @abstractmethod
    def delete_torrent(self, torrent_id: str, user: User, delete_data: bool = True) -> bool:
        """Delete a torrent"""
        pass

    @abstractmethod
    def pause_torrent(self, torrent_id: str, user: User) -> bool:
        """Pause a torrent"""
        pass

    @abstractmethod
    def resume_torrent(self, torrent_id: str, user: User) -> bool:
        """Resume/start a torrent"""
        pass

    @abstractmethod
    def add_label_to_torrent(self, torrent_id: str, user: User, label: str) -> bool:
        """Add label to torrent"""
        pass

    @abstractmethod
    def remove_label_from_torrent(self, torrent_id: str, user: User, label: str) -> bool:
        """Remove label from torrent"""
        pass

    def delete_old_torrents(self) -> None:
        """Delete old completed torrents - optional implementation"""
        pass


class TransmissionClient(TorrentClientInterface):
    """Transmission torrent client implementation"""

    def __init__(self, url: str = None, username: str = None, password: str = None):
        self.url = url or TRANSMISSION_URL
        self.username = username or TRANSMISSION_USER
        self.password = password or TRANSMISSION_PASS

    def _get_session_id(self) -> Optional[str]:
        """Get Transmission session ID"""
        try:
            response = requests.get(self.url, auth=(self.username, self.password))
            return response.headers.get("X-Transmission-Session-Id")
        except Exception as e:
            logger.error(f"Failed to get Transmission session ID: {e}")
            return None

    def _make_request(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make authenticated request to Transmission"""
        session_id = self._get_session_id()
        if not session_id:
            return None

        headers = {"X-Transmission-Session-Id": session_id}
        try:
            response = requests.post(
                self.url, 
                auth=(self.username, self.password), 
                json=payload, 
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Transmission request failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Transmission request error: {e}")
            return None

    def _check_user_access(self, user: User, torrent_id: str) -> bool:
        """Check if user has access to torrent"""
        if user.role == "admin":
            return True

        torrents = self.get_torrents(user)
        if torrents is None:
            return False

        torrent_ids = [t["id"] for t in torrents]
        if torrent_id not in torrent_ids:
            logger.warning(f"User {user.id} tried to access torrent {torrent_id} without permission.")
            return False
        return True

    def get_torrent_by_id(self, torrent_id: str) -> Optional[Dict[str, Any]]:
        """Get torrent details by ID"""
        payload = {
            "method": "torrent-get",
            "arguments": {
                "fields": [
                    "id", "name", "status", "labels", "totalSize", "percentDone",
                    "downloadedEver", "uploadedEver", "addedDate", "uploadRatio",
                    "files", "eta", "hashString"
                ],
                "ids": [int(torrent_id)]
            }
        }

        response_data = self._make_request(payload)
        if not response_data:
            return None

        torrents = response_data.get('arguments', {}).get('torrents', [])
        if torrents:
            return torrents[0]
        return None

    def get_torrents(self, user: User) -> List[Dict[str, Any]]:
        """Get torrents filtered by user permissions"""
        payload = {
            "method": "torrent-get",
            "arguments": {
                "fields": [
                    "id", "name", "status", "labels", "totalSize", "percentDone",
                    "downloadedEver", "uploadedEver", "addedDate", "uploadRatio",
                    "files", "eta", "hashString"
                ]
            }
        }

        response_data = self._make_request(payload)
        if not response_data:
            return []

        torrents = response_data.get('arguments', {}).get('torrents', [])
        all_users = get_users()
        filtered_torrents = []

        for torrent in torrents:
            # Filter by label and user permissions
            torrent_labels = torrent.get("labels", [])
            if (LABEL not in torrent_labels or 
                (user.id not in torrent_labels and user.role != "admin")):
                continue

            # Process torrent data
            status = self._get_torrent_status(torrent["status"])
            name = torrent["name"].replace("_", " ").replace("+", " ").replace(".", " ").strip()
            percent_done = torrent["percentDone"] * 100
            hash_string = torrent.get("hashString", "")
            imported = BEETS_COMPLETE_LABEL in torrent_labels
            import_error = BEETS_ERROR_LABEL in torrent_labels

            # Get added_by info for admin users
            added_by = None
            if user.role == "admin":
                for label in torrent_labels:
                    if label.startswith("username:"):
                        added_by = label.split(":", 1)[1]
                        break

                if not added_by:
                    added_by_users = [u for u in all_users if u.get("id", "0") in torrent_labels]
                    if added_by_users:
                        added_by = added_by_users[0].get("username", "unknown")

            candidates = []
            if import_error:
                candidates = get_candidates(hash_string)

            filtered_torrents.append({
                "id": torrent["id"],
                "labels": torrent_labels,
                "name": name,
                "status": status,
                "total_size": torrent["totalSize"],
                "percent_done": percent_done,
                "downloaded_ever": torrent["downloadedEver"],
                "uploaded_ever": torrent["uploadedEver"],
                "added_date": torrent["addedDate"],
                "files": torrent.get("files", []),
                "use_beets_import": USE_BEETS_IMPORT,
                "imported": imported,
                "importError": import_error,
                "eta": torrent.get("eta", -1),
                "candidates": candidates,
                "hash_string": hash_string,
                "added_by": added_by,
                "upload_ratio": round(torrent.get("uploadRatio", 0.0), 2)
            })

        # Sort by status and added date
        filtered_torrents.sort(key=lambda x: (x["status"] != "Stopped", x["added_date"]), reverse=True)
        return filtered_torrents

    def add_torrent(self, torrent_url: str, user: User, label: str = None) -> bool:
        """Add torrent to Transmission"""
        if label is None:
            label = LABEL

        # Convert to magnet if needed (from audiobookbay.py)
        logger.debug(f"Adding torrent URL: {torrent_url}")
        torrent_url = self._get_jackett_magnet(torrent_url)

        payload = {
            "method": "torrent-add",
            "arguments": {"filename": torrent_url}
        }

        response_data = self._make_request(payload)
        if not response_data:
            return False

        try:
            logger.debug(f"Transmission add_torrent response: {response_data}")
            torrent_id = response_data['arguments']['torrent-added']['id']
            self.add_label_to_torrent(torrent_id, user, label)
            return True
        except (KeyError, TypeError) as e:
            logger.exception(f"Error adding torrent: {e}")
            return False

    def delete_torrent(self, torrent_id: str, user: User, delete_data: bool = True) -> bool:
        """Delete torrent from Transmission"""
        if not user:
            return False

        if not self._check_user_access(user, torrent_id):
            return False

        payload = {
            "method": "torrent-remove",
            "arguments": {
                "ids": [torrent_id],
                "delete-local-data": delete_data
            }
        }

        response_data = self._make_request(payload)
        if response_data:
            logger.info(f"Torrent {torrent_id} {'and its data' if delete_data else ''} deleted successfully.")
            return True
        return False

    def pause_torrent(self, torrent_id: str, user: User) -> bool:
        """Pause torrent in Transmission"""
        if not self._check_user_access(user, torrent_id):
            return False

        payload = {
            "method": "torrent-stop",
            "arguments": {"ids": [torrent_id]}
        }

        response_data = self._make_request(payload)
        if response_data:
            logger.info(f"Torrent {torrent_id} paused successfully.")
            return True
        return False

    def resume_torrent(self, torrent_id: str, user: User) -> bool:
        """Resume/start torrent in Transmission"""
        if not self._check_user_access(user, torrent_id):
            return False

        payload = {
            "method": "torrent-start",
            "arguments": {"ids": [torrent_id]}
        }

        response_data = self._make_request(payload)
        if response_data:
            logger.info(f"Torrent {torrent_id} started successfully.")
            return True
        return False

    def add_label_to_torrent(self, torrent_id: str, user: User, label: str) -> bool:
        """Add label to torrent"""
        torrent = self.get_torrent_by_id(torrent_id=torrent_id)
        if not torrent:
            logger.warning(f"Failed to retrieve torrent with ID {torrent_id}")
            return False

        current_labels = torrent.get("labels", [])
        logger.debug(f"Current labels for torrent {torrent_id}: {current_labels}")
        new_labels = list(set(current_labels + [label]))

        # Add user labels
        if user:
            new_labels.append(user.id)
            if user.username:
                new_labels.append(f"username:{user.username}")
            new_labels = list(set(new_labels))

        payload = {
            "method": "torrent-set",
            "arguments": {
                "ids": [torrent_id],
                "labels": new_labels
            }
        }

        response_data = self._make_request(payload)
        return response_data is not None

    def remove_label_from_torrent(self, torrent_id: str, user: User, label: str) -> bool:
        """Remove label from torrent"""
        torrents = self.get_torrents(user, torrent_id=torrent_id)
        if not torrents:
            logger.warning(f"Failed to retrieve torrent with ID {torrent_id}")
            return False

        current_labels = torrents[0].get("labels", [])
        new_labels = list(set(current_labels) - {label})

        if not new_labels:
            return True  # Nothing to do

        payload = {
            "method": "torrent-set",
            "arguments": {
                "ids": [torrent_id],
                "labels": new_labels
            }
        }

        response_data = self._make_request(payload)
        return response_data is not None

    def delete_old_torrents(self) -> None:
        """Delete old completed torrents"""
        torrents = self.get_torrents(ADMIN_USER_DICT)
        torrents = [t for t in torrents if (
            "audiobook" in t.get("labels", []) and 
            BEETS_COMPLETE_LABEL in t.get("labels", []) and 
            BEETS_ERROR_LABEL not in t.get("labels", [])
        )]

        current_time = time.time()
        for torrent in torrents:
            time_difference_days = (current_time - torrent["added_date"]) / (60 * 60 * 24)

            if (time_difference_days > DELETE_AFTER_DAYS and 
                torrent["upload_ratio"] > 1.0):
                self.delete_torrent(torrent["id"], user=ADMIN_USER_DICT, delete_data=False)
                logger.info(f"DELETED: {torrent['name']}")

            if time_difference_days > STRICTLY_DELETE_AFTER_DAYS:
                self.delete_torrent(torrent["id"], user=ADMIN_USER_DICT, delete_data=True)
                logger.info(f"DELETED: {torrent['name']}")

    def _get_jackett_magnet(self, url: str) -> str:
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

    def _get_torrent_status(self, status_code: int) -> str:
        """Convert status code to readable status"""
        status_map = {
            0: "Stopped",
            1: "Queued to check",
            2: "Checking",
            3: "Queued to download",
            4: "Downloading",
            5: "Queued to seed",
            6: "Seeding"
        }
        return status_map.get(status_code, "Unknown")


class DecypharrClient(TorrentClientInterface):
    """Decypharr torrent client implementation"""

    def __init__(self, url: str = "", username: str = "", password: str = ""):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make request to Decypharr API"""
        try:
            url = f"{self.url}{endpoint}"
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except Exception as e:
            logger.error(f"Decypharr API request failed: {e}")
            return None

    def get_torrents(self, user: User) -> List[Dict[str, Any]]:
        """Get torrents from Decypharr (using qBittorrent API compatibility)"""
        # Decypharr uses qBittorrent API, so we use /api/v2/torrents/info
        params = {}

        response_data = self._make_request('GET', '/api/v2/torrents/info', params=params)
        if not response_data:
            return []

        # Convert qBittorrent format to our internal format
        filtered_torrents = []
        for torrent in response_data:
            # Decypharr doesn't support multi-user, so we don't filter by user
            filtered_torrents.append({
                "id": torrent.get("hash", ""),  # qBittorrent uses hash as ID
                "labels": torrent.get("tags", "").split(",") if torrent.get("tags") else [],
                "name": torrent.get("name", "").replace("_", " ").replace("+", " ").replace(".", " ").strip(),
                "status": torrent.get("state", "unknown"),
                "total_size": torrent.get("size", 0),
                "percent_done": torrent.get("progress", 0) * 100,
                "downloaded_ever": torrent.get("downloaded", 0),
                "uploaded_ever": torrent.get("uploaded", 0),
                "added_date": torrent.get("added_on", 0),
                "files": [],  # Would need separate API call to get files
                "use_beets_import": False,  # Decypharr handles this differently
                "imported": False,
                "importError": False,
                "eta": torrent.get("eta", -1),
                "candidates": [],
                "hash_string": torrent.get("hash", ""),
                "added_by": "system",  # Decypharr is single-user
                "upload_ratio": torrent.get("ratio", 0.0)
            })

        return filtered_torrents

    def add_torrent(self, torrent_url: str, user: User, label: str = None) -> bool:
        """Add torrent to Decypharr"""
        # Use qBittorrent API format
        data = {
            'urls': torrent_url,
        }
        if label:
            data['tags'] = label

        response_data = self._make_request('POST', '/api/v2/torrents/add', data=data)
        return response_data is not None

    def delete_torrent(self, torrent_id: str, user: User, delete_data: bool = True) -> bool:
        """Delete torrent from Decypharr"""
        data = {
            'hashes': torrent_id,
            'deleteFiles': delete_data
        }
        response_data = self._make_request('POST', '/api/v2/torrents/delete', data=data)
        if response_data is not None:
            logger.info(f"Torrent {torrent_id} {'and its data' if delete_data else ''} deleted successfully.")
            return True
        return False

    def pause_torrent(self, torrent_id: str, user: User) -> bool:
        """Pause torrent in Decypharr"""
        data = {'hashes': torrent_id}
        response_data = self._make_request('POST', '/api/v2/torrents/pause', data=data)
        if response_data is not None:
            logger.info(f"Torrent {torrent_id} paused successfully.")
            return True
        return False

    def resume_torrent(self, torrent_id: str, user: User) -> bool:
        """Resume torrent in Decypharr"""
        data = {'hashes': torrent_id}
        response_data = self._make_request('POST', '/api/v2/torrents/resume', data=data)
        if response_data is not None:
            logger.info(f"Torrent {torrent_id} resumed successfully.")
            return True
        return False

    def add_label_to_torrent(self, torrent_id: str, user: User, label: str) -> bool:
        """Add tag/label to torrent in Decypharr"""
        data = {
            'hashes': torrent_id,
            'tags': label
        }
        response_data = self._make_request('POST', '/api/v2/torrents/addTags', data=data)
        return response_data is not None

    def remove_label_from_torrent(self, torrent_id: str, user: User, label: str) -> bool:
        """Remove tag/label from torrent in Decypharr"""
        data = {
            'hashes': torrent_id,
            'tags': label
        }
        response_data = self._make_request('POST', '/api/v2/torrents/removeTags', data=data)
        return response_data is not None

    def delete_old_torrents(self) -> None:
        """Decypharr handles cleanup automatically via debrid services"""
        logger.info("Decypharr handles torrent cleanup automatically via debrid services")
        pass


# Factory function to create appropriate client
def create_torrent_client(client_type: TorrentClientType, **kwargs) -> TorrentClientInterface:
    """Factory function to create torrent client instances"""
    if client_type == TorrentClientType.transmission:
        return TransmissionClient(**kwargs)
    elif client_type == TorrentClientType.decypharr:
        return DecypharrClient(**kwargs)
    else:
        raise ValueError(f"Unsupported torrent client type: {client_type}")

