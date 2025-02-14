import os
import base64
import requests

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "YWRtaW4=")
ADMIN_ID = os.getenv("ADMIN_ID", "e0617896-4560-193c-cc34-653683f99c35")
USERSURL = os.getenv("USERSURL", "")
# USERSURL returns a json of type {"users": [{"username": "user1", "password": "cGFzc3dvcmQ=", "role": "user"}]}


def get_users():
    if not USERSURL:
        return {"users": []}
    response = requests.get(USERSURL)
    response.raise_for_status()
    users = response.json()
    return users

def validate_key(key):
    if key == ADMIN_ID:
        return {"username": ADMIN_USER, "role": "admin", "id": ADMIN_ID}
    users = get_users().get("users", [])
    for user in users:
        if user.get("id", "0") == key:
            return {"username": user.get("username", "invalid"), "role": user.get("role", "user"), "id": user.get("id", "0")}
    return None

def validate_user(username, password):
    base64_password = base64.b64encode(password.encode("utf-8")).decode("utf-8")
    if username == ADMIN_USER and base64_password == ADMIN_PASS:
        return {"username": username, "role": "admin", "id": ADMIN_ID}
    users = get_users().get("users", [])
    for user in users:
        if user.get("username", "invalid") == username:
            base64_password = user.get("password", "")
            valid = base64.b64decode(base64_password).decode("utf-8") == password
            if not valid:
                return None
            return {"username": username, "role": user.get("role", "user"), "id": user.get("id", "0")}
