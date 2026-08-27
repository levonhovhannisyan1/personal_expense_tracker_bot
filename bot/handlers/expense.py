from datetime import date

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.database.connection import SessionLocal
from bot.database.models import Expense
from bot.database.users import get_or_create_user
from bot.handlers.menu import show_main_menu
from bot.services.telegram import (
    answer_callback,
    delete_message,
    delete_message_by_id,
    edit_form,
    send_message,
)
from bot.utils.authorization import get_user_name


CATEGORY, AMOUNT, DESCRIPTION, MONTH, CONFIRM = range(5)


CATEGORY_NAMES = {
    "food": "🍔 Food",
    "transport": "🚗 Transport",
    "shopping": "🛒 Shopping",
    "bills": "💡 Bills",
    "entertainment": "🎮 Entertainment",
    "sport": "⚽ Sport",
    "other": "📦 Other",
}


def expense_keyboard(
    category_selected: bool = False,
    amount_selected: bool = False,
    description_selected: bool = False,
    month_selected: bool = False,
) -> InlineKeyboardMarkup:
    keyboard = []

    if not category_selected:
        keyboard.extend(
            [
                [
                    InlineKeyboardButton(
                        "🍔 Food",
                        callback_data="category_food",
                    ),
                    InlineKeyboardButton(
                        "🚗 Transport",
                        callback_data="category_transport",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🛒 Shopping",
                        callback_data="category_shopping",
                    ),
                    InlineKeyboardButton(
                        "💡 Bills",
                        callback_data="category_bills",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🎮 Entertainment",
                        callback_data="category_entertainment",
                    ),
                    InlineKeyboardButton(
                        "⚽ Sport",
                        callback_data="category_sport",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "📦 Other",
                        callback_data="category_other",
                    ),
                ]
            ]
        )

    if category_selected and not amount_selected:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "💰 Enter Amount",
                    callback_data="expense_amount",
                )
            ]
        )

    if category_selected and amount_selected and not description_selected:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "📝 Enter Description",
                    callback_data="expense_description",
                )
            ]
        )

    if (
        category_selected
        and amount_selected
        and description_selected
        and not month_selected
    ):
        keyboard.append(
            [
                InlineKeyboardButton(
                    "📅 Select Month",
                    callback_data="expense_month",
                )
            ]
        )

    if (
        category_selected
        and amount_selected
        and description_selected
        and month_selected
    ):
        keyboard.append(
            [
                InlineKeyboardButton(
                    "✅ Save",
                    callback_data="expense_confirm",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="expense_cancel",
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)


def expense_text(expense: dict) -> str:
    category = expense.get("category")
    amount = expense.get("amount")
    description = expense.get("description")
    expense_month = expense.get("expense_month")

    category_text = (
        CATEGORY_NAMES.get(
            category,
            category,
        )
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
        "Add Expense\n\n"
        f"Category: {category_text}\n"
        f"Amount: {amount_text}\n"
        f"Description: {description_text}\n"
        f"Month: {month_text}"
    )


def month_keyboard(
    selected_month: date,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️",
                    callback_data="month_previous",
                ),
                InlineKeyboardButton(
                    selected_month.strftime("%b %Y"),
                    callback_data="month_current",
                ),
                InlineKeyboardButton(
                    "➡️",
                    callback_data="month_next",
                ),
            ],
            [
                InlineKeyboardButton(
                    "✅ Select",
                    callback_data="month_select",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="expense_cancel",
                )
            ],
        ]
    )


