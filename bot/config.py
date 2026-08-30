import os

from dotenv import load_dotenv


load_dotenv()

def required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


BOT_TOKEN = required_setting("BOT_TOKEN")
OWNER_ID = int(required_setting("OWNER_ID"))
USER_ID = int(required_setting("USER_ID"))

OWNER_NAME = required_setting("OWNER_NAME")
USER_NAME = required_setting("USER_NAME")

if OWNER_ID == USER_ID:
    raise RuntimeError("OWNER_ID and USER_ID must be different")

USERS = {
    OWNER_ID: OWNER_NAME,
    USER_ID: USER_NAME,
}

ALLOWED_USERS = set(USERS)
