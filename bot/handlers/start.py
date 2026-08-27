from telegram import Update
from telegram.ext import ContextTypes

from bot.services.telegram import send_message
from bot.utils.authorization import get_user_name, is_authorized
from bot.keyboards.main_menu import main_menu_keyboard
from bot.database.users import get_or_create_user


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    if not is_authorized(user_id):
        await send_message(
            update,
            "Access denied",
        )
        return

    name = get_user_name(user_id)
    get_or_create_user(user_id, name)

    await send_message(
        update,
        f"Welcome {name}\n\nChoose an action",
        reply_markup=main_menu_keyboard(),
    )
