# -*- coding: utf-8 -*-
"""Маршруты веб-приложения."""

import secrets
from collections import defaultdict

from flask import jsonify, render_template, request, send_from_directory

from app.ai_logic import process


def register_routes(app):
    # История по session_id для контекста ИИ
    histories: dict[str, list[dict]] = defaultdict(list)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/chat", methods=["POST"])
    def chat():
        data = request.get_json() or {}
        msg = (data.get("message") or "").strip()
        if not msg:
            return jsonify({"reply": "Введите сообщение.", "done": False}), 400

        sid = request.cookies.get("session_id") or secrets.token_hex(16)
        history = histories[sid]
        reply, done = process(sid, msg, history)
        resp = jsonify({"reply": reply, "done": done})
        resp.set_cookie("session_id", sid, max_age=86400 * 7)
        return resp
