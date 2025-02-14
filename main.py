from datetime import datetime

from auth import add_user, change_password, delete_user, get_users, validate_admin_key, validate_key, validate_user
from pydantic import BaseModel
from audiobookbay import get_torrents, search_audiobook, add_to_transmission
from fastapi import FastAPI, Query, HTTPException, Depends, status as httpstatus, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from utils import custom_logger
import uvicorn
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

logger = custom_logger(__name__)

security = HTTPBasic()
authkey = HTTPBasic()
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    user = validate_user(credentials.username, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=httpstatus.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

def validate_admin(x_api_key: str = Header(None)):
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing x-api-key header")
    user = validate_admin_key(x_api_key)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid x-api-key")
    return user

def validate_api_key(x_api_key: str = Header(None)):
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing x-api-key header")
    user = validate_key(x_api_key)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid x-api-key")
    return user

@app.get("/")
def root():
    return FileResponse(os.path.join("static", "index.html"))

@app.get("/login")
def login(userdetails: str = Depends(authenticate)):
    return userdetails

@app.get("/status")
def status():
    now = datetime.utcnow().isoformat() + "Z"
    return {"status": "ok", "timestamp": now}

@app.get("/search")
def search(
    query: str = Query(..., description="Search query"),
    user: str = Depends(validate_api_key)
):
    """
    Searches a webpage based on the provided query and page number.
    """
    try:
        logger.info(user)
        results = search_audiobook(query)
        return {"results": results}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

class TorrentRequest(BaseModel):
    url: str

@app.post("/add")
def add(
    torrent: TorrentRequest,
    user: str = Depends(validate_api_key)
):
    """
    Adds a torrent to the download queue.
    """
    try:
        success = add_to_transmission(torrent.url, user)
        if success:
            return {"status": "ok", "message": "Torrent added successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add torrent")
    except Exception as e:
        logger.error(f"Add failed: {e}")
        raise HTTPException(status_code=500, detail="Add failed")

@app.get("/list")
def list(user: str = Depends(validate_api_key)):
    """
    Lists all torrents in the download queue.
    """
    return get_torrents(user)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True) 

class CreateUserRequest(BaseModel):
    username: str
    password: str
@app.put("/users")
def _add_user(createUserRequest: CreateUserRequest, user: str = Depends(validate_admin)):
    """
    Adds a user to the database.
    """
    try:
        add_user(createUserRequest.username, createUserRequest.password)
        return {"status": "ok", "message": "User added successfully"}
    except Exception as e:
        logger.error(f"Add user failed: {e}")
        raise HTTPException(status_code=500, detail="Add user failed")

@app.get("/users")
def _get_user(user: str = Depends(validate_admin)):
    """
    Retrieves the user details.
    """
    return get_users_list()

@app.delete("/users/{id}")
def _delete_user(id: str, user: str = Depends(validate_admin)):
    """
    Deletes a user from the database.
    """
    try:
        delete_user(id)
        return {"status": "ok", "message": "User deleted successfully"}
    except Exception as e:
        logger.error(f"Delete user failed: {e}")
        raise HTTPException(status_code=500, detail="Delete user failed")

class ChangePasswordRequest(BaseModel):
    id: str
    password: str

@app.post("/change_password")
def _change_password(changePasswordRequest: ChangePasswordRequest, user: str = Depends(validate_admin)):
    """
    Changes the password for a user.
    """
    try:
        change_password(changePasswordRequest.id, changePasswordRequest.password)
        return {"status": "ok", "message": "Password changed successfully"}
    except Exception as e:
        logger.error(f"Change password failed: {e}")
        raise HTTPException(status_code=500, detail="Change password failed")

