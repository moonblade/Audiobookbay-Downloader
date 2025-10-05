from abc import abstractmethod, ABC
import json
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
            logger.debug(f"Making Transmission request with payload: {payload} and headers: {headers} to {self.url}")
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

        torrent_ids = [str(t.get("id", "")) for t in torrents]
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
                "ids": [int(torrent_id)],
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
            "arguments": {"ids": [int(torrent_id)]}
        }

        response_data = self._make_request(payload)
        logger.debug(f"Pause torrent response: {response_data}")
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
            "arguments": {"ids": [int(torrent_id)]}
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
                "ids": [int(torrent_id)],
                "labels": new_labels
            }
        }

        response_data = self._make_request(payload)
        return response_data is not None

    def remove_label_from_torrent(self, torrent_id: str, user: User, label: str) -> bool:
        """Remove label from torrent"""
        torrent = self.get_torrent_by_id(torrent_id)
        if not torrent:
            logger.warning(f"Failed to retrieve torrent with ID {torrent_id}")
            return False

        current_labels = torrent.get("labels", [])
        new_labels = list(set(current_labels) - {label})

        if not new_labels:
            return True  # Nothing to do

        payload = {
            "method": "torrent-set",
            "arguments": {
                "ids": [int(torrent_id)],
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

    def __init__(self, url: str = "", api_key: str = ""):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            # Set the API key in headers for authentication
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make request to Decypharr API"""
        try:
            url = f"{self.url}{endpoint}"
            logger.debug(f"Making {method} request to {url} with kwargs: {kwargs}")
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 404:
                logger.warning(f"Endpoint {endpoint} not found (404) - feature not implemented in Decypharr")
                return None
                
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Decypharr API endpoint {endpoint} not implemented")
            else:
                logger.error(f"Decypharr API HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"Decypharr API request failed: {e}")
            return None

    def get_arrs(self) -> List[Dict[str, Any]]:
        """Get all configured Arrs from Decypharr"""
        response_data = self._make_request('GET', '/api/arrs')
        if not response_data:
            logger.warning("Decypharr /api/arrs endpoint not implemented - returning empty list")
            return []
        return response_data

    def add_content(self, magnet_url: str) -> Dict[str, Any]:
        """Add content to Decypharr using /api/add endpoint"""
        
        # Prepare multipart form data payload matching working sample
        files = {
            "urls": (None, magnet_url),
            "arr": (None, ""),
            "downloadFolder": (None, "/mnt"),
            "action": (None, "none"),
            "downloadUncached": (None, "true")
        }

        response_data = self._make_request('POST', '/api/add', files=files)
        if not response_data:
            logger.warning("Decypharr /api/add endpoint failed")
            return {"results": [], "errors": ["Add content feature failed"]}
        
        return response_data

    def get_torrents(self, user: User) -> List[Dict[str, Any]]:
        """Get torrents from Decypharr using /api/torrents endpoint"""
        response_data = self._make_request('GET', '/api/torrents')
        if not response_data:
            logger.warning("Decypharr /api/torrents endpoint not implemented - returning empty list")
            return []

        # Convert Decypharr format to our internal format
        filtered_torrents = []
        for torrent in response_data:
            # Map Decypharr fields to our internal format
            filtered_torrents.append({
                "id": torrent.get("hash", ""),  # Use hash as ID
                "labels": [torrent.get("category", "")] if torrent.get("category") else [],
                "name": torrent.get("name", "").replace("_", " ").replace("+", " ").replace(".", " ").strip(),
                "status": self._map_torrent_status(torrent.get("status", "unknown")),
                "total_size": torrent.get("size", 0),
                "percent_done": (torrent.get("progress", 0) * 100) if torrent.get("progress") else 0,
                "downloaded_ever": 0,  # Not available in Decypharr API
                "uploaded_ever": 0,    # Not available in Decypharr API
                "added_date": self._parse_date(torrent.get("addedOn", "")),
                "files": [],  # Not available in this endpoint
                "use_beets_import": False,  # Decypharr handles this differently
                "imported": False,
                "importError": False,
                "eta": -1,  # Not available in Decypharr API
                "candidates": [],
                "hash_string": torrent.get("hash", ""),
                "added_by": "",  # Decypharr is single-user
                "upload_ratio": 0.0  # Not available in Decypharr API
            })

        return filtered_torrents

    def delete_torrents(self, hashes: List[str], remove_from_debrid: bool = False) -> bool:
        """Delete multiple torrents using Decypharr API"""
        params = {
            'hashes': ','.join(hashes),
            'removeFromDebrid': str(remove_from_debrid).lower()
        }
        response_data = self._make_request('DELETE', '/api/torrents', params=params)
        if response_data is None:
            logger.warning("Decypharr batch torrent deletion not implemented")
            return False
        return True

    def delete_single_torrent(self, category: str, hash_id: str, remove_from_debrid: bool = False) -> bool:
        """Delete single torrent by category and hash"""
        params = {'removeFromDebrid': str(remove_from_debrid).lower()}
        response_data = self._make_request('DELETE', f'/api/torrents/{category}/{hash_id}', params=params)
        if response_data is None:
            logger.warning("Decypharr single torrent deletion not implemented")
            return False
        return True

    def add_torrent(self, torrent_url: str, user: User, label: str = None) -> bool:
        """Add torrent to Decypharr using the /api/add endpoint"""
        # Use Decypharr's native add endpoint
        result = self.add_content(torrent_url)
        if result and (result.get("results") or result.get("success")):
            logger.info(f"Successfully added torrent to Decypharr: {torrent_url}")
            return True
        
        logger.error(f"Failed to add torrent using Decypharr add endpoint: {result}")
        return False

    def delete_torrent(self, torrent_id: str, user: User, delete_data: bool = True) -> bool:
        """Delete torrent from Decypharr"""
        # Try using the single torrent deletion endpoint first
        success = self.delete_single_torrent("", torrent_id, delete_data)
        if not success:
            # Fallback to batch deletion
            success = self.delete_torrents([torrent_id], delete_data)
        
        if success:
            logger.info(f"Torrent {torrent_id} {'and its data' if delete_data else ''} deleted successfully.")
        else:
            logger.warning(f"Failed to delete torrent {torrent_id} - feature may not be implemented")
        return success

    def pause_torrent(self, torrent_id: str, user: User) -> bool:
        """Pause torrent in Decypharr"""
        logger.warning("Decypharr pause torrent feature not implemented")
        return False

    def resume_torrent(self, torrent_id: str, user: User) -> bool:
        """Resume torrent in Decypharr"""
        logger.warning("Decypharr resume torrent feature not implemented")
        return False

    def add_label_to_torrent(self, torrent_id: str, user: User, label: str) -> bool:
        """Add tag/label to torrent in Decypharr"""
        logger.warning("Decypharr add label feature not implemented")
        return False

    def remove_label_from_torrent(self, torrent_id: str, user: User, label: str) -> bool:
        """Remove tag/label from torrent in Decypharr"""
        logger.warning("Decypharr remove label feature not implemented")
        return False

    def delete_old_torrents(self) -> None:
        """Decypharr handles cleanup automatically via debrid services"""
        logger.info("Decypharr handles torrent cleanup automatically via debrid services")
        pass

    def _map_torrent_status(self, status: str) -> str:
        """Map Decypharr status to internal status"""
        # Map common statuses
        status_map = {
            "downloading": "Downloading",
            "seeding": "Seeding", 
            "completed": "Complete",
            "paused": "Stopped",
            "error": "Error",
            "queued": "Queued"
        }
        return status_map.get(status.lower(), status)

    def _parse_date(self, date_str: str) -> int:
        """Parse date string to timestamp"""
        try:
            if date_str:
                from datetime import datetime
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return int(dt.timestamp())
        except:
            pass
        return 0


# Factory function to create appropriate client
def create_torrent_client(client_type: TorrentClientType, **kwargs) -> TorrentClientInterface:
    """Factory function to create torrent client instances"""
    if client_type == TorrentClientType.transmission:
        return TransmissionClient(**kwargs)
    elif client_type == TorrentClientType.decypharr:
        return DecypharrClient(**kwargs)
    else:
        raise ValueError(f"Unsupported torrent client type: {client_type}")

