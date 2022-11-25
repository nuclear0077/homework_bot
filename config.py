import logging
import os

from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


def set_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        filename='my_bot.log',
        format=(
            '%(asctime)s [%(levelname)s] | '
            '(%(filename)s).%(funcName)s:%(lineno)d | %(message)s'
        ),
    )
