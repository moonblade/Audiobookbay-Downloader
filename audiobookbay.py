import os
import time
import requests

from auth import get_users
from constants import ADMIN_USER_DICT, BEETS_COMPLETE_LABEL, BEETS_ERROR_LABEL, DELETE_AFTER_DAYS, JACKETT_API_KEY, JACKETT_API_URL, LABEL, STRICTLY_DELETE_AFTER_DAYS, TRANSMISSION_PASS, TRANSMISSION_URL, TRANSMISSION_USER, USE_BEETS_IMPORT
from db import get_candidates
from utils import custom_logger

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

def search_audiobook(query):
    params = {
        "apikey": JACKETT_API_KEY,
        "Query": query,
        "Category": "audiobooks"
    }
    logger.info(f"Searching for {query}...")
    response = requests.get(str(JACKETT_API_URL), params=params)
    if response.status_code != 200:
        logger.error("Error fetching results from Jackett:", response.text)
        return []
    results = response.json()
    logger.info(f"Found {len(results.get('Results', []))} results for {query}")
    return results.get("Results", [])

def add_to_transmission(torrent_url, user, label=LABEL):
    torrent_url = get_jackett_magnet(torrent_url)
    session_response = requests.get(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS))
    session_id = session_response.headers.get("X-Transmission-Session-Id")

    if not session_id:
        print("Failed to get Transmission session ID")
        return False

    payload = {
        "method": "torrent-add",
        "arguments": {"filename": torrent_url}
    }
    headers = {"X-Transmission-Session-Id": session_id}

    response = requests.post(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS), json=payload, headers=headers)

    if response.status_code == 200:
        # Get the newly added torrent's ID
        try:
          torrent_id = response.json()['arguments']['torrent-added']['id']
          add_label_to_torrent(torrent_id, user, label) # Add the label after adding the torrent
          return True
        except (KeyError, TypeError) as e: # Handle cases where torrent-added might not be in the response
          logger.exception(f"Error adding torrent {e}")
          print("Warning: Could not retrieve torrent ID from response. Label may not be applied.")
          return True # Torrent was added, but label might have failed. You might want to return False here instead.

    return False

def remove_label_from_torrent_with_hash(hash_string, user=None, label=LABEL):
    session_response = requests.get(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS))
    session_id = session_response.headers.get("X-Transmission-Session-Id")

    if not session_id:
        print("Failed to get Transmission session ID")
        return False

    new_labels = []
    id = None
    try:
        torrents = get_torrents(user)
        if not torrents:
            logger.warn(f"Failed to retrieve torrent with hash {hash_string}")

        torrent = [torrent for torrent in torrents if torrent.get("hash_string") == hash_string][0]
        id = torrent.get("id")
        current_labels = torrent.get("labels", [])

        new_labels = list(set(current_labels) - set([label]))
    except Exception as e:
        logger.warn(f"Error getting existing torrent labels: {e}")
        return

    if not new_labels:
        return

    payload = {
        "method": "torrent-set",
        "arguments": {
            "ids": [id],
            "labels": new_labels
        }
    }
    headers = {"X-Transmission-Session-Id": session_id}
    response = requests.post(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS), json=payload, headers=headers)
    return response.status_code == 200

def remove_label_from_torrent(torrent_id, user=None, label=LABEL):
    session_response = requests.get(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS))
    session_id = session_response.headers.get("X-Transmission-Session-Id")

    if not session_id:
        print("Failed to get Transmission session ID")
        return False

    new_labels = []
    try:
        torrents = get_torrents(user, torrent_id=torrent_id)
        if not torrents:
            logger.warn(f"Failed to retrieve torrent with ID {torrent_id}")

        current_labels = torrents[0].get("labels", [])

        new_labels = list(set(current_labels) - set([label]))
    except Exception as e:
        logger.warn(f"Error getting existing torrent labels: {e}")

    if not new_labels:
        return

    payload = {
        "method": "torrent-set",
        "arguments": {
            "ids": [torrent_id],
            "labels": new_labels
        }
    }
    headers = {"X-Transmission-Session-Id": session_id}
    response = requests.post(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS), json=payload, headers=headers)
    return response.status_code == 200

