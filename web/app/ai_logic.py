# -*- coding: utf-8 -*-
"""
ИИ-логика для веб-виджета — сбор заявки (имя, контакт, описание).
Без продаж, вежливый тон, уточняющие вопросы.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field

import requests

from app.config import (
    YANDEX_API_KEY,
    YANDEX_FOLDER_ID,
)
from app.sheets import append_lead

logger = logging.getLogger(__name__)

URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

FIELDS = ["name", "contact", "description"]
LABELS = {"name": "имя", "contact": "контакт (телефон или email)", "description": "описание запроса"}

SYSTEM_PROMPT = """Ты — вежливый ассистент для сбора заявки с сайта.
Собирай данные пошагово:
1. Имя
2. Контакт (телефон или email)
3. Описание запроса

Правила:
- Вежливый, нейтральный тон. Задавай уточняющие вопросы по запросу.
- НЕ уходи в продажи — только сбор информации, без навязывания товаров/услуг.
- Не придумывай данные — спрашивай.
- Если пользователь уходит от темы — мягко верни: «Давайте соберём заявку. Следующий шаг — ...»
- Один вопрос за раз. Отвечай кратко (1–3 предложения). Без markdown.
- Когда все три поля собраны, напиши ровно: [ЗАЯВКА_ГОТОВА]
"""


@dataclass
class SessionState:
    current_field: int = 0
    data: dict = field(default_factory=lambda: {"name": "", "contact": "", "description": ""})

    def get_field(self) -> str | None:
        return FIELDS[self.current_field] if self.current_field < len(FIELDS) else None

    def set(self, k: str, v: str) -> None:
        if k in self.data:
            self.data[k] = v.strip()

    def next(self) -> None:
        self.current_field = min(self.current_field + 1, len(FIELDS))

    def is_complete(self) -> bool:
        return all(self.data.get(f) for f in FIELDS)

    def reset(self) -> None:
        self.current_field = 0
        self.data = {"name": "", "contact": "", "description": ""}


# Сессии по session_id (cookie или IP)
_sessions: dict[str, SessionState] = defaultdict(SessionState)


def _call_gpt(messages: list[dict]) -> str:
    try:
        r = requests.post(
            URL,
            json={
                "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest",
                "completionOptions": {"temperature": 0.6, "maxTokens": "1024"},
                "messages": [{"role": m["role"], "text": m["text"]} for m in messages],
            },
            headers={"Content-Type": "application/json", "Authorization": f"Api-Key {YANDEX_API_KEY}"},
            timeout=30,
        )
        if not r.ok:
            logger.error(
                "YandexGPT HTTP %s: %s",
                r.status_code,
                (r.text or "")[:4000],
            )
        r.raise_for_status()
        return r.json().get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "")
    except Exception as e:
        logger.exception("YandexGPT: %s", e)
        return "Извините, произошла ошибка. Попробуйте позже."


def _extract(text: str, field: str) -> str | None:
    t = text.strip()
    if not t:
        return None
    if field == "name":
        return " ".join(t.split()[:3])
    if field == "contact":
        if "@" in t:
            return t
        d = "".join(c for c in t if c.isdigit() or c in "+- ()")
        return d if len(d) >= 10 else t
    if field == "description":
        return t
    return t


def process(session_id: str, message: str, history: list[dict]) -> tuple[str, bool]:
    """
    Обрабатывает сообщение. Возвращает (ответ, заявка_принята).
    """
    state = _sessions[session_id]
    cur = state.get_field()

    if cur and message.strip():
        val = _extract(message, cur)
        if val:
            state.set(cur, val)
            state.next()

    ctx = "\n".join(f"{LABELS[f]}: {state.data[f]}" for f in FIELDS if state.data.get(f)) or "Пока ничего."
    user_ctx = f"[Собрано: {ctx}]\nПользователь: {message}"

    msgs = [
        {"role": "system", "text": SYSTEM_PROMPT},
        *[{"role": h["role"], "text": h["text"]} for h in history[-8:]],
        {"role": "user", "text": user_ctx},
    ]
    reply = _call_gpt(msgs)

    history.append({"role": "user", "text": message})
    history.append({"role": "assistant", "text": reply})

    if "[ЗАЯВКА_ГОТОВА]" in reply or state.is_complete():
        if state.is_complete():
            ok = append_lead(state.data["name"], state.data["contact"], state.data["description"])
            state.reset()
            return (
                "Спасибо! Ваша заявка принята. Мы свяжемся с вами в ближайшее время."
                if ok else "Ошибка сохранения. Попробуйте позже или свяжитесь напрямую.",
                True,
            )

    return reply.replace("[ЗАЯВКА_ГОТОВА]", "").strip(), False
