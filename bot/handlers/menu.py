from telegram import Update

from bot.keyboards.main_menu import main_menu_keyboard
from bot.services.telegram import send_message


async def show_main_menu(update: Update):
    await send_message(
        update,
        "Choose an action",
        reply_markup=main_menu_keyboard(update.effective_user.id),
    )
