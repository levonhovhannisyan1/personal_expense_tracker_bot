from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import os
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, Forbidden
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.config import OWNER_ID
from bot.handlers.menu import show_main_menu
from bot.services.expense_service import get_monthly_financial_summary, save_monthly_income
from bot.services.savings_service import archive_monthly_financial_records
from bot.services.telegram import answer_callback, delete_message, send_message
from bot.utils.authorization import require_owner


AMOUNT = 0
REMINDER_TIMEZONE = ZoneInfo("Asia/Yerevan")


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("❌ Cancel", callback_data="income_cancel")]]
    )


async def start_income(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)
    income_month = month_from_callback(update.callback_query.data)
    context.user_data["income_month"] = income_month
    context.user_data["income_prompt_chat_id"] = update.effective_chat.id
    context.user_data["income_prompt_message_id"] = update.callback_query.message.message_id

    await update.callback_query.edit_message_text(
        f"💰 Enter your income for {income_month:%B %Y}",
        reply_markup=cancel_keyboard(),
    )
    return AMOUNT


def month_from_callback(callback_data: str) -> date:
    if callback_data == "add_income":
        return date.today().replace(day=1)
    return date.fromisoformat(f"{callback_data.removeprefix('income_add_')}-01")


async def set_income(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    try:
        amount = Decimal(update.message.text.strip())
        if (
            not amount.is_finite()
            or amount <= 0
            or amount > Decimal("99999999.99")
            or amount.as_tuple().exponent < -2
        ):
            raise ValueError
    except (InvalidOperation, ValueError):
        await delete_message(update)
        await send_message(update, "❌ Enter a positive amount with up to 2 decimals")
        return AMOUNT

    await delete_message(update)
    income_month = context.user_data["income_month"]
    saved = save_monthly_income(update.effective_user.id, amount, income_month)
    if not saved:
        await send_message(update, "❌ Income could not be saved")
        return ConversationHandler.END

    await finish_income_prompt(
        context,
        f"✅ Added {amount:.2f} AMD to your {income_month:%B %Y} income",
    )
    await show_main_menu(update)
    clear_income_data(context)
    return ConversationHandler.END


async def cancel_income(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)
    await update.callback_query.edit_message_text("❌ Income entry cancelled")
    await show_main_menu(update)
    clear_income_data(context)
    return ConversationHandler.END


async def finish_income_prompt(
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
):
    try:
        await context.bot.edit_message_text(
            chat_id=context.user_data["income_prompt_chat_id"],
            message_id=context.user_data["income_prompt_message_id"],
            text=text,
        )
    except BadRequest:
        pass


def clear_income_data(context: ContextTypes.DEFAULT_TYPE):
    for key in (
        "income_month",
        "income_prompt_chat_id",
        "income_prompt_message_id",
    ):
        context.user_data.pop(key, None)


async def send_monthly_income_reminders(
    context: ContextTypes.DEFAULT_TYPE,
):
    income_month = reminder_date().replace(day=1)
    previous_month = previous_calendar_month(income_month)

    try:
        summary_message = await context.bot.send_message(
            chat_id=OWNER_ID,
            text=format_monthly_summary(previous_month),
        )
    except Forbidden:
        return

    try:
        await context.bot.pin_chat_message(
            chat_id=OWNER_ID,
            message_id=summary_message.message_id,
            disable_notification=True,
        )
    except (BadRequest, Forbidden):
        pass

    archive_monthly_financial_records(previous_month)

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💰 Enter income",
                    callback_data=f"income_add_{income_month:%Y-%m}",
                )
            ]
        ]
    )

    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"💰 What is your income for {income_month:%B %Y}?",
            reply_markup=keyboard,
        )
    except Forbidden:
        pass


def previous_calendar_month(month: date) -> date:
    if month.month == 1:
        return month.replace(year=month.year - 1, month=12)
    return month.replace(month=month.month - 1)


def reminder_date() -> date:
    return datetime.now(REMINDER_TIMEZONE).date()


def format_monthly_summary(month: date) -> str:
    expense_count, income, expenses = get_monthly_financial_summary(OWNER_ID, month)
    savings = income - expenses
    expense_label = "expense" if expense_count == 1 else "expenses"
    archive_status = "Detailed records for this month have been archived."
    return (
        f"📌 {month:%B %Y} overall summary\n\n"
        f"Income: {income:.2f} AMD\n"
        f"Expenses: {expenses:.2f} AMD ({expense_count} {expense_label})\n"
        f"Savings: {savings:.2f} AMD\n\n"
        f"{archive_status}"
    )


income_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            require_owner(start_income),
            pattern=r"^(?:add_income|income_add_\d{4}-\d{2})$",
        )
    ],
    states={
        AMOUNT: [
            CallbackQueryHandler(
                require_owner(cancel_income),
                pattern=r"^income_cancel$",
            ),
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                require_owner(set_income),
            ),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            require_owner(cancel_income),
            pattern=r"^income_cancel$",
        )
    ],
)
