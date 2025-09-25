from enum import Enum
from pydantic import BaseModel
from typing import Optional

class TorrentClientType(str, Enum):
    transmission = "transmission"
    decypharr = "decypharr"

class User(BaseModel):
    username: str = "default"
    role: str = "user" 
    id: str = "default"

# Request models moved from main.py
class TorrentRequest(BaseModel):
    url: str

class CreateUserRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    id: str
    password: str

