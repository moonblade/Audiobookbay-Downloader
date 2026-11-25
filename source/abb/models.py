from enum import Enum
from typing import Optional
from pydantic import BaseModel

class TorrentClientType(str, Enum):
    transmission = "transmission"
    decypharr = "decypharr"
    qbittorrent = "qbittorrent"

class User(BaseModel):
    username: str = "default"
    role: str = "user" 
    id: str = "default"

class TorrentRequest(BaseModel):
    url: str
    query: Optional[str] = None  # original search query, used for ebook companion search