def add_label_to_torrent(torrent_id, user=None, label=LABEL):
    session_response = requests.get(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS))
    session_id = session_response.headers.get("X-Transmission-Session-Id")

    if not session_id:
        print("Failed to get Transmission session ID")
        return False

    new_labels = [label]
    try:
        torrents = get_torrents(user, torrent_id=torrent_id)
        if not torrents:
            logger.warn(f"Failed to retrieve torrent with ID {torrent_id}")

        current_labels = torrents[0].get("labels", [])

        new_labels = list(set(current_labels + [label]))
    except Exception as e:
        logger.warn(f"Error getting existing torrent labels: {e}")

    if user:
        new_labels = list(set(new_labels + [user.get("id", "common")]))

    payload = {
        "method": "torrent-set",
        "arguments": {
            "ids": [torrent_id],
            "labels": new_labels
        }
    }
    headers = {"X-Transmission-Session-Id": session_id}
    response = requests.post(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS), json=payload, headers=headers)
    return response.status_code == 200

def get_torrents(user, label=LABEL, torrent_id=None):
    session_response = requests.get(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS))
    session_id = session_response.headers.get("X-Transmission-Session-Id")

    if not session_id:
        print("Failed to get Transmission session ID")
        return []

    payload = {
        "method": "torrent-get",
        "arguments": {
            "fields": [
                "id",
                "name",
                "status",
                "labels",
                "totalSize",
                "percentDone",
                "downloadedEver",
                "uploadedEver",
                "addedDate",
                "uploadRatio",
                "files",
                "eta",
                "hashString"
            ]
        }
    }
    headers = {"X-Transmission-Session-Id": session_id}
    response = requests.post(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS), json=payload, headers=headers)

    all_users = get_users()
    if response.status_code == 200:
        torrents = response.json()['arguments']['torrents']
        filtered_torrents = []
        for torrent in torrents:
            if (torrent_id is None or torrent["id"] == torrent_id) and label in torrent.get("labels", []) and (user.get("id", "common") in torrent.get("labels", []) or user.get("role", "user") == "admin"):
                status = get_torrent_status(torrent["status"])
                total_size = torrent["totalSize"]
                name = torrent["name"].replace("_", " ").replace("+", " ")
                percent_done = torrent["percentDone"] * 100
                downloaded_ever = torrent["downloadedEver"]
                uploaded_ever = torrent["uploadedEver"]
                added_date = torrent["addedDate"]
                eta = torrent.get("eta", -1)
                hash_string = torrent.get("hashString", "")
                upload_ratio = round(torrent.get("uploadRatio", 0.0), 2)
                # files = [{"name": f["name"], "size": f["length"]} for f in torrent.get("files", [])]
                files = torrent.get("files", [])
                imported = BEETS_COMPLETE_LABEL in torrent.get("labels", [])
                importError = BEETS_ERROR_LABEL in torrent.get("labels", [])
                added_by = None
                if user.get("role", "user") == "admin":
                    added_by = [u for u in all_users if u.get("id", "0") in torrent.get("labels", [])]
                    if added_by:
                        added_by = added_by[0].get("username", "unknown")
                candidates = []
                if importError:
                    candidates = get_candidates(hash_string)

                filtered_torrents.append({
                    "id": torrent["id"],
                    "labels": torrent.get("labels", []),
                    "name": name,
                    "status": status,
                    "total_size": total_size,  # Size in bytes
                    "percent_done": percent_done, # Percentage
                    "downloaded_ever": downloaded_ever, # Bytes
                    "uploaded_ever": uploaded_ever, # Bytes
                    "added_date": added_date,
                    "files": files,
                    "use_beets_import": USE_BEETS_IMPORT,
                    "imported": imported,
                    "importError": importError,
                    "eta": eta,
                    "candidates": candidates,
                    "hash_string": hash_string,
                    "added_by": added_by,
                    "upload_ratio": upload_ratio  # Seed ratio
                })

        filtered_torrents.sort(key=lambda x: (x["status"] != "Stopped", x["added_date"]), reverse=True) # Sort by status and then by added date
        return filtered_torrents
    else:
        print(f"Error getting torrent list: {response.status_code}")
        return []

def get_torrent_status(status_code):  # Helper function to convert status code
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

