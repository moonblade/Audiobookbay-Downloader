
import os
import uvicorn
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Query, HTTPException, Depends, status as httpstatus, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.sessions import SessionMiddleware

# Updated imports
from models import TorrentRequest, CreateUserRequest, ChangePasswordRequest, User, TorrentClientType
from torrent_service import (
    init_torrent_service, get_torrents, add_torrent, delete_torrent, 
    pause_torrent, resume_torrent, remove_label_from_torrent_with_hash, delete_old_torrents
)
from audiobookbay import search_audiobook
from auth import add_user, change_password, delete_user, get_users, get_users_list, validate_admin_key, validate_key, validate_user
from beetsapi import autoimport
from constants import BEETS_ERROR_LABEL, TRANSMISSION_URL, TRANSMISSION_USER, TRANSMISSION_PASS, DECYPHARR_URL, DECYPHARR_PASSWORD, DECYPHARR_USERNAME, TORRENT_CLIENT_TYPE
from db import select_candidate
from utils import custom_logger

# App configuration
app = FastAPI()
SESSION_KEY = os.getenv("SESSION_KEY", "cp5oLmSZozoLZWHq")
TITLE = os.getenv("TITLE", "Audiobook Search")
AUTH_MODE = os.getenv("AUTH_MODE", "local")  # local, authentik

app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=SESSION_KEY)

logger = custom_logger(__name__)
security = HTTPBasic()

@app.on_event("startup")
async def startup_event():
    """Initialize torrent service on startup"""
    try:
        client_type = TorrentClientType(TORRENT_CLIENT_TYPE)

        if client_type == TorrentClientType.transmission:
            init_torrent_service(
                client_type=client_type,
                url=TRANSMISSION_URL,
                username=TRANSMISSION_USER,
                password=TRANSMISSION_PASS
            )
        elif client_type == TorrentClientType.decypharr:
            init_torrent_service(
                client_type=client_type,
                url=DECYPHARR_URL,
                username=DECYPHARR_USERNAME,
                password=DECYPHARR_PASSWORD
            )

        logger.info(f"Initialized torrent service with {client_type.value} client")
    except ValueError as e:
        logger.error(f"Invalid torrent client type: {TORRENT_CLIENT_TYPE}")
        raise RuntimeError(f"Invalid torrent client type: {TORRENT_CLIENT_TYPE}")
    except Exception as e:
        logger.error(f"Failed to initialize torrent service: {e}")
        raise RuntimeError(f"Failed to initialize torrent service: {e}")

def authenticate_authentik(request: Request):
    username = request.headers.get("X-authentik-username")
    id = request.headers.get("X-authentik-uid")
    role = "admin" if request.headers.get("X-authentik-role") == "admin" else "user"
    if not username:
        raise HTTPException(status_code=httpstatus.HTTP_401_UNAUTHORIZED, detail="Missing username header")
    logger.info(f"Authenticating user: {username}, role: {role}, id: {id}")
    return User(username=username, role=role, id=id)

def authenticate(request: Request):
    if AUTH_MODE == "authentik":
        return authenticate_authentik(request)
    user_id = request.session.get("user_id")
    if user_id:
        user_dict = validate_key(user_id)
        if user_dict:
            return User(
                username=user_dict["username"],
                role=user_dict["role"],
                id=user_dict["id"]
            )
    return None

def authenticate_userpass_authentik(request: Request):
    username = request.headers.get("X-authentik-username")
    id = request.headers.get("X-authentik-uid")
    role = "admin" if request.headers.get("X-authentik-role") == "admin" else "user"
    if not username:
        raise HTTPException(status_code=httpstatus.HTTP_401_UNAUTHORIZED, detail="Missing username header")
    request.session["user_id"] = id
    request.session["username"] = username
    request.session["role"] = role
    logger.info(f"Authenticating user: {username}, role: {role}, id: {id}")
    return User(username=username, role=role, id=id)

