import time
from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB_NAME

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

messages_col = db["messages"]
mutes_col = db["mutes"]


def init_db():
    messages_col.create_index("group_msg_id", unique=True)
    messages_col.create_index("user_id")
    mutes_col.create_index("user_id", unique=True)


def save_message_link(group_msg_id: int, user_id: int, username: str, fullname: str):
    messages_col.update_one(
        {"group_msg_id": group_msg_id},
        {
            "$set": {
                "group_msg_id": group_msg_id,
                "user_id": user_id,
                "user_username": username,
                "user_fullname": fullname,
                "created_at": time.time()
            }
        },
        upsert=True
    )


def get_message_link(group_msg_id: int) -> dict | None:
    doc = messages_col.find_one({"group_msg_id": group_msg_id})
    if doc is None:
        return None
    return {
        "user_id": doc["user_id"],
        "user_username": doc.get("user_username"),
        "user_fullname": doc.get("user_fullname")
    }


def get_user_id_by_group_msg(group_msg_id: int) -> int | None:
    doc = messages_col.find_one({"group_msg_id": group_msg_id}, {"user_id": 1})
    if doc is None:
        return None
    return doc["user_id"]


def mute_user(user_id: int, duration_seconds: float, reason: str = None):
    muted_until = time.time() + duration_seconds
    mutes_col.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "muted_until": muted_until,
                "reason": reason
            }
        },
        upsert=True
    )


def unmute_user(user_id: int):
    mutes_col.delete_one({"user_id": user_id})


def is_muted(user_id: int) -> tuple:
    doc = mutes_col.find_one({"user_id": user_id})
    if doc is None:
        return False, None

    muted_until = doc["muted_until"]
    if muted_until <= time.time():
        mutes_col.delete_one({"user_id": user_id})
        return False, None

    return True, muted_until