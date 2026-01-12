"""Simple auth service for MVP: in-memory users, password hashing, token generation.
This is intentionally small and dependency-free (uses hashlib/pbkdf2_hmac).
Replace with a persistent store for production.

Tokens have a 7-day expiry by default for MVP.
"""
import uuid
import secrets
import hashlib
import hmac
import base64
from typing import Optional
from datetime import datetime, timedelta, timezone

USERS = {}  # username -> user dict
# TOKENS: token -> {user_id: str, expires_at: datetime}
TOKENS = {}


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${base64.b64encode(dk).decode()}"


def _verify_password(stored: str, password: str) -> bool:
    try:
        salt, hashed = stored.split("$", 1)
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return hmac.compare_digest(base64.b64encode(dk).decode(), hashed)


def create_user(username: str, password: str, display_name: Optional[str] = None) -> dict:
    if username in USERS:
        raise ValueError("username_exists")
    uid = str(uuid.uuid4())
    USERS[username] = {
        "id": uid,
        "username": username,
        "display_name": display_name,
        "password": _hash_password(password),
        "level": 1,
        "xp": 0,
    }
    return USERS[username]


def authenticate(username: str, password: str) -> Optional[dict]:
    u = USERS.get(username)
    if not u:
        return None
    if _verify_password(u["password"], password):
        return u
    return None


def create_token(user_id: str, days_valid: int = 7) -> str:
    """Create a token valid for `days_valid` days (default: 7)."""
    token = secrets.token_hex(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=days_valid)
    TOKENS[token] = {"user_id": user_id, "expires_at": expires_at}
    return token


def get_user_by_token(token: str) -> Optional[dict]:
    info = TOKENS.get(token)
    if not info:
        return None
    if info["expires_at"] < datetime.now(timezone.utc):
        # token expired
        TOKENS.pop(token, None)
        return None
    uid = info["user_id"]
    for u in USERS.values():
        if u["id"] == uid:
            return u
    return None


def add_xp(user_identifier: str, xp: int) -> bool:
    """Add XP to a user; user_identifier can be user id or username.
    Returns True if user found and updated. Also handles level ups.
    """
    from ..config import LEVEL_BASE_XP
    for u in USERS.values():
        if u.get("id") == user_identifier or u.get("username") == user_identifier:
            u["xp"] = u.get("xp", 0) + xp
            # Level-up: while xp exceeds threshold, increment level
            leveled = False
            while True:
                current_level = u.get("level", 1)
                threshold = current_level * LEVEL_BASE_XP
                if u["xp"] >= threshold:
                    u["level"] = current_level + 1
                    leveled = True
                else:
                    break
            return True
    return False


def get_user_by_username(username: str) -> Optional[dict]:
    return USERS.get(username)


def prune_expired_tokens() -> int:
    """Remove expired tokens. Return count removed."""
    now = datetime.now(timezone.utc)
    removed = 0
    for t, info in list(TOKENS.items()):
        if info["expires_at"] < now:
            TOKENS.pop(t, None)
            removed += 1
    return removed