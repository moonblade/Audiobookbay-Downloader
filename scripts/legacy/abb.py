import requests
import json

# Configuration
JACKETT_API_URL = "https://jackett.sirius.moonblade.work/api/v2.0/indexers/audiobookbay/results"
JACKETT_API_KEY = "teyreu39x1pgoeniz94ytixujq41wbxf"
TRANSMISSION_URL = "https://transmission.sirius.moonblade.work/transmission/rpc"
TRANSMISSION_USER = ""
TRANSMISSION_PASS = ""

def resolve_redirect(url):
    response = requests.get(url, allow_redirects=False)  # Depth limited to 1
    if response.status_code in [301, 302]:
        return response.headers.get("Location", url)
    return url

def search_audiobook(query):
    params = {
        "apikey": JACKETT_API_KEY,
        "Query": query,
        "Category": "audiobooks"
    }
    response = requests.get(JACKETT_API_URL, params=params)
    
    if response.status_code != 200:
        print("Error fetching results from Jackett:", response.text)
        return []
    
    results = response.json()
    return results.get("Results", [])


def add_to_transmission(torrent_url):
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
    
    response = requests.post(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS),
                             json=payload, headers=headers)
    
    return response.status_code == 200


def main():
    query = input("Enter audiobook search term: ")
    results = search_audiobook(query)
    
    if not results:
        print("No results found.")
        return
    
    for i, result in enumerate(results[:5]):  # Show top 5 results
        print(f"{i+1}. {result['Title']} - {result['Size']/1024/1024:.2f} MB")
    
    choice = int(input("Select a number to download: ")) - 1
    
    if 0 <= choice < len(results):
        torrent_url = results[choice]["Link"]
        torrent_url = resolve_redirect(torrent_url)
        with open("/tmp/torrent_url.txt", "w") as f:
            f.write(torrent_url)
        success = add_to_transmission(torrent_url)
        if success:
            print("Torrent added successfully!")
        else:
            print("Failed to add torrent.")
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()

