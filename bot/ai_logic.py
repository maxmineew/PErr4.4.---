# -*- coding: utf-8 -*-
"""
Модуль ИИ-логики — консультант интернет-магазина по установке окон.
Взаимодействие с YandexGPT и сценарий оформления заказа.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Literal

import requests

from catalog import CATALOG_TEXT, PAYMENT_METHODS, PRODUCTS
from config import (
    YANDEX_API_KEY,
    YANDEX_FOLDER_ID,
    YANDEXGPT_MAX_TOKENS,
    YANDEXGPT_MODEL,
    YANDEXGPT_TEMPERATURE,
)
from sheets import append_order

logger = logging.getLogger(__name__)

YANDEXGPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

# Поля заказа (расширенный сбор)
FIELDS = [
    "name",
    "contact",
    "product_model",
    "quantity",
    "address",
    "payment",
    "comment",
    "confirmed",
]
FIELD_LABELS = {
    "name": "имя",
    "contact": "телефон",
    "product_model": "товар из каталога",
    "quantity": "количество (шт или м²)",
    "address": "адрес доставки/установки",
    "payment": "способ оплаты",
    "comment": "комментарий к заказу",
    "confirmed": "подтверждение заказа (да/нет)",
}

SYSTEM_PROMPT = f"""Ты — консультант интернет-магазина по установке окон и остеклению лоджий.
Помогаешь оформить заказ, консультируешь по товарам.

КАТАЛОГ ТОВАРОВ:
{CATALOG_TEXT}

Собирай данные пошагово в строгом порядке:
1. Имя
2. Телефон
3. Выберите товар из каталога (назови код или опиши — помогу подобрать)
4. Количество (шт окон или м²)
5. Адрес доставки и установки
6. Способ оплаты: {', '.join(PAYMENT_METHODS)}
7. Комментарий (дополнения, пожелания)
8. Подтверждение: «Подтверждаю заказ» или «Да»