def pause_torrent(torrent_id, user=None):
    """Pauses a torrent in Transmission.

    Args:
        torrent_id: The ID of the torrent to pause.

    Returns:
        True if the torrent was successfully paused, False otherwise.
    """
    session_response = requests.get(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS))
    session_id = session_response.headers.get("X-Transmission-Session-Id")

    if not session_id:
        print("Failed to get Transmission session ID")
        return False

    if user and user.get("role") != "admin":
        torrents = get_torrents(user)  # Retrieve torrents for user
        if torrents is None:
            raise Exception("Error getting torrent list")
        torrent_ids = [t["id"] for t in torrents]
        if torrent_id not in torrent_ids:
            logger.warning(f"User {user.get('id')} tried to delete torrent {torrent_id} without permission.")
            raise Exception("User does not have access to delete this torrent")

    payload = {
        "method": "torrent-stop",
        "arguments": {
            "ids": [torrent_id]
        }
    }
    headers = {"X-Transmission-Session-Id": session_id}

    response = requests.post(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS), json=payload, headers=headers)

    if response.status_code == 200:
        logger.info(f"Torrent {torrent_id} paused successfully.")
        return True
    else:
        logger.error(f"Error pausing torrent {torrent_id}: {response.status_code} - {response.text}")
        return False

def play_torrent(torrent_id, user=None):
    """Starts a torrent in Transmission.

    Args:
        torrent_id: The ID of the torrent to start.

    Returns:
        True if the torrent was successfully started, False otherwise.
    """
    session_response = requests.get(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS))
    session_id = session_response.headers.get("X-Transmission-Session-Id")

    if not session_id:
        print("Failed to get Transmission session ID")
        return False

    if user and user.get("role") != "admin":
        torrents = get_torrents(user)  # Retrieve torrents for user
        if torrents is None:
            raise Exception("Error getting torrent list")
        torrent_ids = [t["id"] for t in torrents]
        if torrent_id not in torrent_ids:
            logger.warning(f"User {user.get('id')} tried to start torrent {torrent_id} without permission.")
            raise Exception("User does not have access to start this torrent")

    payload = {
        "method": "torrent-start",
        "arguments": {
            "ids": [torrent_id]
        }
    }
    headers = {"X-Transmission-Session-Id": session_id}

    response = requests.post(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS), json=payload, headers=headers)

    if response.status_code == 200:
        logger.info(f"Torrent {torrent_id} started successfully.")
        return True
    else:
        logger.error(f"Error starting torrent {torrent_id}: {response.status_code} - {response.text}")
        return False

def delete_old_torrents():
    torrents = get_torrents(ADMIN_USER_DICT)
    torrents = [torrent for torrent in torrents if ("audiobook" in torrent.get("labels") and BEETS_COMPLETE_LABEL in torrent.get("labels") and BEETS_ERROR_LABEL not in torrent.get("labels"))]
    for torrent in torrents:
        added_time = torrent["added_date"]
        current_time = time.time()
        time_difference_days = (current_time - added_time) / (60 * 60 * 24)
        if time_difference_days > DELETE_AFTER_DAYS and torrent["upload_ratio"] > 1.0:
            delete_torrent(torrent["id"], user=ADMIN_USER_DICT, delete_data=False)
            logger.info(f"DELETED: {torrent['name']}")
        if time_difference_days > STRICTLY_DELETE_AFTER_DAYS:
            delete_torrent(torrent["id"], user=ADMIN_USER_DICT, delete_data=True)
            logger.info(f"DELETED: {torrent['name']}")

def delete_torrent(torrent_id, user=None, delete_data=True):
    """Deletes a torrent from Transmission.

    Args:
        torrent_id: The ID of the torrent to delete.
        delete_data: If True, also deletes the downloaded data. Defaults to False.
        user: User dict, used for authorization. If None, assumes admin.

    Returns:
        True if the torrent was successfully deleted, False otherwise.
    """

    session_response = requests.get(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS))
    session_id = session_response.headers.get("X-Transmission-Session-Id")

    if not session_id:
        print("Failed to get Transmission session ID")
        return False

    # Authorization check (if user is provided)
    if not user:
        return False # User must be provided

    if user and user.get("role") != "admin":
        torrents = get_torrents(user)  # Retrieve torrents for user
        if torrents is None:
          return False # Error getting torrent list
        torrent_ids = [t["id"] for t in torrents]
        if torrent_id not in torrent_ids:
          logger.warning(f"User {user.get('id')} tried to delete torrent {torrent_id} without permission.")
          return False # User does not have access to delete this torrent


    payload = {
        "method": "torrent-remove",
        "arguments": {
            "ids": [torrent_id],
            "delete-local-data": delete_data  # Set to True to delete data
        }
    }
    headers = {"X-Transmission-Session-Id": session_id}

    response = requests.post(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS), json=payload, headers=headers)

    if response.status_code == 200:
        logger.info(f"Torrent {torrent_id} {'and its data' if delete_data else ''} deleted successfully.")
        return True
    else:
        logger.error(f"Error deleting torrent {torrent_id}: {response.status_code} - {response.text}")
        return False
