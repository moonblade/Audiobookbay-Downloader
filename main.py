from datetime import datetime, timedelta
from typing import Optional
from auth import add_user, change_password, delete_user, get_users, get_users_list, validate_admin_key, validate_key, validate_user
from beetsapi import autoimport
from constants import BEETS_ERROR_LABEL
from db import select_candidate
from pydantic import BaseModel
from audiobookbay import delete_old_torrents, delete_torrent, get_torrents, pause_torrent, play_torrent, remove_label_from_torrent, remove_label_from_torrent_with_hash, search_audiobook, add_to_transmission
from fastapi import FastAPI, Query, HTTPException, Depends, status as httpstatus, Header, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from utils import custom_logger
import uvicorn
import os

app = FastAPI()

SESSION_KEY = os.getenv("SESSION_KEY", "cp5oLmSZozoLZWHq")
TITLE = os.getenv("TITLE", "Audiobook Search")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=SESSION_KEY)

logger = custom_logger(__name__)

security = HTTPBasic()

def authenticate(request: Request):
    username = request.headers.get("X-authentik-username")
    id = request.headers.get("X-authentik-uid")
    role = "admin" if request.headers.get("X-authentik-role") == "admin" else "user"
    if not username:
        raise HTTPException(status_code=httpstatus.HTTP_401_UNAUTHORIZED, detail="Missing username header")
    logger.info(f"Authenticating user: {username}, role: {role}, id: {id}")
    return {"username": username, "role": role, "id": id}

def authenticate_userpass(request: Request):
    username = request.headers.get("X-authentik-username")
    id = request.headers.get("X-authentik-uid")
    role = "admin" if request.headers.get("X-authentik-role") == "admin" else "user"
    if not username:
        raise HTTPException(status_code=httpstatus.HTTP_401_UNAUTHORIZED, detail="Missing username header")
    request.session["user_id"] = id
    request.session["username"] = username
    request.session["role"] = role
    logger.info(f"Authenticating user: {username}, role: {role}, id: {id}")
    return {"username": username, "role": role, "id": id}

def validate_admin(request: Request):
    id = request.session.get("user_id")
    role = request.session.get("role")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden: Admins only")
    return {"username": request.session.get("username"), "role": role, "id": id}

@app.get("/")
def root(request: Request):
    if "user_id" not in request.session:
        return RedirectResponse("/login")
    return FileResponse(os.path.join("static", "index.html"))

@app.get("/title")
def title():
    return {"title": TITLE}

@app.get("/role")
def role(request: Request, user: dict = Depends(authenticate)):
    if user:
        return {"role": user["role"]}
    else:
        return "Invalid credentials"

@app.get("/login")
def login_page(request: Request, user: dict = Depends(authenticate_userpass)):
    if user:
        request.session["user_id"] = user["id"]
        request.session["username"] = user["username"]
        request.session["role"] = user["role"]
        #
        # # Set a long-lived cookie (one year)
        # expiry_date = datetime.utcnow() + timedelta(days=365)
        # expiry_str = expiry_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
        #
        # request.session.cookie["user_id"] = user["id"]
        # request.session.cookie["user_id"]["expires"] = expiry_str
        # request.session.cookie["user_id"]["samesite"] = "Lax"
        # request.session.cookie["user_id"]["secure"] = True
        # request.session.cookie["user_id"]["httponly"] = True

        return RedirectResponse("/")
    else:
        return "Invalid credentials"

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    response = RedirectResponse("/login")
    response.delete_cookie("user_id")
    return response

def status():
    now = datetime.utcnow().isoformat() + "Z"
    return {"status": "ok", "timestamp": now}

@app.get("/search")
def search(
    query: str = Query(..., description="Search query"),
    user: str = Depends(authenticate)
):
    """
    Searches a webpage based on the provided query and page number.
    """
    try:
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
    user: str = Depends(authenticate)
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
def list(user: str = Depends(authenticate)):
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

@app.delete("/torrent/{torrent_id}")
def delete_torrent_endpoint(
    torrent_id: int,
    delete_data: bool = Query(True, description="Delete downloaded data as well"),
    user: dict = Depends(authenticate) # Requires authentication
):
    """
    Deletes a torrent.
    """
    try:
        if delete_torrent(torrent_id, delete_data=delete_data, user=user):  # Pass user to delete_torrent
            return {"status": "ok", "message": f"Torrent {torrent_id} deleted successfully."}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete torrent {torrent_id}")
    except Exception as e:
        logger.error(f"Delete torrent failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delete torrent failed: {e}")

@app.post("/torrent/{torrent_id}/pause")
def pause_torrent_endpoint(
    torrent_id: int,
    user: dict = Depends(authenticate) # Requires authentication
):
    """
    Pauses a torrent.
    """
    try:
        if pause_torrent(torrent_id, user):
            return {"status": "ok", "message": f"Torrent {torrent_id} paused successfully."}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to pause torrent {torrent_id}")
    except Exception as e:
        logger.error(f"Pause torrent failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pause torrent failed: {e}")

@app.post("/torrent/{torrent_id}/play")
def play_torrent_endpoint(
    torrent_id: int,
    user: dict = Depends(authenticate) # Requires authentication
):
    """
    Plays a torrent.
    """
    try:
        if play_torrent(torrent_id, user):
            return {"status": "ok", "message": f"Torrent {torrent_id} played successfully."}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to play torrent {torrent_id}")
    except Exception as e:
        logger.error(f"Play torrent failed: {e}")
        raise HTTPException(status_code=500, detail=f"Play torrent failed: {e}")

@app.post("/selectCandidate/{hash_string}/{candidate_id}")
def _select_candidate(hash_string: str, candidate_id: str, user: dict = Depends(authenticate)):
    """
    Selects a candidate for a torrent.
    """
    try:
        select_candidate(hash_string, candidate_id)
        remove_label_from_torrent_with_hash(hash_string, user, BEETS_ERROR_LABEL)
        return {"status": "ok", "message": f"Candidate {candidate_id} selected for torrent {hash_string}"}
    except Exception as e:
        logger.error(f"Select candidate failed: {e}")
        raise HTTPException(status_code=500, detail=f"Select candidate failed: {e}")

@app.post("/autoimport")
def _autoimport():
    """
    Imports beets audible stuff to new directory.
    """
    autoimport()
    delete_old_torrents()
