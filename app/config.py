import os
basedir = os.path.abs(os.path.dirname(__file__))

class Config:
    
    #Cryptographic key for signature/tokens to defend web forms against CSRF
  SECRET_KEY = os.environ.get('SECRET_KEY')
  
  SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')