import os
import logging


current_chat_id = ""

postgre = {
    "host": "localhost",
    "port": "5432",
    "default_database": "postgres",
    "database": "japanese_bot",
    "user": "a1",
    "password": "postgres",
    "datatable": "dictionary"
}

# create bot_token file inside .venv with your secret token from @BotFather
with open(".venv/bot_token") as f:
    os.environ['BOT_TOKEN'] = f.readline()

bot_info = {
    "token": os.environ['BOT_TOKEN']
}


new_word = {
    "word": "",
    "translation": ""
}


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
