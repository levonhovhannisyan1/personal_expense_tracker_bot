from datetime import date
from decimal import Decimal, InvalidOperation

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.services.expense_service import (
    get_expense,
    update_expense,
)
from bot.services.telegram import (
    answer_callback,
    delete_message,
    delete_message_by_id,
    edit_form,
    send_message,
)

from bot.handlers.menu import show_main_menu
from bot.utils.authorization import require_authorization


CATEGORY_NAMES = {
    "food": "🍔 Food",
    "transport": "🚗 Transport",
    "shopping": "🛒 Shopping",
    "bills": "💡 Bills",
    "entertainment": "🎮 Entertainment",
    "health": "🩺 Health",
    "sport": "⚽ Sport",
    "other": "📦 Other",
}


CATEGORY, AMOUNT, DESCRIPTION, MONTH, CONFIRM = range(5)


def edit_expense_text(expense: dict) -> str:
    category = expense.get("category")
    amount = expense.get("amount")
    description = expense.get("description")
    expense_month = expense.get("expense_month")

    category_text = (
        CATEGORY_NAMES.get(category, category)
        if category
        else "—"
    )

    amount_text = (
        f"{amount:.2f} AMD"
        if amount is not None
        else "—"
    )

    description_text = (
        description
        if description
        else "—"
    )

    month_text = (
        expense_month.strftime("%b %Y")
        if expense_month
        else "—"
    )

    return (
        "Edit Expense\n\n"
        f"Category: {category_text}\n"
        f"Amount: {amount_text}\n"
        f"Description: {description_text}\n"
        f"Month: {month_text}"
    )


def edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📂 Category",
                    callback_data="edit_field_category",
                ),
                InlineKeyboardButton(
                    "💰 Amount",
                    callback_data="edit_field_amount",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📝 Description",
                    callback_data="edit_field_description",
                ),
                InlineKeyboardButton(
                    "📅 Month",
                    callback_data="edit_field_month",
                ),
            ],
            [
                InlineKeyboardButton(
                    "✅ Save",
                    callback_data="edit_expense_save",
                ),
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="edit_expense_cancel",
                ),
            ],
        ]
    )


def category_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🍔 Food",
                    callback_data="edit_category_food",
                ),
                InlineKeyboardButton(
                    "🚗 Transport",
                    callback_data="edit_category_transport",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🛒 Shopping",
                    callback_data="edit_category_shopping",
                ),
                InlineKeyboardButton(
                    "💡 Bills",
                    callback_data="edit_category_bills",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🩺 Health",
                    callback_data="edit_category_health",
                ),
                InlineKeyboardButton(
                    "🎮 Entertainment",
                    callback_data="edit_category_entertainment",
                ),
                InlineKeyboardButton(
                    "⚽ Sport",
                    callback_data="edit_category_sport",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📦 Other",
                    callback_data="edit_category_other",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="edit_back",
                ),
            ],
        ]
    )


def month_keyboard(
    selected_month: date,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️",
                    callback_data="edit_month_previous",
                ),
                InlineKeyboardButton(
                    selected_month.strftime("%b %Y"),
                    callback_data="edit_month_current",
                ),
                InlineKeyboardButton(
                    "➡️",
                    callback_data="edit_month_next",
                ),
            ],
            [
                InlineKeyboardButton(
                    "✅ Select",
                    callback_data="edit_month_select",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="edit_back",
                ),
            ],
        ]
    )


async def start_edit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    # Save the original expense window
    context.user_data["expense_detail_message_id"] = (
        update.callback_query.message.message_id
    )

    context.user_data["expense_detail_chat_id"] = (
        update.effective_chat.id
    )

    expense_id = int(
        update.callback_query.data.removeprefix(
            "edit_expense_"
        )
    )

    telegram_user_id = update.effective_user.id

    expense = get_expense(
        telegram_user_id,
        expense_id,
    )

    if expense is None:
        await edit_form(
            update,
            context,
            "❌ Expense not found",
        )

        return ConversationHandler.END

    context.user_data["editing_expense_id"] = (
        expense.id
    )

    context.user_data["editing_expense"] = {
        "category": expense.category,
        "amount": expense.amount,
        "description": expense.description,
        "expense_month": expense.expense_month,
    }

    await edit_form(
        update,
        context,
        edit_expense_text(
            context.user_data["editing_expense"]
        ),
        reply_markup=edit_keyboard(),
    )

    return CONFIRM


