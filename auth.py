import json
import os
import base64
import requests
import uuid

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "YWRtaW4=")
ADMIN_ID = os.getenv("ADMIN_ID", "e0617896-4560-193c-cc34-653683f99c35")
DB_PATH = os.getenv("DB_PATH", "/tmp")
# DB_PATH/users.json returns a json of type [{"username": "user1", "password": "cGFzc3dvcmQ=", "role": "user", "id": "userapikey"}]


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
    return [{"username": user.get("username", "invalid"), "role": user.get("role", "user"), "id": user.get("id", "0")} for user in users]

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
