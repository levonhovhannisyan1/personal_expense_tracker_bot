from telegram.ext import Application, CommandHandler

from bot.config import BOT_TOKEN
from bot.handlers.start import start
from bot.handlers.expense import expense_conversation
from bot.handlers.expenses import expenses_handlers
from bot.handlers.edit_expense import edit_expense_conversation


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        expense_conversation
    )

    for handler in expenses_handlers:
        application.add_handler(handler)

    application.add_handler(
        edit_expense_conversation
    )

    application.run_polling()


if __name__ == "__main__":
    main()