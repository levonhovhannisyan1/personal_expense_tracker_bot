from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import OWNER_ID
from bot.services.savings_service import has_opening_savings


def main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Expense", callback_data="add_expense"),
        ],
    ]

    if user_id == OWNER_ID:
        has_balance = has_opening_savings(user_id)
        keyboard.append(
            [
                InlineKeyboardButton("💰 Add income", callback_data="add_income"),
                InlineKeyboardButton(
                    "💵 Adjust balance" if has_balance else "🏦 Set balance",
                    callback_data="adjust_balance" if has_balance else "set_starting_savings",
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
