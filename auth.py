import os
import base64
import requests

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "YWRtaW4=")
USERSURL = os.getenv("USERSURL", "")

def get_users():
    response = requests.get(USERSURL)
    response.raise_for_status()
    users = response.json()
    return users

def validate_user(username, password):
    base64_password = base64.b64encode(password.encode("utf-8")).decode("utf-8")
    if username == ADMIN_USER and base64_password == ADMIN_PASS:
        return {"username": username, "role": "admin"}
    users = get_users().get("users", [])
    for user in users:
        if user.get("username", "invalid") == username:
            base64_password = user.get("password", "")
            valid = base64.b64decode(base64_password).decode("utf-8") == password
            if not valid:
                return None
            return {"username": username, "role": user.get("role", "user")}
