"""Flask app configurations"""

import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """General base config class"""
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'

    #Cryptographic key for signature/tokens to defend web forms against CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')