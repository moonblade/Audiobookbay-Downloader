from datetime import datetime
from typing import Optional
from auth import add_user, change_password, delete_user, get_users, get_users_list, validate_admin_key, validate_key, validate_user
from pydantic import BaseModel
from audiobookbay import get_torrents, search_audiobook, add_to_transmission
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
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=SESSION_KEY)

logger = custom_logger(__name__)

security = HTTPBasic()

def authenticate(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        user = validate_key(user_id)
        if user:
            return user
    return None

def authenticate_userpass(credentials: HTTPBasicCredentials = Depends(security)):
    user = validate_user(credentials.username, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=httpstatus.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

def validate_admin(request: Request):
    x_api_key = request.session.get("user_id")
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing x-api-key header")
    user = validate_admin_key(x_api_key)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid x-api-key")
    return user

@app.get("/")
def root(request: Request):
    if "user_id" not in request.session:
        return RedirectResponse("/login")
    return FileResponse(os.path.join("static", "index.html"))

@app.get("/role")
def role(request: Request, user: dict = Depends(authenticate_userpass)):
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
        return RedirectResponse("/")
    else:
        return "Invalid credentials"

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login_page")

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

