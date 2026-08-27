from telegram import Update
from telegram.error import BadRequest


async def answer_callback(
    update: Update,
):
    if update.callback_query:
        await update.callback_query.answer()


async def send_message(
    update: Update,
    text: str,
    reply_markup=None,
):
    return await update.effective_chat.send_message(
        text=text,
        reply_markup=reply_markup,
    )


async def edit_message(
    update: Update,
    text: str,
    reply_markup=None,
):
    try:
        return await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
        )

    except BadRequest as error:
        if "Message is not modified" in str(error):
            return None

        raise


async def delete_message(
    update: Update,
):
    if update.message:
        try:
            await update.message.delete()
        except BadRequest:
            pass


async def delete_message_by_id(
    context,
    chat_id: int,
    message_id: int,
):
    try:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )
    except BadRequest:
        pass


async def edit_form(
    update: Update,
    context,
    text: str,
    reply_markup=None,
):
    message_id = context.user_data.get(
        "form_message_id"
    )

    chat_id = context.user_data.get(
        "form_chat_id"
    )

    if message_id and chat_id:
        try:
            return await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
            )

        except BadRequest as error:
            error_text = str(error)

            if "Message is not modified" in error_text:
                return None

            if "Message to edit not found" not in error_text:
                raise

            # Stored form message no longer exists
            context.user_data.pop(
                "form_message_id",
                None,
            )

            context.user_data.pop(
                "form_chat_id",
                None,
            )

    # Create a new form message
    message = await send_message(
        update,
        text,
        reply_markup,
    )

    context.user_data["form_chat_id"] = (
        message.chat_id
    )

    context.user_data["form_message_id"] = (
        message.message_id
    )

    return message