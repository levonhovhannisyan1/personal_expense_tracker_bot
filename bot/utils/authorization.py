from bot.config import USERS


def is_authorized(user_id: int) -> bool:
    return user_id in USERS


def get_user_name(user_id: int) -> str:
    return USERS[user_id]