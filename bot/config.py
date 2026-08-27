import os

from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = int(os.getenv("OWNER_ID"))
USER_ID = int(os.getenv("USER_ID"))

OWNER_NAME = os.getenv("OWNER_NAME")
USER_NAME = os.getenv("USER_NAME")

USERS = {
    OWNER_ID: OWNER_NAME,
    USER_ID: USER_NAME,
}

ALLOWED_USERS = set(USERS)