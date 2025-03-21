import os
from constants import DB_PATH
from tinydb import TinyDB, Query

beetsdb = TinyDB(os.path.join(DB_PATH, "beets.json"))
# {
#     "torrent_id": "1",
#     "candidates": [
#           {
#             "match": 85,
#             "artist": "Maxime J. Durand, Void Herald",
#             "album": "The Perfect Run 3",
#             "cover": "https://m.media-amazon.com/images/I/91ePRUrVbUL.jpg",
#             "id": "B09SVQLY96",
#             "length": "18 hrs, 14 min"
#           }
#     ],
#     "selected": "B09SVQLY96"
# }

def get_entry(torrent_id):
    return beetsdb.get(Query().torrent_id == torrent_id)

def get_candidates(torrent_id):
    entry = get_entry(torrent_id)
    if entry:
        return entry.get("candidates", [])

def get_selected(torrent_id):
    entry = get_entry(torrent_id)
    if entry:
        return entry.get("selected", None)

def save_candidates(torrent_id, candidates):
    entry = get_entry(torrent_id)
    if entry:
        beetsdb.update({"candidates": candidates}, Query().torrent_id == torrent_id)
    else:
        beetsdb.insert({"torrent_id": torrent_id, "candidates": candidates})

def select_candidate(torrent_id, candidate_id):
    beetsdb.update({"selected": candidate_id}, Query().torrent_id == torrent_id)