def authenticate_userpass(credentials: HTTPBasicCredentials = Depends(security)):
    user_dict = validate_user(credentials.username, credentials.password)
    if user_dict is None:
        raise HTTPException(
            status_code=httpstatus.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return User(
        username=user_dict["username"],
        role=user_dict["role"],
        id=user_dict["id"]
    )

def validate_admin(request: Request):
    if AUTH_MODE == "authentik":
        id = request.session.get("user_id")
        role = request.session.get("role")
        if role != "admin":
            raise HTTPException(status_code=403, detail="Access forbidden: Admins only")
        return User(
            username=request.session.get("username"),
            role=role,
            id=id
        )
    x_api_key = request.session.get("user_id")
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing x-api-key header")
    user_dict = validate_admin_key(x_api_key)
    if user_dict is None:
        raise HTTPException(status_code=401, detail="Invalid x-api-key")
    return User(
        username=user_dict["username"],
        role=user_dict["role"],
        id=user_dict["id"]
    )

@app.get("/")
def root(request: Request):
    if "user_id" not in request.session:
        return RedirectResponse("/login")
    return FileResponse(os.path.join("static", "index.html"))

@app.get("/title")
def title():
    return {"title": TITLE}

@app.get("/role")
def role(request: Request, user: User = Depends(authenticate)):
    if user:
        return {"role": user.role}
    else:
        return "Invalid credentials"

auth_pass_fn = authenticate_userpass_authentik if AUTH_MODE == "authentik" else authenticate_userpass

@app.get("/login")
async def login(request: Request, user: User = Depends(auth_pass_fn)):
    if user:
        request.session["user_id"] = user.id
        request.session["username"] = user.username
        request.session["role"] = user.role
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
    user: User = Depends(authenticate)
):
    """
    Searches for audiobooks based on the provided query.
    """
    try:
        results = search_audiobook(query)
        return {"results": results}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.post("/add")
def add(
    torrent: TorrentRequest,
    user: User = Depends(authenticate)
):
    """
    Adds a torrent to the download queue.
    """
    try:
        success = add_torrent(torrent.url, user)
        if success:
            return {"status": "ok", "message": "Torrent added successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add torrent")
    except Exception as e:
        logger.error(f"Add failed: {e}")
        raise HTTPException(status_code=500, detail="Add failed")

@app.get("/list")
def list_torrents(user: User = Depends(authenticate)):
    """
    Lists all torrents in the download queue.
    """
    try:
        return get_torrents(user)
    except Exception as e:
        logger.error(f"List torrents failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list torrents")

@app.delete("/torrent/{torrent_id}")
def delete_torrent_endpoint(
    torrent_id: int,
    delete_data: bool = Query(True, description="Delete downloaded data as well"),
    user: User = Depends(authenticate)
):
    """
    Deletes a torrent.
    """
    try:
        if delete_torrent(torrent_id, user, delete_data=delete_data):
            return {"status": "ok", "message": f"Torrent {torrent_id} deleted successfully."}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete torrent {torrent_id}")
    except Exception as e:
        logger.error(f"Delete torrent failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delete torrent failed: {e}")

@app.post("/torrent/{torrent_id}/pause")
def pause_torrent_endpoint(
    torrent_id: int,
    user: User = Depends(authenticate)
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
    user: User = Depends(authenticate)
):
    """
    Plays/resumes a torrent.
    """
    try:
        if resume_torrent(torrent_id, user):
            return {"status": "ok", "message": f"Torrent {torrent_id} resumed successfully."}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to resume torrent {torrent_id}")
    except Exception as e:
        logger.error(f"Resume torrent failed: {e}")
        raise HTTPException(status_code=500, detail=f"Resume torrent failed: {e}")

@app.post("/selectCandidate/{hash_string}/{candidate_id}")
def select_candidate_endpoint(hash_string: str, candidate_id: str, user: User = Depends(authenticate)):
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
def autoimport_endpoint():
    """
    Imports beets audible stuff to new directory.
    """
    try:
        autoimport()
        delete_old_torrents()
        return {"status": "ok", "message": "Auto-import completed successfully"}
    except Exception as e:
        logger.error(f"Auto-import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-import failed: {e}")

# User management endpoints
@app.put("/users")
def add_user_endpoint(createUserRequest: CreateUserRequest, user: User = Depends(validate_admin)):
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
def get_users_endpoint(user: User = Depends(validate_admin)):
    """
    Retrieves the user details.
    """
    try:
        return get_users_list()
    except Exception as e:
        logger.error(f"Get users failed: {e}")
        raise HTTPException(status_code=500, detail="Get users failed")

@app.delete("/users/{id}")
def delete_user_endpoint(id: str, user: User = Depends(validate_admin)):
    """
    Deletes a user from the database.
    """
    try:
        delete_user(id)
        return {"status": "ok", "message": "User deleted successfully"}
    except Exception as e:
        logger.error(f"Delete user failed: {e}")
        raise HTTPException(status_code=500, detail="Delete user failed")

@app.post("/change_password")
def change_password_endpoint(changePasswordRequest: ChangePasswordRequest, user: User = Depends(validate_admin)):
    """
    Changes the password for a user.
    """
    try:
        change_password(changePasswordRequest.id, changePasswordRequest.password)
        return {"status": "ok", "message": "Password changed successfully"}
    except Exception as e:
        logger.error(f"Change password failed: {e}")
        raise HTTPException(status_code=500, detail="Change password failed")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)

