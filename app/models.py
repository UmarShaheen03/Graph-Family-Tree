from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from flask_login import UserMixin
from app import login
from hashlib import md5

STRING_MAX = 999 #max length of strings in the db

class User(UserMixin, db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(STRING_MAX), unique=True, nullable=False)
    email = db.Column(db.String(STRING_MAX), unique=True, nullable=False) 
    password_hash = db.Column(db.String(STRING_MAX), nullable=False)
    privillege = db.Column(db.Integer)

    def get_id(self):
        return (self.user_id)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password) 