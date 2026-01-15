import re

USERNAME_REGEX = r"^[a-zA-Z0-9_-]+$"

def validate_username(username: str) -> bool:
    return bool(re.match(USERNAME_REGEX, username))
