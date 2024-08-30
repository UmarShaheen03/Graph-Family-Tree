from app.models import User
from flask_login import login_user
from app.databases import db
from werkzeug.security import generate_password_hash
from flask import current_app

class SignupError(Exception):
    pass

class LoginError(Exception):
    pass

def init_database():
    #create tables
    db.create_all()
    #clear any existing info (for testing DO NOT KEEP IN FINAL)
    User.query.delete()

    #create mock accounts
    test_admin = User(
        user_id=0,
        username="test_admin",
        email="admin@test.com",
        privilege=1,
        password_hash=str(generate_password_hash("admin1234"))
    )

    test_user = User(
        user_id=1,
        username="test_user",
        email="user@test.com",
        privilege=0,
        password_hash=str(generate_password_hash("user1234"))
    )

    db.session.add(test_admin)
    db.session.add(test_user)
    db.session.commit()

def signup(email, username, password, repeat, remember):
    if password != repeat:
        raise SignupError("Passwords do not match")
    
    if db.session.query(User).filter(User.email == email).first() != None:
        raise SignupError("Email already exists")

    if db.session.query(User).filter(User.username == username).first() != None:
        raise SignupError("Username already exists")
    
    #get a new user_id, +1 to last user_id
    new_id = db.session.query(User).order_by(User.user_id.desc()).first().user_id + 1

    #construct user object
    user = User(
        user_id = new_id,
        username = username,
        email = email,
        privilege = 0 #default privilege is 0, for user level
    )

    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()

    login(username, password, remember)
    
def login(email_or_username, password, remember):
    user = db.session.query(User).filter((User.username == email_or_username) | (User.email == email_or_username)).first()

    if not user:
        raise LoginError("User does not exist")
    
    if not user.check_password(password):
        raise LoginError("Incorrect password")
    
    login_user(user, remember=remember)