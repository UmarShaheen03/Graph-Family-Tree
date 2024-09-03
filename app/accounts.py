from app.models import User
from flask_login import login_user
from app.databases import db
from werkzeug.security import generate_password_hash
from flask import current_app
import smtplib

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
        username="admin_test",
        email="admin@test.com",
        privilege=1,
        password_hash=str(generate_password_hash("admin1234"))
    )

    test_user = User(
        user_id=1,
        username="user_test",
        email="user@test.com",
        privilege=0,
        password_hash=str(generate_password_hash("user1234"))
    )

    #add mock accounts to db
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
    
    #get a new user_id, +1 from the last user_id
    #TODO: make the user ids more random? harder to guess
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

def reset_email(email):
    user = db.session.query(User).filter(User.email == email).first()
    if user == None:
        return #return without error if no matching user, vulnerable if it reports when user does/doesn't exist
    
    #TODO send email, with link to specific page to reset password
    pass