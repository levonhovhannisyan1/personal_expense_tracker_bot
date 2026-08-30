from telegram.ext import Application, CommandHandler, PicklePersistence

from bot.config import BOT_TOKEN
from bot.handlers.start import start
from bot.handlers.expense import expense_conversation
from bot.handlers.expenses import expenses_handlers
from bot.handlers.edit_expense import edit_expense_conversation
from bot.handlers.statistics import statistics_handlers
from bot.handlers.income import income_conversation
from bot.handlers.savings import savings_conversation
from bot.utils.authorization import require_authorization


def create_application():
    persistence = PicklePersistence(filepath="bot_data.pickle")

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .persistence(persistence)
        .build()
    )

    application.add_handler(
        CommandHandler("start", require_authorization(start))
    )

    application.add_handler(expense_conversation)
    application.add_handler(income_conversation)
    application.add_handler(savings_conversation)

    for handler in expenses_handlers:
        application.add_handler(handler)

    for handler in statistics_handlers:
        application.add_handler(handler)

    application.add_handler(edit_expense_conversation)

    return application