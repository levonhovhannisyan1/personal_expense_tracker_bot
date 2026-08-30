from datetime import date

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from bot.keyboards.main_menu import main_menu_keyboard
from bot.services.expense_service import (
    get_monthly_expense_totals,
    get_monthly_income_totals,
    next_month,
)
from bot.services.savings_service import get_monthly_closing_balances
from bot.services.telegram import answer_callback, edit_message
from bot.utils.authorization import require_authorization


def statistics_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📋 View all expenses",
                    callback_data="expenses",
                )
            ],
            [InlineKeyboardButton("🏠 Home", callback_data="statistics_back")],
        ]
    )


def format_statistics(telegram_user_id: int) -> str:
    current_month = date.today().replace(day=1)
    expense_totals = get_monthly_expense_totals(telegram_user_id, current_month)
    income_totals = get_monthly_income_totals(telegram_user_id, current_month)
    closing_balances = get_monthly_closing_balances(
        telegram_user_id,
        current_month,
    )
    months = (current_month, next_month(current_month))
    lines = ["📊 Expense Statistics", ""]

    for month in months:
        count, expenses = expense_totals[month]
        income = income_totals[month]
        savings = income - expenses
        expense_label = "expense" if count == 1 else "expenses"
        lines.extend(
            [
                f"{month:%B %Y}",
                f"• {count} {expense_label}",
                f"• Income: {income:.2f} AMD",
                f"• Expenses: {expenses:.2f} AMD",
                f"• Savings: {savings:.2f} AMD",
                f"• Total balance: {closing_balances[month]:.2f} AMD",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


async def show_statistics(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)
    await edit_message(
        update,
        format_statistics(update.effective_user.id),
        reply_markup=statistics_keyboard(),
    )


async def statistics_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)
    await edit_message(
        update,
        "Choose an action",
        reply_markup=main_menu_keyboard(),
    )


statistics_handlers = [
    CallbackQueryHandler(
        require_authorization(show_statistics),
        pattern=r"^statistics$",
    ),
    CallbackQueryHandler(
        require_authorization(statistics_back),
        pattern=r"^statistics_back$",
    ),
]
