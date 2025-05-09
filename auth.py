import json
import os
import base64
import requests
import uuid
import time

from constants import ADMIN_ID, ADMIN_PASS, ADMIN_USER, DB_PATH



def get_users():
    users_url = os.path.join(DB_PATH, "users.json")
    if not os.path.exists(users_url):
        return []
    with open(users_url, "r") as f:
        users = json.loads(f.read())
    return users

def validate_admin_key(key):
    if key == ADMIN_ID:
        return {"username": ADMIN_USER, "role": "admin", "id": ADMIN_ID}
    return None

def validate_key(key):
    if key == ADMIN_ID:
        return {"username": ADMIN_USER, "role": "admin", "id": ADMIN_ID}
    users = get_users()
    for user in users:
        if user.get("id", "0") == key:
            return {"username": user.get("username", "invalid"), "role": user.get("role", "user"), "id": user.get("id", "0")}
    return None

def update_last_seen(user_id):
    users = get_users()
    for user in users:
        if user.get("id", "0") == user_id:
            user["last_seen"] = int(time.time())
            break
    users_url = os.path.join(DB_PATH, "users.json")
    with open(users_url, "w") as f:
        f.write(json.dumps(users))
    return True

def validate_user(username, password):
    base64_password = base64.b64encode(password.encode("utf-8")).decode("utf-8")
    if username == ADMIN_USER and base64_password == ADMIN_PASS:
        return {"username": username, "role": "admin", "id": ADMIN_ID}
    users = get_users()
    for user in users:
        if user.get("username", "invalid") == username:
            base64_password = user.get("password", "")
            valid = base64.b64decode(base64_password).decode("utf-8") == password
            if not valid:
                return None
            update_last_seen(user.get("id", "0"))
            return {"username": username, "role": user.get("role", "user"), "id": user.get("id", "0")}

def add_user(username, password):
    base64_password = base64.b64encode(password.encode("utf-8")).decode("utf-8")
    users = get_users()
    users.append({"username": username, "password": base64_password, "role": "user", "id": str(uuid.uuid4())})
    users_url = os.path.join(DB_PATH, "users.json")
    with open(users_url, "w") as f:
        f.write(json.dumps(users))
    return True

def get_users_list():
    users = get_users()
    return [{"username": user.get("username", "invalid"), "role": user.get("role", "user"), "id": user.get("id", "0"), "last_seen": "never" if user.get("last_seen", 0) == 0 else time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(user.get("last_seen", 0)))} for user in users]

def change_password(id, password):
    base64_password = base64.b64encode(password.encode("utf-8")).decode("utf-8")
    users = get_users()
    for user in users:
        if user.get("id", "0") == id:
            user["password"] = base64_password
            break
    users_url = os.path.join(DB_PATH, "users.json")
    with open(users_url, "w") as f:
        f.write(json.dumps(users))
    return True

def delete_user(id):
    users = get_users()
    users = [user for user in users if user.get("id", "0") != id]
    users_url = os.path.join(DB_PATH, "users.json")
    with open(users_url, "w") as f:
        f.write(json.dumps(users))
    return True
