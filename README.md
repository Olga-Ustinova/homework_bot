# homework_bot
Telegram-bot, который обращается к API сервиса Практикум.Домашка и узнаёт статус вашей домашней работы.

При обновлении статуса вашей последней работы бот анализирует ответ API и отправляет соответствующее уведомление в Telegram.
Логирование ведётся в stdout.

## Используемые технологии
* [Python](https://www.python.org/downloads/release/python-3910/),
* [Python-telegram-bot](https://docs.python-telegram-bot.org/en/v13.7/),
* [Python-dotenv](https://pypi.org/project/python-dotenv/0.19.0/),
* [Requests](https://pypi.org/project/requests/2.26.0/).

## Запуск бота
1. Клонируйте репозиторий и перейдите в него в командной строке:
```bash
git clone git@github.com:Olga-Ustinova/homework_bot.git

cd homework_bot
```
2. Создайте и активируйте виртуальное окружение, установите зависимости из файла `requirements.txt` и выполните миграции:
```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
python manage.py migrate
```
3. Создайте файл `.env` в корневой директории с переменными окружения:
* `PRAKTIKUM_TOKEN` - токен API сервиса Практикум.Домашка;
* `TELEGRAM_TOKEN` - токен Telegram-бота;
* `TELEGRAM_CHAT_ID` - ID чата адресата оповещения.
4. Запустите скрипт:
```bash
python homework.py
```
## Об авторе
[Olga-Ustinova](https://github.com/Olga-Ustinova)
