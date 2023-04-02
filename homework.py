import logging
import os
import requests
import sys
import time
import telegram

from dotenv import load_dotenv
from http import HTTPStatus

load_dotenv()
PRACTICUM_TOKEN = os.getenv('TOKEN_YP')
TELEGRAM_TOKEN = os.getenv('TOKEN_TG')
TELEGRAM_CHAT_ID = os.getenv('TG_CHAT_ID')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения для работы программы."""
    logger.info('Началась проверка доступности переменных окружения.')
    tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    if not all(tokens):
        logger.critical('Отсутствует токен.')
        return False
    logger.info('Проверка прошла успешно.')
    return True


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    logger.debug('Началась отправка сообщения в Telegram.')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Отправлено сообщение: {message}')
    except telegram.TelegramError as error:
        logger.error(f'Ошибка отправки сообщения {error}')


def get_api_answer(timestamp):
    """Осуществление запроса к единственному эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    logger.debug(f'Выполнение работы API с полезной нагрузкой: {payload}')
    try:
        response = requests.get(ENDPOINT, headers=HEADERS,
                                params=payload)
    except requests.RequestException as error:
        raise ConnectionError(f'Не удалось получить ответ от API {error}'
                              f'при запросе {payload} и {HEADERS}.'
                              'Отсутствует доступ к серверу ЯП.')
    else:
        if response.status_code != HTTPStatus.OK:
            raise ValueError(f'Некорректный статус ответа'
                             f'API {response.status_code}'
                             f'при запросе {payload} и {HEADERS}.')
    logger.debug(f'Полученный ответ API: {response.json()}')
    return response.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарём.')
    if missed_keys := {'homeworks', 'current_date'} - response.keys():
        logger.error(f'В ответе API нет ожидаемых ключей: {missed_keys}')
        raise KeyError(f'В ответе API отсутствует(ют) ключ(и): {missed_keys}.')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Ответ API не является списком.')
    return homeworks


def parse_status(homework):
    """Извлечение статуса конкретной домашней работы."""
    if not isinstance(homework, dict):
        raise TypeError('Ответ от API не является словарём.')
    if missed_keys := {'homework_name', 'status'} - homework.keys():
        logger.error(f'В ответе API нет ожидаемых ключей: {missed_keys}')
        raise KeyError(f'В ответе API отсутствует(ют) ключ(и): {missed_keys}.')
    if homework.get('status') not in HOMEWORK_VERDICTS:
        raise KeyError('У домашней работы неизвестный статус.')
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_VERDICTS.get(homework.get('status'))
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit("Отсутствует обязательная переменная окружения")

    timestamp = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    message_last = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            timestamp = response['current_date']
            if homeworks:
                message = parse_status(homeworks[0])
                logger.info(f'Есть обновление {message}')
                if message != message_last:
                    send_message(bot, message)
                else:
                    logger.debug(message)
            else:
                message = 'Нет новых статусов'
            message_last = message
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != message_last:
                send_message(bot, message)
                message_last = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
