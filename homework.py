import logging
import time
from http import HTTPStatus

import requests
from telegram import Bot, TelegramError

from config import PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, \
    RETRY_PERIOD, ENDPOINT, HEADERS, SLEEP_TIME
from exceptions import CriticalError, StatusNotFound
from status import HOMEWORK_VERDICTS

logging.basicConfig(
    level=logging.DEBUG,
    filename='my_bot.log',
    format='%(asctime)s, [%(levelname)s], %(message)s, %(name)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=None)
logger.addHandler(handler)


# :TODO чисто теоритически можно переменные (PRACTICUM_TOKEN,
# TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
# вынести в список и в цикле пробежатся и получить данные, есть venv или нет,
# также сделать отдельную функцию для формирования данного сообщения и просто
# передавать туда имя переменной ( что бы исключить дублирование )
# либо реализовать типо гетера для получения токенов из venv, вопрос а надо
# так усложнять ? про функцию исключения
# дублирования сообщений я бы наверное сделал
def check_tokens():
    error_count = 0
    logger.debug('Загружаем переменные из venv')
    # вообщем можно в raise передать всю информацию и дополнительно не писать
    # через logger, но как учил ревьюер у нас есть ТЗ )))
    if not PRACTICUM_TOKEN:
        logger.critical(
            'Отсутствует обязательная переменная окружения: PRACTICUM_TOKEN'
        )
        error_count += 1
        raise CriticalError('Программа остановлена из за критической ошибки')
    if not TELEGRAM_TOKEN:
        logger.critical(
            'Отсутствует обязательная переменная окружения: TELEGRAM_TOKEN'
        )
        error_count += 1
        raise CriticalError('Программа остановлена из за критической ошибки')
    if not TELEGRAM_CHAT_ID:
        logger.critical(
            'Отсутствует обязательная переменная окружения: TELEGRAM_CHAT_ID'
        )
        error_count += 1
        raise CriticalError('Программа остановлена из за критической ошибки')
    if error_count == 0:
        logger.debug('Все токены успешно получены')


def send_message(bot, message):
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message
    )
    logger.debug(
        f'Бот отправил сообщение: {message} \nпользователю с id: {TELEGRAM_CHAT_ID}')


# точно помню, что в datetime библиотеке, можно вычитать даты и получать
# в формате timedelta, вычислим тут просто от текущей даты - 600 сек
def get_api_answer(timestamp):
    params = {'from_date': timestamp - RETRY_PERIOD}
    # в лог header не записал так как там токен
    logger.debug(f'Формируем запрос к {ENDPOINT} \nParams: {params}')
    homework_statuses = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params=params,
    )
    if homework_statuses.status_code == HTTPStatus.OK:
        logger.debug(f'Ответ: {homework_statuses.json()}')
        return homework_statuses.json()
    logger.critical(
        f'Был полочен неожиданный ответ \n Статус ответа: {homework_statuses.status_code}, \n {homework_statuses.json()} \n ENDPOINT:{ENDPOINT}, headers:{HEADERS}, params:{params}')
    # или просто пишем в лог и возращаем неизвестный ответ? хотя вся логика
    # ломается, я бы кидал исключение
    raise CriticalError('Программа остановлена из за критической ошибки')


# честно говоря не очень понимаю зачем эта функия тут нужна? если только
# проверить, что есть ождидающие ключи в словаре так как в нее пришел обьект с кодом 200
def check_response(response):
    return response.get('homeworks')


def parse_status(homework):
    logger.debug(f'Парсим данные {homework}')
    last_homework = homework[0]
    current_status_homework = last_homework.get('status')
    logger.debug(f'Текущий статус работы {current_status_homework}')
    if current_status_homework is None:
        message = 'У домшней работы нет поля статус'
        logger.warning(message)
        return message
    elif current_status_homework in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS.get(last_homework.get('status'))
        homework_name = last_homework.get('homework_name')
        logger.debug(f'Текущиие имя работы {homework_name}')
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    # наверное кидать исключение это слишком, хотя зависит все от ТЗ,
    # можно и просто в лог занести
    raise StatusNotFound(
        f'Неизвестный статус: {current_status_homework}, приостанавливаем работу программы')


# :TODO  вместо sleep можно использовать https://pypi.org/project/aioschedule/
# или https://schedule.readthedocs.io/en/stable/
def main():
    check_tokens()
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_exception = None
    while True:
        try:
            request_query = get_api_answer(timestamp=timestamp)
            response = check_response(request_query)
            if response is not None and response != []:
                get_message = parse_status(response)
                send_message(bot=bot, message=get_message)
            previous_exception = None
        # мне кажется, достаточно отловить все exceptions, так как у меня
        # действия одни и теже, но я читал что это плохой тон как правильно?
        except CriticalError as error:
            if str(previous_exception) != str(error):
                send_message(bot=bot, message=str(error))
            previous_exception = error
            logger.exception(error)
        except StatusNotFound as error:
            if str(previous_exception) != str(error):
                send_message(bot=bot, message=str(error))
            previous_exception = error
            logger.exception(error)
        except TelegramError as error:
            if str(previous_exception) != str(error):
                send_message(bot=bot, message=str(error))
            previous_exception = error
            logger.exception(error)
        except Exception as error:
            if str(previous_exception) != str(error):
                send_message(bot=bot, message=str(error))
            previous_exception = error
            logger.exception(error)
        time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    main()
