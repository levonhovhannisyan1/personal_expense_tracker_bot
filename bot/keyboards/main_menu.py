from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import OWNER_ID


def main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Expense", callback_data="add_expense"),
        ],
    ]

    if user_id == OWNER_ID:
        keyboard.append(
            [
                InlineKeyboardButton("💰 Add income", callback_data="add_income"),
                InlineKeyboardButton(
                    "🏦 Set balance",
                    callback_data="set_starting_savings",
                ),
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton("📋 Expenses", callback_data="expenses"),
            InlineKeyboardButton("📊 Statistics", callback_data="statistics"),
        ]
    )

    return InlineKeyboardMarkup(keyboard)
