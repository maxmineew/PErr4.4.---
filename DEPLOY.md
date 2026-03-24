# Деплой бота и веба на VPS (Ubuntu 24.04)

Путь в примерах: `/root/PErr4.4.---` — при другом каталоге замените в unit-файлах и командах.

## 1. Система и репозиторий

```bash
apt update && apt upgrade -y
apt install -y git python3.12-venv python3-pip nginx
cd /root
git clone https://github.com/maxmineew/PErr4.4.---.git
cd PErr4.4.---
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-server.txt
```

## 2. Переменные окружения

Создайте `bot/.env` (файл в `.gitignore`; реальные ключи не вносите в репозиторий и не копируйте в тикеты/чаты):

```env
TELEGRAM_BOT_TOKEN=...
YANDEX_API_KEY=...
YANDEX_FOLDER_ID=...
YANDEX_DISK_TOKEN=...
YANDEX_DISK_FILE_PATH=/Заявки/applications.xlsx

FLASK_SECRET_KEY=случайная-длинная-строка
YANDEX_DISK_FILE_PATH_WEB=/Заявки/website_applications.xlsx
```

Веб-приложение читает тот же файл через `bot/.env` (см. `web/app/config.py`).

## 3. Проверка вручную

```bash
cd /root/PErr4.4.---
source .venv/bin/activate
python bot/bot.py          # Ctrl+C после проверки
cd web && gunicorn -w 1 -b 127.0.0.1:5000 "app:app"   # Ctrl+C
```

## 4. systemd: бот и веб как сервисы

```bash
cp /root/PErr4.4.---/deploy/perr-bot.service /etc/systemd/system/
cp /root/PErr4.4.---/deploy/perr-web.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now perr-bot.service perr-web.service
systemctl status perr-bot.service perr-web.service
```

Логи:

```bash
journalctl -u perr-bot.service -f
journalctl -u perr-web.service -f
```

## 5. Nginx (HTTP на порт 80 → веб)

```bash
cp /root/PErr4.4.---/deploy/nginx-perr.conf /etc/nginx/sites-available/perr
ln -sf /etc/nginx/sites-available/perr /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

Сайт: `http://ВАШ_IP/` или `http://ваш.домен` (после настройки `server_name` в nginx).

SSL (Let's Encrypt), если есть домен:

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d ваш.домен
```

## 6. Файрвол (опционально)

```bash
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
```

---

Если путь к проекту не `/root/PErr4.4.---`, отредактируйте `WorkingDirectory`, `ExecStart` и `EnvironmentFile` в `deploy/perr-bot.service` и `deploy/perr-web.service` перед копированием в `/etc/systemd/system/`.

## Ошибка `perr-web` / `perr-bot`: status=203/EXEC

Обычно **нет исполняемого файла** по пути в `ExecStart` (не то имя каталога venv или не установлены пакеты).

- Убедитесь, что окружение создано как **`/root/PErr4.4.---/.venv`** (как в разделе 1) и в нём: `pip install -r requirements-server.txt`.
- Если окружение у вас называется **`venv`**, а не **`.venv`**, отредактируйте `/etc/systemd/system/perr-*.service`: замените `/.venv/` на `/venv/`, затем `systemctl daemon-reload` и `restart`.
- Либо: `cd /root/PErr4.4.--- && ln -sfn venv .venv` (если есть только `venv`).
