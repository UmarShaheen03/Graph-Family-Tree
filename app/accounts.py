from app.models import User
from flask_login import login_user
from app.databases import db
from werkzeug.security import generate_password_hash

class SignupError(Exception):
    pass

class LoginError(Exception):
    pass

def init_database():
    #create tables
    db.create_all()
    #clear any existing info 
    User.query.delete()

    #create mock accounts
    test_admin = User(
        user_id=0,
        username="test_admin",
        email="admin@test.com",
        privillege=1,
        password_hash=str(generate_password_hash("admin1234"))
    )

    test_user = User(
        user_id=1,
        username="test_user",
        email="user@test.com",
        privillege=0,
        password_hash=str(generate_password_hash("user1234"))
    )

    db.session.add(test_admin)
    db.session.add(test_user)

def signup(email, username, password, repeat, remember):
    if password != repeat:
        raise SignupError("Passwords do not match")
    
    #TODO: check if email is already in db
    if False:
        raise SignupError("Email already exists")

    #TODO: check if username is already in db
    if False:
        raise SignupError("Username already exists")
    
    #construct user object
    user = User(
        user_id = 0, #TODO: change this to an incrementing/random value later
        username = username,
        email = email,
        privillege = 0,
    )
    user.set_password(user, password)
    
    #TODO: add user to db

    login(username, password, remember)
    
def login(email_or_username, password, remember):
    #TODO: check that user exists in db (search by username and email)
    if False:
        raise LoginError("User does not exist")
    
    #TODO: check if the found users password hash matches
    if False:
        raise LoginError("Password is incorrect")
    
    login_user(remember=remember)
    