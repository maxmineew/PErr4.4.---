# -*- coding: utf-8 -*-
"""Flask-приложение для веб-чат-виджета сбора заявок."""

from flask import Flask

app = Flask(__name__, static_folder=None, template_folder="../templates")

from app import config
app.config["SECRET_KEY"] = config.SECRET_KEY

from app.routes import register_routes
register_routes(app)
