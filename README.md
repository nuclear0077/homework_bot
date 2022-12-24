## Bot-ассистент

## About
Telegram-бот, который будет обращается к API сервиса Практикум.Домашка узнает статус вашей домашней работы и отправляет уведомление.

## Documentation

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/nuclear0077/homework_bot
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Создать файл .env пример файла:

```
PRACTICUM_TOKEN = 'TOKEN'
TELEGRAM_TOKEN = 'TOKEN'
TELEGRAM_CHAT_ID = 'CHAT_ID'
```

Запустить проект:

```
python3 homework.py
```

### Что делает бот
+ раз в 10 минут опрашивает API сервиса Практикум.Домашка и проверяет статус отправленной на ревью домашней работы;
+ при обновлении статуса анализирует ответ API и отправлять соответствующее уведомление в Telegram;
+ логирует свою работу и сообщает о важных проблемах сообщением в Telegram.

#### Описание функций
Функция main(): в ней описана основная логика работы программы. Все остальные функции запускаються из неё. Последовательность действий такая:
1. Делаем запрос к API.
2. Проверяем ответ.
3. Если есть обновления — получаем статус работы из обновления и отправляем сообщение в Telegram.
4. Подождать некоторое время и вернуться в пункт 1.

##### Функция check_tokens()
Проверяет доступность переменных окружения, которые необходимы для работы программы. Если отсутствует хотя бы одна переменная окружения — останавливаем работу бота.

##### Функция get_api_answer()
Делает запрос к единственному эндпоинту API-сервиса. В качестве параметра в функцию передается временная метка. В случае успешного запроса возвращает ответ API, приведя его из формата JSON к типам данных Python.

##### Функция check_response()
Проверяет ответ API на соответствие документации. В качестве параметра функция получает ответ API, приведенный к типам данных Python.

##### Функция parse_status() 
Извлекает из информации о конкретной домашней работе статус этой работы. В качестве параметра функция получает только один элемент из списка домашних работ. В случае успеха, функция возвращает подготовленную для отправки в Telegram строку, содержащую один из вердиктов словаря HOMEWORK_VERDICTS.

##### Функция send_message()
Отправляет сообщение в Telegram чат, определяемый переменной окружения TELEGRAM_CHAT_ID. Принимает на вход два параметра: экземпляр класса Bot и строку с текстом сообщения.

## Developer

- [Aleksandr M](https://github.com/nuclear0077)
- Telegram @nuclear0077

