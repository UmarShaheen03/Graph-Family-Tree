"""This module is the entry point for the flask application"""

import os
import logging
from logging.handlers import SMTPHandler
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config #from config.py import the Config class
from flask_wtf import CSRFProtect

from .databases import db, login
from .main import main_bp
from jinja2 import Environment

def create_app():
    """Create and configure app"""
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)
    flask_app.config['IMAGE_UPLOADS'] = os.path.join(flask_app.root_path,'static', 'uploads')
    csrf = CSRFProtect(flask_app)

    db.init_app(flask_app)
    login.init_app(flask_app)

    migrate = Migrate(flask_app, db)

    flask_app.register_blueprint(main_bp)

    return flask_app
