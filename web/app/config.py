# -*- coding: utf-8 -*-
"""Конфигурация веб-приложения."""

import os
from pathlib import Path

from dotenv import load_dotenv

base = Path(__file__).resolve().parent.parent
for p in (base.parent / ".env", base / ".env", base.parent / "bot" / ".env"):
    if p.exists():
        load_dotenv(p)


def _get(key: str, default: str | None = None, required: bool = False) -> str | None:
    v = os.getenv(key, default)
    if required and not v:
        raise ValueError(f"Переменная {key} обязательна")
    return v


SECRET_KEY = _get("FLASK_SECRET_KEY", "dev-secret-change-me", required=False)
YANDEX_API_KEY = _get("YANDEX_API_KEY", required=True)
YANDEX_FOLDER_ID = _get("YANDEX_FOLDER_ID", required=True)
YANDEX_DISK_TOKEN = _get("YANDEX_DISK_TOKEN", required=True)
YANDEX_DISK_FILE_PATH = _get("YANDEX_DISK_FILE_PATH_WEB", "/Заявки/website_applications.xlsx")
