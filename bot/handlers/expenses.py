from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
)

from bot.handlers.menu import show_main_menu
from bot.services.expense_service import (
    delete_expense,
    get_expense,
    get_user_expenses,
)
from bot.services.telegram import (
    answer_callback,
    edit_message,
    send_message,
)
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


def expenses_keyboard(expenses):
    keyboard = []

    for expense in expenses:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{expense.description} — "
                    f"{expense.amount:.2f} AMD",
                    callback_data=f"expense_view_{expense.id}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="expenses_back",
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)


def expense_details_keyboard(expense_id: int):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✏️ Edit",
                    callback_data=f"edit_expense_{expense_id}",
                ),
                InlineKeyboardButton(
                    "🗑 Delete",
                    callback_data=f"expense_delete_{expense_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="expenses_list",
                )
            ],
        ]
    )


def format_expenses(
    expenses,
) -> str:
    if not expenses:
        return "You have no expenses yet"

    lines = [
        "Your expenses",
        "",
    ]

    for expense in expenses:
        category = CATEGORY_NAMES.get(
            expense.category,
            expense.category,
        )

        lines.append(
            f"{category} — "
            f"{expense.amount:.2f} AMD"
        )

        lines.append(
            f"📝 {expense.description}"
        )

        lines.append(
            f"📅 {expense.expense_month:%b %Y}"
        )

        lines.append(
            f"👤 {expense.user.name}"
        )

        lines.append("")

    return "\n".join(lines)


def format_expense(expense) -> str:
    category = CATEGORY_NAMES.get(
        expense.category,
        expense.category,
    )

    return (
        "Expense\n\n"
        f"{category}\n"
        f"💰 {expense.amount:.2f} AMD\n"
        f"📝 {expense.description}\n"
        f"📅 {expense.expense_month:%b %Y}\n"
        f"👤 {expense.user.name}"
    )


async def show_expenses(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    telegram_user_id = update.effective_user.id

    expenses = get_user_expenses(
        telegram_user_id
    )

    await edit_message(
        update,
        format_expenses(expenses),
        reply_markup=expenses_keyboard(expenses),
    )


async def view_expense(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    expense_id = int(
        update.callback_query.data.removeprefix(
            "expense_view_"
        )
    )

    expense = get_expense(
        update.effective_user.id,
        expense_id,
    )

    if expense is None:
        await edit_message(
            update,
            "Expense not found",
        )

        return

    await edit_message(
        update,
        format_expense(
            expense
        ),
        reply_markup=expense_details_keyboard(
            expense.id
        ),
    )


async def delete_expense_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    expense_id = int(
        update.callback_query.data.removeprefix(
            "expense_delete_"
        )
    )

    deleted = delete_expense(
        update.effective_user.id,
        expense_id,
    )

    if not deleted:
        await edit_message(
            update,
            "Expense not found",
        )
        return

    # Delete the current expense window
    try:
        await update.callback_query.message.delete()
    except Exception:
        pass

    # Send notification first
    await send_message(
        update,
        "✅ Expense deleted",
    )

    # Create a new expenses window below it
    expenses = get_user_expenses(
        update.effective_user.id
    )

    message = await send_message(
        update,
        format_expenses(expenses),
        reply_markup=expenses_keyboard(expenses),
    )

    # Store the new expenses window if needed later
    context.user_data["expenses_message_id"] = (
        message.message_id
    )


async def expenses_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    # Delete the current "Your expenses" window
    try:
        await update.callback_query.message.delete()
    except Exception:
        pass

    # Clear old form message data
    context.user_data.pop(
        "form_message_id",
        None,
    )

    context.user_data.pop(
        "form_chat_id",
        None,
    )

    # Show a new main menu
    await show_main_menu(update)


expenses_handlers = [
    CallbackQueryHandler(
        require_authorization(show_expenses),
        pattern="^expenses$",
    ),
    CallbackQueryHandler(
        require_authorization(show_expenses),
        pattern="^expenses_list$",
    ),
    CallbackQueryHandler(
        require_authorization(view_expense),
        pattern="^expense_view_",
    ),
    CallbackQueryHandler(
        require_authorization(delete_expense_handler),
        pattern="^expense_delete_",
    ),
    CallbackQueryHandler(
        require_authorization(expenses_back),
        pattern="^expenses_back$",
    ),
]
