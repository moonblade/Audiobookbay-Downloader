import os
import requests

from utils import custom_logger

logger = custom_logger(__name__)
JACKETT_API_URL = os.getenv("JACKETT_API_URL" "")
JACKETT_API_KEY = os.getenv("JACKETT_API_KEY", "")
TRANSMISSION_URL = os.getenv("TRANSMISSION_URL", "")
TRANSMISSION_USER = os.getenv("TRANSMISSION_USER", "")
TRANSMISSION_PASS = os.getenv("TRANSMISSION_PASS", "")
LABEL = os.getenv("LABEL", "audiobook")

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
        except (KeyError, TypeError): # Handle cases where torrent-added might not be in the response
          print("Warning: Could not retrieve torrent ID from response. Label may not be applied.")
          return True # Torrent was added, but label might have failed. You might want to return False here instead.

    return False

def add_label_to_torrent(torrent_id, user=None, label=LABEL):
    session_response = requests.get(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS))
    session_id = session_response.headers.get("X-Transmission-Session-Id")

    if not session_id:
        print("Failed to get Transmission session ID")
        return []

    torrents = get_torrents(user, torrent_id=torrent_id)
    if not torrents:
        print(f"Failed to retrieve torrent with ID {torrent_id}")
        return False

    current_labels = torrents[0].get("labels", [])

    new_labels = list(set(current_labels + [label]))
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
            "fields": ["id", "name", "status", "labels", "totalSize", "percentDone", "downloadedEver", "uploadedEver", "addedDate", "uploadRatio", "files"]
        }
    }
    headers = {"X-Transmission-Session-Id": session_id}
    response = requests.post(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS), json=payload, headers=headers)

    if response.status_code == 200:
        torrents = response.json()['arguments']['torrents']
        filtered_torrents = []
        for torrent in torrents:
            if (torrent_id is None or torrent["id"] == torrent_id) and label in torrent.get("labels", []) and (user.get("id", "common") in torrent.get("labels", []) or user.get("role", "user") == "admin"):
                status = get_torrent_status(torrent["status"])
                total_size = torrent["totalSize"]
                percent_done = torrent["percentDone"] * 100
                downloaded_ever = torrent["downloadedEver"]
                uploaded_ever = torrent["uploadedEver"]
                added_date = torrent["addedDate"]
                upload_ratio = round(torrent.get("uploadRatio", 0.0), 2)
                # files = [{"name": f["name"], "size": f["length"]} for f in torrent.get("files", [])]
                files = torrent.get("files", [])

                filtered_torrents.append({
                    "id": torrent["id"],
                    "labels": torrent.get("labels", []),
                    "name": torrent["name"],
                    "status": status,
                    "total_size": total_size,  # Size in bytes
                    "percent_done": percent_done, # Percentage
                    "downloaded_ever": downloaded_ever, # Bytes
                    "uploaded_ever": uploaded_ever, # Bytes
                    "added_date": added_date,
                    "files": files,
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
