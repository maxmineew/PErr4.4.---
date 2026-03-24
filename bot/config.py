# -*- coding: utf-8 -*-
"""
Модуль конфигурации — загрузка переменных окружения и констант.
Все секретные данные хранятся в .env и загружаются через dotenv.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем .env — из корня и bot/ (bot перезаписывает для совпадений)
base = Path(__file__).resolve().parent
load_dotenv(dotenv_path=base.parent / ".env")
load_dotenv(dotenv_path=base / ".env")


def get_env(key: str, default: str | None = None, required: bool = False) -> str | None:
    """
    Получить переменную окружения.

    Args:
        key: Имя переменной
        default: Значение по умолчанию
        required: Если True, отсутствие переменной вызовет ошибку

    Returns:
        Значение переменной или default
    """
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"Переменная окружения {key} обязательна, но не задана")
    return value


# Telegram
TELEGRAM_BOT_TOKEN = get_env("TELEGRAM_BOT_TOKEN", required=True)

# YandexGPT (Яндекс Облако)
YANDEX_API_KEY = get_env("YANDEX_API_KEY", required=True)
YANDEX_FOLDER_ID = get_env("YANDEX_FOLDER_ID", required=True)

# Яндекс Диск — хранение заявок (Excel-файл)
YANDEX_DISK_TOKEN = get_env("YANDEX_DISK_TOKEN", required=True)
YANDEX_DISK_FILE_PATH = get_env("YANDEX_DISK_FILE_PATH", "/Заявки/applications.xlsx")

# Настройки LLM
YANDEXGPT_MODEL = "yandexgpt/latest"
YANDEXGPT_TEMPERATURE = 0.6
YANDEXGPT_MAX_TOKENS = 1024
