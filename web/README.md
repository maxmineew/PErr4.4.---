# Веб-чат-виджет для сбора заявок

Лендинг с ИИ-ассистентом. Собирает: имя, контакт, описание запроса. Сохраняет в лист **«Заявки с сайта»** на Яндекс Диске.

## Запуск

```bash
cd web
pip install -r requirements.txt
flask --app app run
```

Либо из корня проекта (если используется общий venv):

```bash
cd web
../venv/Scripts/python.exe -m flask --app app run
```

Откройте http://127.0.0.1:5000

## Переменные окружения

Создайте `.env` в папке `web/` или в корне проекта:

```
FLASK_SECRET_KEY=ваш-секрет
YANDEX_API_KEY=...
YANDEX_FOLDER_ID=...
YANDEX_DISK_TOKEN=...
YANDEX_DISK_FILE_PATH_WEB=/Заявки/website_applications.xlsx
```

Используются те же ключи, что и для Telegram-бота. Файл на Диске — отдельный (`website_applications.xlsx`), лист «Заявки с сайта».

## Деплой

```bash
gunicorn -w 1 -b 0.0.0.0:5000 "app:app"
```

Из папки `web/` с установленным `gunicorn`.
