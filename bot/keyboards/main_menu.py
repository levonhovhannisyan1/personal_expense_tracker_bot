from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Expense", callback_data="add_expense"),
        ],
        [
            InlineKeyboardButton("💰 Add income", callback_data="add_income"),
            InlineKeyboardButton(
                "🏦 Set balance",
                callback_data="set_starting_savings",
            ),
        ],
        [
            InlineKeyboardButton("📋 Expenses", callback_data="expenses"),
            InlineKeyboardButton("📊 Statistics", callback_data="statistics"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)
