import json
import os
from itertools import chain
import beets.importer as importer
from beets.ui.commands import AlbumChange, PromptChoice
from beets.library import Library
from beets import config, plugins
from beets.autotag import Recommendation

from audiobookbay import add_label_to_torrent, get_torrents
from constants import ADMIN_USER_DICT, BEETS_COMPLETE_LABEL, BEETS_DIR, BEETS_ERROR_LABEL, BEETS_INPUT_PATH
from db import get_candidates, save_candidates
from utils import custom_logger

logger = custom_logger(__name__)

plugins.load_plugins(str(config["plugins"]).split(" "))
# logger.info(config)

lib = Library(os.path.join(BEETS_DIR, "library.db"), directory=config["directory"].get())

class ProgrammaticImportSession(importer.ImportSession):
    def __init__(self, lib, loghandler, paths, query, torrent):
        super(ProgrammaticImportSession, self).__init__(lib, loghandler, paths, query)
        self.torrent = torrent

    def summary_judgement(self, rec):
        """Determines whether a decision should be made without even asking
        the user. This occurs in quiet mode and when an action is chosen for
        NONE recommendations. Return None if the user should be queried.
        Otherwise, returns an action. May also print to the console if a
        summary judgment is made.
        """
        if rec == Recommendation.strong:
            return importer.action.APPLY
        if config["import"]["quiet"]:
            action = importer.action.SKIP
            if rec != Recommendation.strong:
                action = config["import"]["quiet_fallback"].as_choice(
                    {
                        "skip": importer.action.SKIP,
                        "asis": importer.action.ASIS,
                    }
                )
        elif config["import"]["timid"]:
            return None
        elif rec == Recommendation.none:
            action = config["import"]["none_rec_action"].as_choice(
                {
                    "skip": importer.action.SKIP,
                    "asis": importer.action.ASIS,
                    "ask": None,
                }
            )
        else:
            return None

        if action == importer.action.SKIP:
            logger.info("Skipping.")
        elif action == importer.action.ASIS:
            logger.info("Using as-is.")
        return action

    def show_change(self, cur_artist, cur_album, match):
        # print(cur_artist, cur_album, match)
        pass

    def seconds_to_hours_and_minutes(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return hours, minutes

    def transform_candidates(self, task):
        candidates = []
        for candidate in task.candidates:
            length = sum([track.length for track in candidate.info.tracks])
            hours, minutes = self.seconds_to_hours_and_minutes(length)
            time_string = f"{hours} hrs, {minutes} min"
            candidateObject = {
                "match": round((1 - candidate.distance.distance)*100),
                "artist": candidate.info.artist,
                "album": candidate.info.album,
                "cover": candidate.info.cover_url,
                "id": candidate.info.album_id,
                "length": time_string,
            }
            candidates.append(candidateObject)
        return candidates

    def get_saved_choice(self, task):
        return None

    def save_candidates(self, task):
        saved_candidates = get_candidates(self.torrent.get("id"))
        if saved_candidates:
            return

        candidates = self.transform_candidates(task)
        save_candidates(self.torrent.get("id"), candidates)

    def choose_match(self, task):
        plugins.send("import_task_before_choice", session=self, task=task)
        action = self.summary_judgement(task.rec)
        if action == importer.action.APPLY:
            match = task.candidates[0]
            self.show_change(task.cur_artist, task.cur_album, match)
            return match

        saved_choice = self.get_saved_choice(task)
        if saved_choice is not None:
            return saved_choice

        self.save_candidates(task)
        # choices = self._get_choices(task)

    def choose_item(self, task):
        return

    def resolve_duplicates(self, task, found_duplicates):
        logger.info(task)
        logger.info(found_duplicates)
        return

    def should_resume(self, path):
        return

    def _get_choices(self, task):
        choices = [
            PromptChoice("a", "Apply", None),
            PromptChoice("u", "Use as-is", lambda s, t: importer.action.ASIS),
        ]
        # We dont particularly care for the choices given by the plugin, so ignoring it
        return choices

def getFolders(torrent):
    folders = set()
    for file in torrent.get("files"):
        folders.add(os.path.join(BEETS_INPUT_PATH, file.get("name").split("/")[0]))
    return list(folders)

def autoimport():
    torrents = get_torrents(ADMIN_USER_DICT)
    # torrents = [torrent for torrent in torrents if "Perfect Run" in torrent.get("name")]
    torrents = [torrent for torrent in torrents if ("audiobook" in torrent.get("labels") and BEETS_COMPLETE_LABEL not in torrent.get("labels") and BEETS_ERROR_LABEL not in torrent.get("labels"))]
    if not torrents:
        logger.warn("No torrents found")
        return
    logger.info(f"Found {len(torrents)} torrents")
    for torrent in torrents:
        try:
            if torrent["status"] != "Seeding":
                continue
            logger.info(f"Processing {torrent['name']}")
            folders = getFolders(torrent)
            session = ProgrammaticImportSession(
                lib,
                loghandler=logger,
                paths=folders,
                query=None,
                torrent=torrent
            )
            session.run()
            add_label_to_torrent(torrent.get("id"), ADMIN_USER_DICT, BEETS_COMPLETE_LABEL)
        except Exception as e:
            logger.exception(f"Import failed: {e}")
            add_label_to_torrent(torrent.get("id"), ADMIN_USER_DICT, BEETS_ERROR_LABEL)
