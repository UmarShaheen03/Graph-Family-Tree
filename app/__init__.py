from flask import Flask
from .config import Config #from config.py import the Config class
#from flask_sqlalchemy import SQLAlchemy
#from flask_migrate import Migrate
#from flask_login import LoginManager
#import logging
#from logging.handlers import SMTPHandler
#from logging.handlers import RotatingFileHandler
import os

app = Flask(__name__)
app.config.from_object(Config)
#b = SQLAlchemy(app)
#migrate = Migrate(app, db)
#login = LoginManager(app)
#login.login_view = 'login'

from app import routes