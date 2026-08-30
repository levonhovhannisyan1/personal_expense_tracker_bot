from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from telegram import Update
from telegram.ext import ConversationHandler

from bot.config import OWNER_ID, USERS


def is_authorized(user_id: int) -> bool:
    return user_id in USERS


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def get_user_name(user_id: int) -> str:
    return USERS[user_id]


def require_authorization(
    handler: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    @wraps(handler)
    async def wrapped(update: Update, *args: Any, **kwargs: Any) -> Any:
        user = update.effective_user
        if user and is_authorized(user.id):
            return await handler(update, *args, **kwargs)

        if update.callback_query:
            await update.callback_query.answer(
                "Access denied",
                show_alert=True,
            )
        elif update.effective_message:
            await update.effective_message.reply_text("Access denied")

        return ConversationHandler.END

    return wrapped


def require_owner(
    handler: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    @wraps(handler)
    async def wrapped(update: Update, *args: Any, **kwargs: Any) -> Any:
        user = update.effective_user
        if user and is_owner(user.id):
            return await handler(update, *args, **kwargs)

        if update.callback_query:
            await update.callback_query.answer(
                "Owner only",
                show_alert=True,
            )
        elif update.effective_message:
            await update.effective_message.reply_text("Owner only")

        return ConversationHandler.END

    return wrapped
