from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Expense", callback_data="add_expense"),
        ],
        [
            InlineKeyboardButton("📋 Expenses", callback_data="expenses"),
            InlineKeyboardButton("📊 Statistics", callback_data="statistics"),
        ],
        [
            InlineKeyboardButton("💰 Add Income", callback_data="add_income"),
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)