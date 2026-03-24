# Telegram-бот — консультант интернет-магазина по установке окон

Бот работает как консультант компании по установке окон и остеклению лоджий. Помогает оформить заказ: собирает имя, телефон, товар из каталога, количество, адрес, способ оплаты и подтверждение. Использует YandexGPT для диалога, сохраняет заказы в Excel на **Яндекс Диске**.

## Структура проекта

```
bot/
├── bot.py        # Запуск Telegram-бота
├── ai_logic.py   # ИИ-логика YandexGPT, сценарий оформления заказа
├── catalog.py   # Каталог товаров (окна, остекление и др.)
├── sheets.py    # Запись заказов в Excel на Яндекс Диске
├── config.py    # Переменные окружения
├── requirements.txt
└── README.md
```

## Требования

- Python 3.12+
- Аккаунт Telegram (бот создаётся через [@BotFather](https://t.me/BotFather))
- [Yandex Cloud](https://cloud.yandex.ru/) — для YandexGPT
- [Яндекс ID](https://oauth.yandex.ru/) — OAuth-токен для Яндекс Диска

## Установка

### 1. Зависимости

```bash
cd Проект
py -3.12 -m venv venv   # или python -m venv venv, если python — это 3.12
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/macOS
pip install -r bot/requirements.txt
```

> **На Windows с несколькими версиями Python** — используйте `py -3.12 -m venv venv`, чтобы явно создать окружение на Python 3.12.

**При таймаутах PyPI** — используйте зеркало и увеличенный таймаут:

```bash
# Windows (или запустите install.bat)
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn --timeout 120 -r bot/requirements.txt
```

Либо настройте pip глобально: создайте `%APPDATA%\pip\pip.ini` (Windows) с содержимым:

```ini
[global]
timeout = 120
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

### 2. Переменные окружения

Создайте файл `.env` в корне проекта (рядом с папкой `bot/`):

```env
# Telegram — получите у @BotFather
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# YandexGPT — Yandex Cloud
YANDEX_API_KEY=ваш_api_ключ
YANDEX_FOLDER_ID=идентификатор_каталога

# Яндекс Диск
YANDEX_DISK_TOKEN=OAuth_токен_для_диска
YANDEX_DISK_FILE_PATH=/Заявки/applications.xlsx
```

### 3. Telegram-бот

1. Напишите [@BotFather](https://t.me/BotFather)
2. Команда `/newbot` → укажите имя и username
3. Скопируйте токен в `TELEGRAM_BOT_TOKEN`

### 4. YandexGPT

1. Зарегистрируйтесь на [cloud.yandex.ru](https://cloud.yandex.ru/)
2. Создайте каталог (Folder)
3. Включите сервис **YandexGPT** в этом каталоге
4. Создайте API-ключ: **IAM** → **API-ключи** → **Создать**
5. Скопируйте ключ и Folder ID в `.env`

### 5. Яндекс Диск (OAuth-токен)

1. Перейдите в [OAuth Яндекс ID](https://oauth.yandex.ru/)
2. Создайте приложение (если ещё нет)
3. Укажите права доступа: **Яндекс.Диск** (чтение и запись)
4. Получите OAuth-токен — перейдите по ссылке:
   ```
   https://oauth.yandex.ru/authorize?response_type=token&client_id=<ID_приложения>
   ```
5. Авторизуйтесь и скопируйте `access_token` из URL в `YANDEX_DISK_TOKEN`
6. Путь к файлу: `YANDEX_DISK_FILE_PATH=/Заявки/applications.xlsx`
   - Файл создаётся автоматически при первой заявке
   - Папка `Заявки` также создаётся при необходимости

> **Срок действия токена:** OAuth-токен Яндекс Диска действует 1 год. После истечения получите новый токен.

## Запуск

```bash
# Из корня проекта (Проект/)
python bot/bot.py
```

Или из папки `bot/`:

```bash
cd bot
python bot.py
```

## Команды бота

| Команда   | Описание               |
|-----------|------------------------|
| `/start`  | Начать сбор заявки      |
| `/help`   | Справка                |
| `/cancel` | Отменить текущую заявку|

## Логика оформления заказа

1. **Имя** — как к вам обращаться
2. **Телефон** — для связи
3. **Товар** — выбор из каталога (окна, остекление лоджий, подоконники и др.)
4. **Количество** — шт или м²
5. **Адрес** — доставки и установки
6. **Способ оплаты** — наличные, карта, предоплата, рассрочка
7. **Комментарий** — дополнения к заказу
8. **Подтверждение** — «Да» или «Подтверждаю заказ»

YandexGPT ведёт диалог и помогает с выбором товара. После заполнения всех полей заказ сохраняется в Excel на Яндекс Диске.

## Просмотр заявок

Откройте файл `applications.xlsx` в [Яндекс Диске](https://disk.yandex.ru/) или **Яндекс Таблицах**. Колонки: Имя, Контакт, Товар, Количество, Адрес, Оплата, Комментарий, Telegram ID.

## Логирование

```
2025-03-23 12:00:00 [INFO] __main__: Бот запущен
2025-03-23 12:00:15 [INFO] __main__: Пользователь 123456789 начал сессию
2025-03-23 12:01:30 [INFO] sheets: Заявка успешно сохранена в Яндекс Диск: Иван
```

## Устранение неполадок

- **Ошибка авторизации YandexGPT** — проверьте `YANDEX_API_KEY`, `YANDEX_FOLDER_ID` и подключение YandexGPT в каталоге.
- **Ошибка Яндекс Диска (403 Forbidden)** — у OAuth-приложения нет прав на запись. Зайдите на [oauth.yandex.ru](https://oauth.yandex.ru/) → ваше приложение → раздел «Доступ к данным» → включите **«Запись в любом месте на диске»**. Затем получите новый токен по ссылке авторизации и обновите `YANDEX_DISK_TOKEN`.
- **Проверка Диска** — запустите `venv\Scripts\python.exe bot\test_disk.py` для диагностики.
- **Лог ошибок** — при сбоях смотрите `bot_errors.log` в корне проекта.
- **Резерв при ошибке Диска** — заказы сохраняются в `orders_backup.csv` в корне проекта.
- **Бот не отвечает** — проверьте `TELEGRAM_BOT_TOKEN` и подключение к интернету.