Правила:
- Будь вежлив и деловит. Помогай с выбором товара.
- Задавай по одному вопросу за раз.
- НИКОГДА не придумывай данные — спрашивай.
- Если пользователь пишет не по сценарию — мягко верни: «Давайте оформим заказ. Следующий шаг — ...»
- При выборе товара предлагай варианты из каталога.
- Когда все поля собраны и заказ подтверждён, напиши ровно: [ЗАКАЗ_ГОТОВ]
- Отвечай кратко (1–3 предложения). Без markdown.
"""


@dataclass
class UserState:
    """Состояние пользователя при оформлении заказа."""
    current_field_index: int = 0
    collected_data: dict = field(
        default_factory=lambda: {
            "name": "", "contact": "", "product_model": "",
            "quantity": "", "address": "", "payment": "", "comment": "", "confirmed": ""
        }
    )

    def get_current_field(self) -> str | None:
        if self.current_field_index >= len(FIELDS):
            return None
        return FIELDS[self.current_field_index]

    def set_field_value(self, field_key: str, value: str) -> None:
        if field_key in self.collected_data:
            self.collected_data[field_key] = value.strip()

    def move_next(self) -> None:
        self.current_field_index = min(self.current_field_index + 1, len(FIELDS))

    def is_complete(self) -> bool:
        return all(self.collected_data.get(f) for f in FIELDS)

    def reset(self) -> None:
        self.current_field_index = 0
        self.collected_data = {
            "name": "", "contact": "", "product_model": "",
            "quantity": "", "address": "", "payment": "", "comment": "", "confirmed": ""
        }


def call_yandexgpt(messages: list[dict]) -> str:
    payload = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/{YANDEXGPT_MODEL}",
        "completionOptions": {
            "temperature": YANDEXGPT_TEMPERATURE,
            "maxTokens": str(YANDEXGPT_MAX_TOKENS),
        },
        "messages": [{"role": m["role"], "text": m["text"]} for m in messages],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
    }
    try:
        response = requests.post(YANDEXGPT_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "")
    except Exception as e:
        logger.exception("Ошибка вызова YandexGPT: %s", e)
        return "Извините, произошла техническая ошибка. Попробуйте позже."


def _match_product(text: str) -> str | None:
    """Пытается сопоставить текст с товаром из каталога."""
    text_upper = text.upper().strip()
    for code in PRODUCTS:
        if code.replace("_", " ") in text_upper.replace("_", " "):
            return PRODUCTS[code][0]
    # По ключевым словам
    kw_map = {
        "rehau": "Окна Rehau Standard", "veka": "Окна VEKA Standard",
        "лоджи": "Остекление лоджии тёплое", "балкон": "Остекление лоджии тёплое",
        "холодн": "Остекление лоджии холодное", "подоконник": "Подоконник стандарт",
        "сетк": "Москитная сетка", "отлив": "Отлив водосточный",
        "штор": "Рулонные шторы",
    }
    for kw, name in kw_map.items():
        if kw in text.lower():
            return name
    return None


def _match_payment(text: str) -> str | None:
    text_lower = text.lower().strip()
    for method in PAYMENT_METHODS:
        if any(w in text_lower for w in method.split()[:2]):
            return method
    if "налич" in text_lower or "нал" in text_lower:
        return "наличными при получении"
    if "карт" in text_lower:
        return "картой при получении"
    if "предоплат" in text_lower or "50" in text_lower:
        return "предоплата 50%"
    if "рассроч" in text_lower:
        return "рассрочка 0%"
    if "онлайн" in text_lower:
        return "онлайн-оплата"
    return None


def _is_confirmation(text: str) -> bool:
    t = text.lower().strip()
    return any(w in t for w in ["да", "подтверждаю", "верно", "ок", "давай", "заказываю"])


def extract_field_from_response(response: str, field_key: str) -> str | None:
    text = response.strip()
    if not text:
        return None

    if field_key == "name":
        parts = text.split()
        return " ".join(parts[:3]) if parts else text
    elif field_key == "contact":
        if "@" in text:
            return text
        digits = "".join(c for c in text if c.isdigit() or c in "+- ()")
        if len(digits) >= 10:
            return digits
        return text
    elif field_key == "product_model":
        return _match_product(text) or text
    elif field_key == "quantity":
        nums = re.findall(r"\d+", text)
        return nums[0] if nums else text
    elif field_key == "address":
        return text
    elif field_key == "payment":
        return _match_payment(text) or text
    elif field_key == "comment":
        return text
    elif field_key == "confirmed":
        return "Да" if _is_confirmation(text) else None
    return text


def process_user_message(
    user_id: int,
    user_message: str,
    state: UserState,
    history: list[dict],
) -> tuple[str, UserState, Literal["continue", "complete", "error"]]:
    current_field = state.get_current_field()

    if current_field and user_message.strip():
        extracted = extract_field_from_response(user_message, current_field)
        if extracted:
            state.set_field_value(current_field, extracted)
            state.move_next()

    context_parts = []
    for f in FIELDS:
        if state.collected_data.get(f):
            context_parts.append(f"{FIELD_LABELS[f]}: {state.collected_data[f]}")
    context = "\n".join(context_parts) if context_parts else "Пока ничего не собрано."

    user_context = f"[Уже собрано: {context}]\nПользователь: {user_message}"

    messages = [
        {"role": "system", "text": SYSTEM_PROMPT},
        *[{"role": h["role"], "text": h["text"]} for h in history],
        {"role": "user", "text": user_context},
    ]

    assistant_reply = call_yandexgpt(messages)

    history.append({"role": "user", "text": user_message})
    history.append({"role": "assistant", "text": assistant_reply})

    if len(history) > 12:
        history[:] = history[-12:]

    if "[ЗАКАЗ_ГОТОВ]" in assistant_reply or state.is_complete():
        if not state.is_complete():
            for h in reversed(history):
                if h["role"] == "user" and h["text"]:
                    for f in FIELDS:
                        if not state.collected_data.get(f):
                            val = extract_field_from_response(h["text"], f)
                            if val:
                                state.set_field_value(f, val)

        if state.is_complete():
            d = state.collected_data
            success, used_backup = append_order(
                name=d["name"],
                contact=d["contact"],
                product=d["product_model"],
                quantity=d["quantity"],
                address=d["address"],
                payment=d["payment"],
                comment=d.get("comment", ""),
                telegram_user_id=user_id,
            )
            if success:
                reply = "Спасибо! Ваш заказ принят. Менеджер свяжется с вами в ближайшее время для согласования деталей."
            elif used_backup:
                reply = "Заказ принят и сохранён локально. Мы свяжемся с вами. (Запись в облако временно недоступна.)"
            else:
                reply = "К сожалению, при сохранении заказа произошла ошибка. Пожалуйста, попробуйте позже или свяжитесь с нами по телефону."
            state.reset()
            return reply, state, "complete"

    reply = assistant_reply.replace("[ЗАКАЗ_ГОТОВ]", "").strip()
    return reply, state, "continue"