async def select_category(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    await edit_form(
        update,
        context,
        "Select category",
        reply_markup=category_keyboard(),
    )

    return CATEGORY


async def set_category(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    category = update.callback_query.data.removeprefix(
        "edit_category_"
    )

    context.user_data["editing_expense"][
        "category"
    ] = category

    await edit_form(
        update,
        context,
        edit_expense_text(
            context.user_data["editing_expense"]
        ),
        reply_markup=edit_keyboard(),
    )

    return CONFIRM


async def request_amount(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    message = await send_message(
        update,
        "Enter the amount",
    )

    context.user_data[
        "edit_input_message_id"
    ] = message.message_id

    return AMOUNT


async def set_amount(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    try:
        amount = Decimal(text)

        if (
            not amount.is_finite()
            or amount <= 0
            or amount > Decimal("99999999.99")
            or amount.as_tuple().exponent < -2
        ):
            raise ValueError

    except (InvalidOperation, ValueError):
        await delete_message(update)

        old_error_id = context.user_data.get(
            "edit_amount_error_message_id"
        )

        if old_error_id:
            await delete_message_by_id(
                context,
                update.effective_chat.id,
                old_error_id,
            )

        error_message = await send_message(
            update,
            "❌ Invalid amount\n\n"
            "Please enter a positive number",
        )

        context.user_data[
            "edit_amount_error_message_id"
        ] = error_message.message_id

        return AMOUNT

    await delete_message(update)

    input_message_id = context.user_data.get(
        "edit_input_message_id"
    )

    if input_message_id:
        await delete_message_by_id(
            context,
            update.effective_chat.id,
            input_message_id,
        )

        context.user_data.pop(
            "edit_input_message_id",
            None,
        )

    error_message_id = context.user_data.get(
        "edit_amount_error_message_id"
    )

    if error_message_id:
        await delete_message_by_id(
            context,
            update.effective_chat.id,
            error_message_id,
        )

        context.user_data.pop(
            "edit_amount_error_message_id",
            None,
        )

    context.user_data["editing_expense"][
        "amount"
    ] = amount

    await edit_form(
        update,
        context,
        edit_expense_text(
            context.user_data["editing_expense"]
        ),
        reply_markup=edit_keyboard(),
    )

    return CONFIRM


async def request_description(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    message = await send_message(
        update,
        "Enter the description",
    )

    context.user_data[
        "edit_input_message_id"
    ] = message.message_id

    return DESCRIPTION


async def set_description(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    description = update.message.text.strip()

    if not description or len(description) > 255:
        await delete_message(update)
        await send_message(
            update,
            "❌ Description must contain 1–255 characters",
        )
        return DESCRIPTION

    await delete_message(update)

    input_message_id = context.user_data.get(
        "edit_input_message_id"
    )

    if input_message_id:
        await delete_message_by_id(
            context,
            update.effective_chat.id,
            input_message_id,
        )

        context.user_data.pop(
            "edit_input_message_id",
            None,
        )

    context.user_data["editing_expense"][
        "description"
    ] = description

    await edit_form(
        update,
        context,
        edit_expense_text(
            context.user_data["editing_expense"]
        ),
        reply_markup=edit_keyboard(),
    )

    return CONFIRM


async def request_month(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    current_month = context.user_data[
        "editing_expense"
    ].get("expense_month")

    context.user_data[
        "edit_month_selector"
    ] = current_month

    await edit_form(
        update,
        context,
        "Select month",
        reply_markup=month_keyboard(
            current_month
        ),
    )

    return MONTH


async def previous_month(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    current_month = context.user_data[
        "edit_month_selector"
    ]

    if current_month.month == 1:
        new_month = current_month.replace(
            year=current_month.year - 1,
            month=12,
        )
    else:
        new_month = current_month.replace(
            month=current_month.month - 1
        )

    context.user_data[
        "edit_month_selector"
    ] = new_month

    await edit_form(
        update,
        context,
        "Select month",
        reply_markup=month_keyboard(
            new_month
        ),
    )

    return MONTH


async def next_month(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    current_month = context.user_data[
        "edit_month_selector"
    ]

    if current_month.month == 12:
        new_month = current_month.replace(
            year=current_month.year + 1,
            month=1,
        )
    else:
        new_month = current_month.replace(
            month=current_month.month + 1
        )

    context.user_data[
        "edit_month_selector"
    ] = new_month

    await edit_form(
        update,
        context,
        "Select month",
        reply_markup=month_keyboard(
            new_month
        ),
    )

    return MONTH


async def select_month(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    selected_month = context.user_data[
        "edit_month_selector"
    ]

    context.user_data["editing_expense"][
        "expense_month"
    ] = selected_month

    context.user_data.pop(
        "edit_month_selector",
        None,
    )

    await edit_form(
        update,
        context,
        edit_expense_text(
            context.user_data["editing_expense"]
        ),
        reply_markup=edit_keyboard(),
    )

    return CONFIRM


async def save_edit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    telegram_user_id = update.effective_user.id

    expense_id = context.user_data[
        "editing_expense_id"
    ]

    expense = context.user_data[
        "editing_expense"
    ]

    updated = update_expense(
        telegram_user_id=telegram_user_id,
        expense_id=expense_id,
        category=expense["category"],
        amount=expense["amount"],
        description=expense["description"],
        expense_month=expense["expense_month"],
    )

    if not updated:
        await edit_form(
            update,
            context,
            "❌ Expense could not be updated",
        )

        return ConversationHandler.END

    # Delete the original expense window
    expense_message_id = context.user_data.get(
        "expense_detail_message_id"
    )

    expense_chat_id = context.user_data.get(
        "expense_detail_chat_id"
    )

    if expense_message_id and expense_chat_id:
        try:
            await delete_message_by_id(
                context,
                expense_chat_id,
                expense_message_id,
            )
        except Exception:
            pass

    # Delete the current edit window
    try:
        await update.callback_query.message.delete()
    except Exception:
        pass

    context.user_data.pop(
        "form_message_id",
        None,
    )

    context.user_data.pop(
        "form_chat_id",
        None,
    )

    # Create success message
    summary = (
        "✅ Expense updated successfully\n\n"
        f"{CATEGORY_NAMES[expense['category']]}\n"
        f"💰 {expense['amount']:.2f} AMD\n"
        f"📝 {expense['description']}\n"
        f"📅 {expense['expense_month']:%b %Y}"
    )

    await send_message(
        update,
        summary,
    )

    # Show main menu
    await show_main_menu(
        update
    )

    # Clean up conversation data
    context.user_data.pop(
        "editing_expense_id",
        None,
    )

    context.user_data.pop(
        "editing_expense",
        None,
    )

    context.user_data.pop(
        "expense_detail_message_id",
        None,
    )

    context.user_data.pop(
        "expense_detail_chat_id",
        None,
    )

    context.user_data.pop(
        "edit_month_selector",
        None,
    )

    context.user_data.pop(
        "edit_input_message_id",
        None,
    )

    context.user_data.pop(
        "edit_amount_error_message_id",
        None,
    )

    return ConversationHandler.END


async def back_to_edit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    await edit_form(
        update,
        context,
        edit_expense_text(
            context.user_data["editing_expense"]
        ),
        reply_markup=edit_keyboard(),
    )

    return CONFIRM


async def cancel_edit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    # Delete the original expense window
    expense_message_id = context.user_data.get(
        "expense_detail_message_id"
    )

    expense_chat_id = context.user_data.get(
        "expense_detail_chat_id"
    )

    if expense_message_id and expense_chat_id:
        try:
            await delete_message_by_id(
                context,
                expense_chat_id,
                expense_message_id,
            )
        except Exception:
            pass

    # Delete the current edit window
    try:
        await update.callback_query.message.delete()
    except Exception:
        pass

    # Clear form message information
    context.user_data.pop(
        "form_message_id",
        None,
    )

    context.user_data.pop(
        "form_chat_id",
        None,
    )

    # Show cancellation message
    await send_message(
        update,
        "❌ Edit cancelled",
    )

    # Show a new main menu
    await show_main_menu(
        update
    )

    # Clear edit data
    context.user_data.pop(
        "editing_expense_id",
        None,
    )

    context.user_data.pop(
        "editing_expense",
        None,
    )

    context.user_data.pop(
        "expense_detail_message_id",
        None,
    )

    context.user_data.pop(
        "expense_detail_chat_id",
        None,
    )

    context.user_data.pop(
        "edit_month_selector",
        None,
    )

    context.user_data.pop(
        "edit_input_message_id",
        None,
    )

    context.user_data.pop(
        "edit_amount_error_message_id",
        None,
    )

    return ConversationHandler.END


edit_expense_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            require_authorization(start_edit),
            pattern=r"^edit_expense_\d+$",
        )
    ],
    states={
        CATEGORY: [
            CallbackQueryHandler(
                require_authorization(set_category),
                pattern=r"^edit_category_",
            ),
            CallbackQueryHandler(
                require_authorization(back_to_edit),
                pattern=r"^edit_back$",
            ),
        ],
        AMOUNT: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                require_authorization(set_amount),
            ),
        ],
        DESCRIPTION: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                require_authorization(set_description),
            ),
        ],
        MONTH: [
            CallbackQueryHandler(
                require_authorization(previous_month),
                pattern=r"^edit_month_previous$",
            ),
            CallbackQueryHandler(
                require_authorization(next_month),
                pattern=r"^edit_month_next$",
            ),
            CallbackQueryHandler(
                require_authorization(select_month),
                pattern=r"^edit_month_select$",
            ),
            CallbackQueryHandler(
                require_authorization(back_to_edit),
                pattern=r"^edit_back$",
            ),
        ],
        CONFIRM: [
            CallbackQueryHandler(
                require_authorization(select_category),
                pattern=r"^edit_field_category$",
            ),
            CallbackQueryHandler(
                require_authorization(request_amount),
                pattern=r"^edit_field_amount$",
            ),
            CallbackQueryHandler(
                require_authorization(request_description),
                pattern=r"^edit_field_description$",
            ),
            CallbackQueryHandler(
                require_authorization(request_month),
                pattern=r"^edit_field_month$",
            ),
            CallbackQueryHandler(
                require_authorization(save_edit),
                pattern=r"^edit_expense_save$",
            ),
            CallbackQueryHandler(
                require_authorization(cancel_edit),
                pattern=r"^edit_expense_cancel$",
            ),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            require_authorization(cancel_edit),
            pattern=r"^edit_expense_cancel$",
        ),
    ],
)
