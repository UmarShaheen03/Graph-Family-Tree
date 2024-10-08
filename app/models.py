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
    
    def get_username(self):
        return (self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password) 
    
    @login.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    comments = db.relationship('Comment', back_populates='user', lazy=True)

    def is_admin(self):
        return (self.admin)
    

class Biography(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(50), nullable=True)
    biography = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    phonenumber = db.Column(db.Integer, nullable=True)
    address = db.Column(db.String(100), nullable=True)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=False)
    text = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', back_populates='comments') 

