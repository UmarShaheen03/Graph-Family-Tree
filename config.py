"""Flask app configurations"""

import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """General base config class"""
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'

    #Cryptographic key for signature/tokens to defend web forms against CSRF
    SECRET_KEY = "test1234"
    # SECRET_KEY = os.environ.get('SECRET_KEY')
    
    WTF_CSRF_ENABLED = False

class DeploymentConfig(Config):
  SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')

class TestConfig(Config):
  SQLALCHEMY_DATABASE_URI = "sqlite:///:memory" #store db in memory, not with uri
  TESTING = True