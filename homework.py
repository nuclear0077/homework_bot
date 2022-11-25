import sys
import logging
import time
from http import HTTPStatus

import requests
import telegram

from config import (
    ENDPOINT,
    HEADERS,
    PRACTICUM_TOKEN,
    RETRY_PERIOD,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
    set_logging
)
from exceptions import UnexpectedAnswer, NotHomeWork
# а если так?
set_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=None)
logger.addHandler(handler)

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


# хочу уточнить вопрос, я правильно понимаю исключения которые могут
# возникнуть когда мы обрадаемся к файлу, сервису либо к другому
# источнику взаимодействия мы данные запросы обрабатываем
# прямо в функции? в конце ловить все исключения плохой тон?
# еще вопрос я создавал свои исключения, но тесты перестали проходить,
# как определяется когда нужно использовать базовые или свои ?
# например у меня было 2 исключения
# 1 - CriticalError критическая ошибка ( когда например нет токена в ENV )
# 2 - StatusNotFound у нас не существует статуса в словаре
# пришлось убрать из за тестов.
# Вопрос по поводу логирования, я кидаю исключения и записываю их в лог в самом
# конце блока когда идет обработка всех exceptions, это правильно? или лучше
# перед тем как кинуть залогировать сообщение с нужным статусом ?
# просто получается некое дублирование


def check_tokens():
    """Проверка загрузки переменных из venv."""
    logger.debug('Загружаем переменные из venv')
    if not PRACTICUM_TOKEN:
        logger.critical('Нет токена PRACTICUM_TOKEN')
    if not TELEGRAM_TOKEN:
        logger.critical('Нет токена TELEGRAM_TOKEN')
    if not TELEGRAM_CHAT_ID:
        logger.critical('Нет токена TELEGRAM_CHAT_ID')
    if all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)):
        logger.debug('Все токены успешно получены')
        return None
    logger.critical('Приостанавливаем программу')
    sys.exit()


def send_message(bot, message):
    """Функция для отправки сообщения в телеграмм.

    Args:
        bot (TelegramObject)
        message (str): сообщение для отправки в телеграмм
    """
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.TelegramError as error:
        logger.exception(error)
    else:
        logger.debug(f'Бот отправил сообщение: {message}'
                     f'/nпользователю с id: {TELEGRAM_CHAT_ID}')


# точно помню, что в datetime библиотеке, можно вычитать даты и получать
# в формате timedelta, вычислим тут просто от текущей даты - 600 сек
def get_api_answer(timestamp):
    """Функция для отправки запроса к API YandexPracticum.

    Args:
        timestamp (int): текущие время в формате int
    Returns:
        response (dict): ответ от сервера
    Raises:
        CriticalError: ошибка когда был получен любой ответ со стутусом != 200
    """
    params = {'from_date': timestamp}
    logger.debug(f'Формируем запрос к {ENDPOINT} Params: {params}')
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params,
        )
    except requests.RequestException as error:
        logger.exception(error)
    if not homework_statuses.status_code == HTTPStatus.OK:
        message = 'Был полочен неожиданный ответ'
        f'Статус ответа: {homework_statuses.status_code},'
        f'{homework_statuses.json()}\n ENDPOINT:{ENDPOINT}, params:{params}'
        raise requests.RequestException(message)
    logger.debug('Получен ответ')
    return homework_statuses.json()


def check_response(response):
    """Функция для проверки существования ключа в ответе.

    Args:
        response (dict): словарь ответа
    Returns:
        response (dict) or None: если ключ существует
        возвращается словарь иначе None
    Raises:
        KeyError: В ответе API нет ключа домашней работы
        TypeError: когда на вход подали не словарь
    """
    if not isinstance(response, dict):
        raise TypeError('Неверный формат данных, ожидаем словарь')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Неверный формат homeworks, ожидаем список')
    if not len(homeworks) != 0:
        raise NotHomeWork('Нет домашней работы')
    if homeworks is None:
        raise KeyError('В ответе API нет ключа домашней работы')
    return homeworks[0]


def parse_status(homework):
    """Функция для проверки существования ключа в ответе.

    Args:
        homework (dict): словарь домашней работы
    Returns:
        message (str): сообщение для отправки боту
    Raises:
        StatusNotFound: если в словаре HOMEWORK_VERDICTS нет статуса
    """
    logger.debug(f'Парсим данные {homework}')
    current_status_homework = homework.get('status')
    logger.debug(f'Текущий статус работы {current_status_homework}')
    if (current_status_homework is None) or (
        current_status_homework not in HOMEWORK_VERDICTS
    ):
        raise KeyError(f'Ошибка с ключом {current_status_homework}')
    verdict = HOMEWORK_VERDICTS.get(homework.get('status'))
    homework_name = homework.get('homework_name')
    if not homework_name:
        raise KeyError('В домашней работе нет ключа homework_name')
    logger.debug(f'Текущиие имя работы {homework_name}')
    message = f"""Изменился статус проверки работы "{homework_name}".
        {verdict}"""
    return message


# :TODO  вместо sleep можно использовать https://pypi.org/project/aioschedule/
# или https://schedule.readthedocs.io/en/stable/
def main():
    """Основная функция для запуска бота.

    Логика следующая:
    1 - Проверяем загрузку токенов из venv
    2 - Инициализируем бота
    3 - инициализируем переменную для сохранения исключений
    4 - инициализируем текущие время
    5 - заходим в бесконечный цикл
    6 - получаем ответ API яндекса
    7 - проверяем ответ
    8 - получачем статус ответа
    9 - оптравялем сообщение в телеграмм
    10 - ставим паузу на 10 минут
    11 - обрабаываем исключения, при повторном одинаковой ошибки мы сообщение
    не отправляем
    """
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    previous_exception = None
    # изначально timestamp был в цилке, далее каждый круг цикла обновлял
    # информацию о времени и вычитаем 10 минут, получаем актуально информацию
    # но с вычитаением ловлю ошибку на pytest и тогда смысла ставить данный
    # блок в цикл нет, так как интервал будет секунда )
    # получается сейчас интервал, текущие время - время работы программы,
    # но такое себе честно говоря, скрипт работает 1 год и мы будем получать
    # историю за весь год, но зачем нам это ? я думаю надо сделать отдельную
    # функцию получения времени, текущие время - sleeptime
    timestamp = int(time.time())
    while True:
        try:
            request_query = get_api_answer(timestamp=timestamp)
            response = check_response(request_query)
            if response is not None and response != []:
                get_message = parse_status(response)
                send_message(bot=bot, message=get_message)
            previous_exception = None
        except requests.RequestException as error:
            # но в логах не видно всю цепочку (
            logger.exception(error)
            previous_exception = error
            send_message(bot=bot, message=str(error))
            raise UnexpectedAnswer(error) from error
        except Exception as error:
            if str(previous_exception) != str(error):
                send_message(bot=bot, message=str(error))
            previous_exception = error
            logger.exception(error)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
