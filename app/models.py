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
    reset_expiry = db.Column(db.Integer) #is a datetime, but i store it as an int
    comments = db.relationship('Comment', back_populates='user', lazy=True)
    email_preference = db.Column(db.String) #values of "None", "Daily" or "Weekly"


    def get_id(self):
        return (self.user_id)
    
    def get_username(self):
        return (self.username)

    def get_email(self):
        return (self.email)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password) 
    
    def unsubscribe(self):
        self.email_preference = "None"
    
    @login.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

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

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
    bio_id = db.Column(db.Integer, db.ForeignKey('biography.id'), nullable=True)
    tree_id = db.Column(db.Integer) #TODO link to tree model
    text = db.Column(db.Text, nullable=False)
    admin = db.Column(db.Boolean)
    acknowledged = db.Column(db.Boolean)

#what to log:
#   - account creation (viewable to admins, linked to user)
#   - logins (viewable to admins, linked to user)
#   - admin requests (viewable to admins, linked to user)
#   - tree requests (viewable to admins, linked to user)

#   - request acceptance (viewavle to users, linked to user)
#   - tree edits (viewable to users, linked to tree)
#   - biography edits (viewable to users, linked to bio)
#   - comments (viewable to users, linked to bio)

# options
#   - toggles for each type of notification
#   - toggles for how often to email (daily, weekly, monthly?, none)



#   - put all on the email? or just a few
#   - have how often be per type or overall
#   - unsubscribe link on email