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
    token = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    if not all(token):
        logger.critical(f'Отсутствует токен: {token}')
        sys.exit('Переменные окружения отсутствуют.')
    logger.info('Проверка прошла успешно.')


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Отправлено сообщение: {message}')
    except telegram.TelegramError as error:
        logger.error(f'Ошибка отправки сообщения {error}')


def get_api_answer(timestamp):
    """Осуществление запроса к единственному эндпоинту API-сервиса."""
    timestamp = int(time.time())
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS,
                                params=payload)
    except requests.RequestException as error:
        raise ConnectionError(f'Не удалось получить ответ от API {error}.'
                              'Отсутствует доступ к серверу ЯП.')
    else:
        if response.status_code != HTTPStatus.OK:
            raise ValueError('Некорректный статус ответа API.')
    return response.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарём.')
    if 'homeworks' not in response:
        raise KeyError('В ответе API отсутствует ключ homeworks.')
    if 'current_date' not in response:
        raise KeyError('В ответе API отсутствует ключ current_date.')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Ответ API не является списком.')
    return homeworks


def parse_status(homework):
    """Извлечение статуса конкретной домашней работы."""
    if not isinstance(homework, dict):
        raise TypeError('Ответ от API не является словарём.')
    if 'homework_name' not in homework:
        raise KeyError('В ответе от API отсутствует ключ homework_name.')
    if homework.get('status') not in HOMEWORK_VERDICTS:
        raise KeyError('У домашней работы неизвестный статус.')
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_VERDICTS.get(homework.get('status'))
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    message_last = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                logger.info(f'Есть обновление {message}')
            else:
                message = 'Нет новых статусов'
            if message != message_last:
                send_message(bot, message)
                message_last = message
            else:
                logger.debug(message)
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
