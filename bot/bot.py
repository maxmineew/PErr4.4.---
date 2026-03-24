# -*- coding: utf-8 -*-
"""
Точка входа — запуск Telegram-бота с ИИ-ассистентом для сбора заявок.
"""

import logging
from collections import defaultdict

import telebot
from telebot import types

from ai_logic import UserState, process_user_message
from config import TELEGRAM_BOT_TOKEN
from sheets import try_sync_backup

# Логирование: консоль (INFO) + bot.log (все INFO+) + bot_errors.log (только ERROR)
from logging.handlers import RotatingFileHandler
from pathlib import Path

_log_dir = Path(__file__).resolve().parent.parent
_fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=_fmt,
    datefmt="%Y-%m-%d %H:%M:%S",
)
_root = logging.getLogger()

# Полный журнал (в т.ч. ответы API YandexGPT при ошибках)
_log_all = _log_dir / "bot.log"
_file_info = RotatingFileHandler(
    _log_all, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_file_info.setLevel(logging.INFO)
_file_info.setFormatter(logging.Formatter(_fmt, datefmt="%Y-%m-%d %H:%M:%S"))
_root.addHandler(_file_info)

# Только ошибки — отдельный файл для быстрого поиска
_log_err = _log_dir / "bot_errors.log"
_file_err = RotatingFileHandler(
    _log_err, maxBytes=2 * 1024 * 1024, backupCount=2, encoding="utf-8"
)
_file_err.setLevel(logging.ERROR)
_file_err.setFormatter(logging.Formatter(_fmt, datefmt="%Y-%m-%d %H:%M:%S"))
_root.addHandler(_file_err)

logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Состояние пользователей: user_id -> (UserState, history)
user_sessions: dict[int, tuple[UserState, list[dict]]] = defaultdict(
    lambda: (UserState(), [])
)


def get_session(user_id: int) -> tuple[UserState, list[dict]]:
    """Возвращает состояние и историю диалога пользователя."""
    return user_sessions[user_id]


def reset_session(user_id: int) -> None:
    """Сбрасывает сессию пользователя."""
    user_sessions[user_id] = (UserState(), [])


@bot.message_handler(commands=["start"])
def handle_start(message: types.Message) -> None:
    """Обработка команды /start — приветствие и начало сбора заявки."""
    user_id = message.from_user.id
    reset_session(user_id)
    
    welcome = (
        "Здравствуйте! 👋 Я консультант компании по установке окон и остеклению лоджий.\n\n"
        "Помогу подобрать товар и оформить заказ. Сначала — как вас зовут?"
    )
    bot.reply_to(message, welcome)
    logger.info("Пользователь %s начал сессию", user_id)


@bot.message_handler(commands=["help"])
def handle_help(message: types.Message) -> None:
    """Обработка команды /help."""
    help_text = (
        "Я помогаю оформить заказ: пластиковые окна, остекление лоджий, подоконники и др.\n"
        "Соберу: имя, телефон, товар, количество, адрес, способ оплаты.\n\n"
        "/start — оформить новый заказ\n"
        "/help — эта справка"
    )
    bot.reply_to(message, help_text)


@bot.message_handler(commands=["cancel"])
def handle_cancel(message: types.Message) -> None:
    """Отмена текущей заявки."""
    user_id = message.from_user.id
    reset_session(user_id)
    bot.reply_to(message, "Заказ отменён. Чтобы начать заново, отправьте /start")
    logger.info("Пользователь %s отменил заказ", user_id)


@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_message(message: types.Message) -> None:
    """Обработка текстовых сообщений — диалог с ИИ-ассистентом."""
    user_id = message.from_user.id
    text = message.text or ""
    
    state, history = get_session(user_id)
    
    reply, new_state, status = process_user_message(
        user_id=user_id,
        user_message=text,
        state=state,
        history=history,
    )
    
    # Обновляем состояние в сессии
    user_sessions[user_id] = (new_state, history)
    
    if status == "complete":
        reset_session(user_id)
    
    try:
        bot.reply_to(message, reply)
    except Exception as e:
        logger.exception("Ошибка отправки сообщения пользователю %s: %s", user_id, e)
        bot.reply_to(message, "Произошла ошибка. Попробуйте /start")


def main() -> None:
    """Запуск бота."""
    if try_sync_backup():
        logger.info("Заказы из backup перенесены в облако")
    logger.info("Бот запущен")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
