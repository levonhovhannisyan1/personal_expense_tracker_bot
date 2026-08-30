from datetime import date
from decimal import Decimal, InvalidOperation

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from bot.handlers.menu import show_main_menu
from bot.services.savings_service import add_balance_adjustment, set_opening_savings
from bot.services.telegram import answer_callback, delete_message, send_message
from bot.utils.authorization import require_owner


AMOUNT = 0


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("❌ Cancel", callback_data="savings_cancel")]]
    )


async def start_savings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await answer_callback(update)
    context.user_data["savings_prompt_chat_id"] = update.effective_chat.id
    context.user_data["savings_prompt_message_id"] = update.callback_query.message.message_id
    await update.callback_query.edit_message_text(
        "🏦 Enter your current savings balance\n\n"
        "This is your starting balance, not monthly income.",
        reply_markup=cancel_keyboard(),
    )
    return AMOUNT


async def set_savings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = Decimal(update.message.text.strip())
        if (
            not amount.is_finite()
            or amount < 0
            or amount > Decimal("9999999999.99")
            or amount.as_tuple().exponent < -2
        ):
            raise ValueError
    except (InvalidOperation, ValueError):
        await delete_message(update)
        await send_message(update, "❌ Enter a non-negative amount with up to 2 decimals")
        return AMOUNT

    await delete_message(update)
    saved = set_opening_savings(update.effective_user.id, amount, date.today().replace(day=1))
    if not saved:
        await send_message(update, "❌ Starting savings could not be saved")
        return ConversationHandler.END

    await finish_savings_prompt(context, f"✅ Starting savings set to {amount:.2f} AMD")
    await show_main_menu(update)
    clear_savings_data(context)
    return ConversationHandler.END


async def start_adjustment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await answer_callback(update)
    context.user_data["savings_prompt_chat_id"] = update.effective_chat.id
    context.user_data["savings_prompt_message_id"] = update.callback_query.message.message_id
    await update.callback_query.edit_message_text(
        "➕ Enter the balance adjustment\n\n"
        "Use a positive amount to add money or a negative amount to subtract money.",
        reply_markup=cancel_keyboard(),
    )
    return AMOUNT


async def set_adjustment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = Decimal(update.message.text.strip())
        if (
            not amount.is_finite()
            or amount == 0
            or abs(amount) > Decimal("9999999999.99")
            or amount.as_tuple().exponent < -2
        ):
            raise ValueError
    except (InvalidOperation, ValueError):
        await delete_message(update)
        await send_message(update, "❌ Enter a non-zero amount with up to 2 decimals")
        return AMOUNT

    await delete_message(update)
    saved = add_balance_adjustment(
        update.effective_user.id,
        amount,
        date.today().replace(day=1),
    )
    if not saved:
        await send_message(update, "❌ Balance adjustment could not be saved")
        return ConversationHandler.END

    sign = "+" if amount > 0 else ""
    await finish_savings_prompt(context, f"✅ Balance adjusted by {sign}{amount:.2f} AMD")
    await show_main_menu(update)
    clear_savings_data(context)
    return ConversationHandler.END


async def cancel_savings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await answer_callback(update)
    await update.callback_query.edit_message_text("❌ Balance entry cancelled")
    await show_main_menu(update)
    clear_savings_data(context)
    return ConversationHandler.END


async def finish_savings_prompt(context: ContextTypes.DEFAULT_TYPE, text: str):
    try:
        await context.bot.edit_message_text(
            chat_id=context.user_data["savings_prompt_chat_id"],
            message_id=context.user_data["savings_prompt_message_id"],
            text=text,
        )
    except BadRequest:
        pass


def clear_savings_data(context: ContextTypes.DEFAULT_TYPE):
    for key in ("savings_prompt_chat_id", "savings_prompt_message_id"):
        context.user_data.pop(key, None)


savings_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            require_owner(start_savings),
            pattern=r"^set_starting_savings$",
        ),
        CallbackQueryHandler(
            require_owner(start_adjustment),
            pattern=r"^adjust_balance$",
        ),
    ],
    states={
        AMOUNT: [
            CallbackQueryHandler(
                require_owner(cancel_savings),
                pattern=r"^savings_cancel$",
            ),
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                require_owner(set_savings),
            ),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            require_owner(cancel_savings),
            pattern=r"^savings_cancel$",
        )
    ],
)
