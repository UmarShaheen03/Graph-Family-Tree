from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin, LoginManager
from hashlib import md5
from app.databases import db, login

class User(UserMixin, db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False) 
    password_hash = db.Column(db.String, nullable=False)
    admin = db.Column(db.Boolean)
    reset_token = db.Column(db.String)
    reset_expiry = db.Column(db.Integer) #is a datetime, but i treat it as an int

    def get_id(self):
        return (self.user_id)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password) 
    
    @login.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))