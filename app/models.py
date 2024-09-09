from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from flask_login import UserMixin
from app import login
from hashlib import md5

class Biography(db.model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(50), nullable=True)
    biography = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    phonenumber = db.Column(db.Integer, nullable=True)
    address = db.Column(db.String(100), nullable=True)


class Comment(db.model):
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.Integer, db.ForeignKey('node.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)