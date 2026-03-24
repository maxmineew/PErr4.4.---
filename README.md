# PErr4.4 — Telegram-бот и веб-чат для заявок

Секреты (токены, ключи) **не хранятся в репозитории**. Создайте файл `bot/.env` по образцу `bot/.env.example` и заполните значения у себя локально или на сервере.

## Локальная разработка (Python 3.12)

```text
cd Проект
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements-server.txt
```

Скопируйте `bot/.env.example` → `bot/.env` и подставьте реальные переменные (без публикации в Git).

- **Бот:** `python bot/bot.py` — см. [bot/README.md](bot/README.md)
- **Веб:** `cd web` → `flask --app app run` — см. [web/README.md](web/README.md)

## Деплой на VPS

- [DEPLOY.md](DEPLOY.md) — systemd, nginx, `requirements-server.txt`
- В unit-файлах указано виртуальное окружение **`.venv`** в каталоге проекта (на сервере: `python3.12 -m venv .venv`).

## Репозиторий

```bash
git clone https://github.com/maxmineew/PErr4.4.---.git
```
