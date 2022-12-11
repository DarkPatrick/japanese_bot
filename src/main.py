from telegram import __version__ as TG_VER
from telegram import __version_info__
from telegram import (
    Poll, ReplyKeyboardRemove, Update
)
from telegram.ext import (
    CommandHandler, ContextTypes, MessageHandler, ConversationHandler,
    PollHandler, filters, Application,
)
from telegram.constants import ParseMode
import prettytable as pt
from random import random

import config as cfg
import dictionary as dictionary


cfg.logger.info(TG_VER)
cfg.logger.info(__version_info__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inform user about what this bot can do"""
    await set_timer(update, context)
    await update.message.reply_text(
        "Используй /add для добавления слова или фразы "
        "/del для удаления слова из словаря "
        "/dict для отображения текущего словаря "
        "/edit для редактирования записи"
    )


async def add_new_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = "Введи слово / фразу"
    await update.effective_message.reply_text(
        message
    )
    return 0


async def add_jap_word(update: Update, 
                       context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the info about the user and ends the conversation."""
    cfg.logger.info(f"японское слово: {update.message.text}")
    cfg.new_word["word"] = update.message.text
    await update.message.reply_text("Теперь введи перевод")
    return 1


async def add_jap_word_translation(update: Update, 
                                   context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    cfg.new_word["translation"] = update.message.text
    res = dictionary.add_row(cfg.new_word, update.message.chat_id)
    cfg.logger.info(f"первод: {update.message.text}")
    await update.message.reply_text("слово успешно добавлено" if res == 1 
                                    else "слово уже существует")
    return ConversationHandler.END


async def del_jap_word(update: Update, 
                       context: ContextTypes.DEFAULT_TYPE) -> int:
    message = "Введи слово, которое хочешь удалить или его перевод"
    await update.effective_message.reply_text(
        message
    )
    return 0


async def del_word_from_dict(update: Update, 
                             context: ContextTypes.DEFAULT_TYPE) -> int:
    word_to_del = update.message.text
    res = dictionary.del_row(word_to_del, update.message.chat_id)
    await update.message.reply_text("слово успешно удалено" if res == 1 
                                    else "такого слова в словаре не найдено")
    return ConversationHandler.END


async def print_dictionary(update: Update, 
                           context: ContextTypes.DEFAULT_TYPE) -> None:
    table = pt.PrettyTable(['Слово', 'Перевод', 'Тестов', 'Верных ответов'])
    table.align['Слово'] = 'l'
    table.align['Перевод'] = 'r'
    table.align['Тестов'] = 'r'
    table.align['Верных ответов'] = 'r'
    df = dictionary.get_datatable(update.message.chat_id)
    for index, row in df.iterrows():
        table.add_row([row['word'], row['translation'], 
                       row['tries'], row['success_cnt']])
    await update.message.reply_text(f'```{table}```', 
                                    parse_mode=ParseMode.MARKDOWN_V2)


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    job = context.job
    questions_df = dictionary.get_random_word(chat_id=job.chat_id)
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
        type=Poll.QUIZ, correct_option_id=int(answer_id)
    )
    payload = {
        message.poll.id: {"chat_id": job.chat_id, 
                          "message_id": message.message_id}
    }
    context.bot_data.update(payload)


async def set_timer(update: Update, 
                    context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id
    try:
        due = 60
        context.job_queue.run_repeating(alarm, interval=due, first=1, 
                                        chat_id=chat_id, name=str(chat_id), 
                                        data=due)
    except (IndexError, ValueError):
        await update.effective_message.reply_text("ошибка таймера квиза")


async def receive_quiz_answer(update: Update, 
                              context: ContextTypes.DEFAULT_TYPE) -> None:
    """Close quiz after three participants took it"""
    if not update.poll.is_closed and update.poll.id in context.bot_data:
        if update.poll.options[update.poll.correct_option_id].voter_count == 1:
            dictionary.update_stats(
                update.poll.options[update.poll.correct_option_id].text, 1, 
                context.bot_data[update.poll.id]["chat_id"])
        else:
            dictionary.update_stats(
                update.poll.options[update.poll.correct_option_id].text, 0, 
                context.bot_data[update.poll.id]["chat_id"])

        if update.poll.id in context.bot_data.keys():
            quiz_data = context.bot_data[update.poll.id]
            await context.bot.stop_poll(quiz_data["chat_id"], 
                                        quiz_data["message_id"])


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    cfg.logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", 
        reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main() -> None:
    """Run bot."""
    application = Application.builder().token(cfg.bot_info["token"]).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("dict", print_dictionary))
    word_add_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add_new_word)],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_jap_word)],
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, 
                               add_jap_word_translation)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    word_del_handler = ConversationHandler(
        entry_points=[CommandHandler("del", del_jap_word)],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, 
                               del_word_from_dict)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(PollHandler(receive_quiz_answer))

    application.add_handler(word_add_handler)
    application.add_handler(word_del_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