async def add_expense(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    context.user_data["expense"] = {}

    message = await send_message(
        update,
        expense_text(
            context.user_data["expense"]
        ),
        reply_markup=expense_keyboard(),
    )

    context.user_data["form_chat_id"] = message.chat_id
    context.user_data["form_message_id"] = message.message_id

    return CATEGORY


async def category(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    category_name = update.callback_query.data.removeprefix(
        "category_"
    )

    context.user_data["expense"]["category"] = category_name

    await edit_form(
        update,
        context,
        expense_text(
            context.user_data["expense"]
        ),
        reply_markup=expense_keyboard(
            category_selected=True,
        ),
    )

    return AMOUNT


async def request_amount(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    message = await send_message(
        update,
        "Enter the amount",
    )

    context.user_data["input_message_id"] = message.message_id

    return AMOUNT


async def amount(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = update.message.text.strip()

    try:
        amount_value = float(text)

        if amount_value <= 0:
            raise ValueError

    except ValueError:
        await delete_message(update)

        old_error_id = context.user_data.get(
            "amount_error_message_id"
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
            "amount_error_message_id"
        ] = error_message.message_id

        return AMOUNT

    await delete_message(update)

    input_message_id = context.user_data.get(
        "input_message_id"
    )

    if input_message_id:
        await delete_message_by_id(
            context,
            update.effective_chat.id,
            input_message_id,
        )

        context.user_data.pop(
            "input_message_id",
            None,
        )

    error_message_id = context.user_data.get(
        "amount_error_message_id"
    )

    if error_message_id:
        await delete_message_by_id(
            context,
            update.effective_chat.id,
            error_message_id,
        )

        context.user_data.pop(
            "amount_error_message_id",
            None,
        )

    context.user_data["expense"][
        "amount"
    ] = amount_value

    await edit_form(
        update,
        context,
        expense_text(
            context.user_data["expense"]
        ),
        reply_markup=expense_keyboard(
            category_selected=True,
            amount_selected=True,
        ),
    )

    return DESCRIPTION


async def request_description(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    message = await send_message(
        update,
        "Enter the description",
    )

    context.user_data["input_message_id"] = message.message_id

    return DESCRIPTION


async def description(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    description_text = update.message.text.strip()

    if not description_text:
        await delete_message(update)
        return DESCRIPTION

    input_message_id = context.user_data.get(
        "input_message_id"
    )

    await delete_message(update)

    if input_message_id:
        await delete_message_by_id(
            context,
            update.effective_chat.id,
            input_message_id,
        )

        context.user_data.pop(
            "input_message_id",
            None,
        )

    context.user_data["expense"]["description"] = (
        description_text
    )

    await edit_form(
        update,
        context,
        expense_text(
            context.user_data["expense"]
        ),
        reply_markup=expense_keyboard(
            category_selected=True,
            amount_selected=True,
            description_selected=True,
        ),
    )

    return MONTH


async def request_month(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    selected_month = context.user_data.get(
        "month_selector",
        date.today().replace(day=1),
    )

    context.user_data["month_selector"] = selected_month

    await edit_form(
        update,
        context,
        "Choose month",
        reply_markup=month_keyboard(selected_month),
    )

    return MONTH


async def previous_month(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    current_month = context.user_data["month_selector"]

    if current_month.month == 1:
        new_month = current_month.replace(
            year=current_month.year - 1,
            month=12,
        )
    else:
        new_month = current_month.replace(
            month=current_month.month - 1
        )

    context.user_data["month_selector"] = new_month

    await edit_form(
        update,
        context,
        "Choose month",
        reply_markup=month_keyboard(new_month),
    )

    return MONTH


async def next_month(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    current_month = context.user_data["month_selector"]

    if current_month.month == 12:
        new_month = current_month.replace(
            year=current_month.year + 1,
            month=1,
        )
    else:
        new_month = current_month.replace(
            month=current_month.month + 1
        )

    context.user_data["month_selector"] = new_month

    await edit_form(
        update,
        context,
        "Choose month",
        reply_markup=month_keyboard(new_month),
    )

    return MONTH


async def select_month(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    selected_month = context.user_data[
        "month_selector"
    ]

    context.user_data["expense"][
        "expense_month"
    ] = selected_month

    context.user_data.pop(
        "month_selector",
        None,
    )

    await edit_form(
        update,
        context,
        expense_text(
            context.user_data["expense"]
        ),
        reply_markup=expense_keyboard(
            category_selected=True,
            amount_selected=True,
            description_selected=True,
            month_selected=True,
        ),
    )

    return CONFIRM


async def confirm(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    expense_data = context.user_data["expense"]

    user = get_or_create_user(
        update.effective_user.id,
        update.effective_user.first_name
    )

    expense = Expense(
        user_id=user.id,
        category=expense_data["category"],
        amount=expense_data["amount"],
        description=expense_data["description"],
        expense_month=expense_data["expense_month"],
    )

    with SessionLocal() as session:
        session.add(expense)
        session.commit()
        session.refresh(expense)

    user_name = get_user_name(
        update.effective_user.id
    )

    summary = (
        "✅ Expense added successfully\n\n"
        f"{CATEGORY_NAMES[expense.category]}\n"
        f"💰 {expense.amount:.2f} AMD\n"
        f"📝 {expense.description}\n"
        f"📅 {expense.expense_month:%B %Y}\n"
        f"👤 {user_name}"
    )

    await edit_form(
        update,
        context,
        summary,
    )

    await show_main_menu(update)

    context.user_data.pop("expense", None)
    context.user_data.pop("form_chat_id", None)
    context.user_data.pop("form_message_id", None)
    context.user_data.pop("input_message_id", None)

    return ConversationHandler.END


async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await answer_callback(update)

    input_message_id = context.user_data.get(
        "input_message_id"
    )

    if input_message_id:
        await delete_message_by_id(
            context,
            update.effective_chat.id,
            input_message_id,
        )

    await edit_form(
        update,
        context,
        "❌ Expense cancelled",
    )

    await show_main_menu(update)

    context.user_data.pop("expense", None)
    context.user_data.pop("form_chat_id", None)
    context.user_data.pop("form_message_id", None)
    context.user_data.pop("input_message_id", None)

    return ConversationHandler.END


expense_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            add_expense,
            pattern="^add_expense$",
        )
    ],
    states={
        CATEGORY: [
            CallbackQueryHandler(
                category,
                pattern="^category_",
            ),
            CallbackQueryHandler(
                cancel,
                pattern="^expense_cancel$",
            ),
        ],
        AMOUNT: [
            CallbackQueryHandler(
                request_amount,
                pattern="^expense_amount$",
            ),
            CallbackQueryHandler(
                cancel,
                pattern="^expense_cancel$",
            ),
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                amount,
            ),
        ],
        DESCRIPTION: [
            CallbackQueryHandler(
                request_description,
                pattern="^expense_description$",
            ),
            CallbackQueryHandler(
                cancel,
                pattern="^expense_cancel$",
            ),
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                description,
            ),
        ],
        MONTH: [
            CallbackQueryHandler(
                request_month,
                pattern="^expense_month$",
            ),
            CallbackQueryHandler(
                previous_month,
                pattern="^month_previous$",
            ),
            CallbackQueryHandler(
                next_month,
                pattern="^month_next$",
            ),
            CallbackQueryHandler(
                select_month,
                pattern="^month_select$",
            ),
            CallbackQueryHandler(
                cancel,
                pattern="^expense_cancel$",
            ),
        ],
        CONFIRM: [
            CallbackQueryHandler(
                confirm,
                pattern="^expense_confirm$",
            ),
            CallbackQueryHandler(
                cancel,
                pattern="^expense_cancel$",
            ),
        ],
    },
    fallbacks=[
        CommandHandler(
            "cancel",
            cancel,
        ),
    ],
)