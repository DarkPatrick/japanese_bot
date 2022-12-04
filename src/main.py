import asyncio
from typing import NoReturn

from telegram import __version__ as TG_VER
from telegram import __version_info__

print(TG_VER)
print(__version_info__)

from telegram import (
    KeyboardButton, KeyboardButtonPollType, Poll, ReplyKeyboardMarkup,
    ReplyKeyboardRemove, Update
)

from telegram.ext import (
    CommandHandler, ContextTypes, MessageHandler, ConversationHandler,
    PollAnswerHandler, PollHandler, filters, ApplicationBuilder, Application,
    Updater
)

from telegram.constants import ParseMode

import prettytable as pt

from random import random, randint, shuffle


import config as cfg
import dictionary as dictionary


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inform user about what this bot can do"""
    cfg.current_chat_id = update.message.chat_id
    cfg.logger.info(f"id чата: {cfg.current_chat_id}")
    # await set_timer(cfg.current_chat_id, context)
    # here
    await set_timer(update, context)
    await update.message.reply_text(
        "Используй /add для добавления слова или фразы "
        "/del для удаления слова из словаря "
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

    return 1


async def add_jap_word_translation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    cfg.new_word["translation"] = update.message.text
    dictionary.add_row(cfg.new_word)
    cfg.logger.info(f"первод: {update.message.text}")
    await update.message.reply_text("слово успешно добавлено")

    return ConversationHandler.END


async def del_jap_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = "Введи слово, которое хочешь удалить или его перевод"
    await update.effective_message.reply_text(
        message
    )
    return 0

async def del_word_from_dict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    word_to_del = update.message.text
    res = dictionary.del_row(word_to_del)
    await update.message.reply_text("слово успешно удалено" if res == 1 else "такого слова в словаре не найдено")

    return ConversationHandler.END


async def print_dictionary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    table = pt.PrettyTable(['Слово', 'Перевод', 'Тестов', 'Верных ответов'])
    table.align['Слово'] = 'l'
    table.align['Перевод'] = 'r'
    table.align['Тестов'] = 'r'
    table.align['Верных ответов'] = 'r'
    df = dictionary.get_datatable()
    for index, row in df.iterrows():
        table.add_row([row['word'], row['translation'], row['tries'], row['success_cnt']])

    await update.message.reply_text(f'```{table}```', parse_mode=ParseMode.MARKDOWN_V2)


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    # update = context.update
    job = context.job
    # await context.bot.send_message(job.chat_id, text=f"Beep! {job.data} seconds are over!")
    questions_df = dictionary.get_random_word()
    # questions = ["1", "2", "4", "20"]
    # idx = randint(0, len(questions_df.index))
    if random() < 0.5:
        word = questions_df.word[0]
        questions_df = questions_df.sample(frac=1).reset_index(drop=True)
        options = list(questions_df.translation)
        answer_id = questions_df[questions_df.word==word].index[0]
    else:
        word = questions_df.translation[0]
        questions_df = questions_df.sample(frac=1).reset_index(drop=True)
        options = list(questions_df.word)
        answer_id = questions_df[questions_df.translation==word].index[0]
    message = await context.bot.send_poll(
        chat_id=job.chat_id,
        question=f"Выбери верный перевод слова {word}",
        options=options,
        # allows_multiple_answers=True,
        type=Poll.QUIZ, correct_option_id=int(answer_id)
    )
    # Save some info about the poll the bot_data for later use in receive_quiz_answer
    payload = {
        # message.poll.id: {"chat_id": update.effective_chat.id, "message_id": message.message_id}
        message.poll.id: {"chat_id": cfg.current_chat_id, "message_id": message.message_id}
    }
    context.bot_data.update(payload)


# async def set_timer(chat_id: str, context: ContextTypes.DEFAULT_TYPE) -> None:
async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        due = 60

        context.job_queue.run_repeating(alarm, interval=due, first=1, chat_id=chat_id, name=str(chat_id), data=due)
        # context.job.run(alarm, due, chat_id=chat_id, name=str(chat_id), data=due)

    except (IndexError, ValueError):
        # pass
        await update.effective_message.reply_text("ошибка таймера квиза")

async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Summarize a users poll vote"""
    answer = update.poll_answer
    answered_poll = context.bot_data[answer.poll_id]
    cfg.logger.info(f"poll info: {context.bot_data}")
    try:
        questions = answered_poll["questions"]
    # this means this poll answer update is from an old poll, we can't do our answering then
    except KeyError:
        return
    selected_options = answer.option_ids
    answer_string = ""
    for question_id in selected_options:
        if question_id != selected_options[-1]:
            answer_string += questions[question_id] + " and "
        else:
            answer_string += questions[question_id]
    await context.bot.send_message(
        answered_poll["chat_id"],
        f"{update.effective_user.mention_html()} feels {answer_string}!",
        parse_mode=ParseMode.HTML,
    )
    answered_poll["answers"] += 1
    # Close poll after three participants voted
    if answered_poll["answers"] == 3:
        await context.bot.stop_poll(answered_poll["chat_id"], answered_poll["message_id"])


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a predefined poll"""
    questions = ["1", "2", "4", "20"]
    message = await update.effective_message.reply_poll(
        "How many eggs do you need for a cake?", questions, type=Poll.QUIZ, correct_option_id=2
    )
    # Save some info about the poll the bot_data for later use in receive_quiz_answer
    payload = {
        message.poll.id: {"chat_id": update.effective_chat.id, "message_id": message.message_id}
    }
    context.bot_data.update(payload)


async def receive_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Close quiz after three participants took it"""
    if not update.poll.is_closed:
        if update.poll.options[update.poll.correct_option_id].voter_count == 1:
            dictionary.update_stats(update.poll.options[update.poll.correct_option_id].text, 1)
        else:
            dictionary.update_stats(update.poll.options[update.poll.correct_option_id].text, 0)
        if update.poll.id in context.bot_data.keys():
            quiz_data = context.bot_data[update.poll.id]
            await context.bot.stop_poll(quiz_data["chat_id"], quiz_data["message_id"])


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
    # updater = Updater(cfg.bot_info["token"], pass_job_queue=True)
    # dispatcher = updater.dispatcher
    # dispatcher.add_handler(set_timer)
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(cfg.bot_info["token"]).build()
    # application.bot.getUpdates()
    # asyncio.run(set_timer(application.bot., application.context_types))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("dict", print_dictionary))
    # application.add_handler(CommandHandler("set", set_timer))
    # application.add_handler(CommandHandler("add", add))
    word_add_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add)],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_jap_word)],
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_jap_word_translation)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    word_del_handler = ConversationHandler(
        entry_points=[CommandHandler("del", del_jap_word)],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, del_word_from_dict)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    # application.add_handler(CommandHandler("quiz", quiz))
    # application.add_handler(CommandHandler("preview", preview))
    # application.add_handler(CommandHandler("help", help_handler))
    # application.add_handler(MessageHandler(filters.POLL, receive_poll))
    application.add_handler(PollHandler(receive_quiz_answer))
    # application.add_handler(PollAnswerHandler(receive_poll_answer))

    application.add_handler(word_add_handler)
    application.add_handler(word_del_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()