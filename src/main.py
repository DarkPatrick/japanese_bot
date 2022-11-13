# import os
import asyncio
from typing import NoReturn
# import logging

from telegram import __version__ as TG_VER
from telegram import __version_info__

from telegram import (
    KeyboardButton, KeyboardButtonPollType, Poll, ReplyKeyboardMarkup,
    ReplyKeyboardRemove, Update
)

from telegram.ext import (
    CommandHandler, ContextTypes, MessageHandler, ConversationHandler,
    PollAnswerHandler, PollHandler, filters, ApplicationBuilder, Application
)

from telegram.constants import ParseMode

import prettytable as pt


import config as cfg
import dictionary


# create bot_token file inside .venv with your secret token from @BotFather
# with open(".venv/bot_token") as f:
#     os.environ['BOT_TOKEN'] = f.readline()

# print(TG_VER)

# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
# )
# logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inform user about what this bot can do"""
    await update.message.reply_text(
        "Используй /add для добавления слова или фразы "
        "/dict для отображения текущего словаря "
        "/edit для редактирования записи"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = "Введи слово / фразу"
    await update.effective_message.reply_text(
        message
    )
    return 0

async def add_jap_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the info about the user and ends the conversation."""
    cfg.logger.info(f"японское слово: {update.message.text}")
    cfg.new_word["word"] = update.message.text
    await update.message.reply_text("Теперь введи перевод")

    # return ConversationHandler.END
    return 1

async def add_jap_word_translation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    cfg.new_word["translation"] = update.message.text
    dictionary.add_row(cfg.new_word)
    cfg.logger.info(f"первод: {update.message.text}")
    await update.message.reply_text("слово успешно добавлено")

    return ConversationHandler.END
    # return 2

async def print_dictionary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    table = pt.PrettyTable(['Слово', 'Перевод'])
    table.align['Слово'] = 'l'
    table.align['Перевод'] = 'r'
    df = dictionary.get_datatable()
    for index, row in df.iterrows():
        # print(row['word'], row['translation'])
        # print(row['word'], row['translation'])
        table.add_row([row['word'], row['translation']])

    await update.message.reply_text(f'```{table}```', parse_mode=ParseMode.MARKDOWN_V2)


# async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Summarize a users poll vote"""
#     answer = update.poll_answer
#     answered_poll = context.bot_data[answer.poll_id]
#     try:
#         questions = answered_poll["questions"]
#     # this means this poll answer update is from an old poll, we can't do our answering then
#     except KeyError:
#         return
#     selected_options = answer.option_ids
#     answer_string = ""
#     for question_id in selected_options:
#         if question_id != selected_options[-1]:
#             answer_string += questions[question_id] + " and "
#         else:
#             answer_string += questions[question_id]
#     await context.bot.send_message(
#         answered_poll["chat_id"],
#         f"{update.effective_user.mention_html()} feels {answer_string}!",
#         parse_mode=ParseMode.HTML,
#     )
#     answered_poll["answers"] += 1
#     # Close poll after three participants voted
#     if answered_poll["answers"] == 3:
#         await context.bot.stop_poll(answered_poll["chat_id"], answered_poll["message_id"])


# async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Send a predefined poll"""
#     questions = ["1", "2", "4", "20"]
#     message = await update.effective_message.reply_poll(
#         "How many eggs do you need for a cake?", questions, type=Poll.QUIZ, correct_option_id=2
#     )
#     # Save some info about the poll the bot_data for later use in receive_quiz_answer
#     payload = {
#         message.poll.id: {"chat_id": update.effective_chat.id, "message_id": message.message_id}
#     }
#     context.bot_data.update(payload)


# async def receive_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Close quiz after three participants took it"""
#     # the bot can receive closed poll updates we don't care about
#     if update.poll.is_closed:
#         return
#     if update.poll.total_voter_count == 3:
#         try:
#             quiz_data = context.bot_data[update.poll.id]
#         # this means this poll answer update is from an old poll, we can't stop it then
#         except KeyError:
#             return
#         await context.bot.stop_poll(quiz_data["chat_id"], quiz_data["message_id"])


# async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Ask user to create a poll and display a preview of it"""
#     # using this without a type lets the user chooses what he wants (quiz or poll)
#     button = [[KeyboardButton("Press me!", request_poll=KeyboardButtonPollType())]]
#     message = "Press the button to let the bot generate a preview for your poll"
#     # using one_time_keyboard to hide the keyboard
#     await update.effective_message.reply_text(
#         message, reply_markup=ReplyKeyboardMarkup(button, one_time_keyboard=True)
#     )


# async def receive_poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """On receiving polls, reply to it by a closed poll copying the received poll"""
#     actual_poll = update.effective_message.poll
#     # Only need to set the question and options, since all other parameters don't matter for
#     # a closed poll
#     await update.effective_message.reply_poll(
#         question=actual_poll.question,
#         options=[o.text for o in actual_poll.options],
#         # with is_closed true, the poll/quiz is immediately closed
#         is_closed=True,
#         reply_markup=ReplyKeyboardRemove(),
#     )


# async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Display a help message"""
#     await update.message.reply_text("Use /quiz, /poll or /preview to test this bot.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    cfg.logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(cfg.bot_info["token"]).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("dict", print_dictionary))
    # application.add_handler(CommandHandler("add", add))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add)],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_jap_word)],
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_jap_word_translation)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    # application.add_handler(CommandHandler("quiz", quiz))
    # application.add_handler(CommandHandler("preview", preview))
    # application.add_handler(CommandHandler("help", help_handler))
    # application.add_handler(MessageHandler(filters.POLL, receive_poll))
    # application.add_handler(PollAnswerHandler(receive_poll_answer))
    # application.add_handler(PollHandler(receive_quiz_answer))

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()