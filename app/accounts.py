from models import User
from flask_login import login_user

class SignupError(Exception):
    pass

class LoginError(Exception):
    pass


def signup(email, username, password, repeat, remember):
    if password != repeat:
        raise SignupError("Passwords do not match")
    
    if len(password) < 8:
        raise SignupError("Password is less than 8 characters")

    if not any(char.isdigit() for char in password):
        raise SignupError("Password requires at least 1 number")
    
    if not any(char.isupper() for char in password):
        raise SignupError("Password requires at least 1 capital letter")
    
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
        raise LoginError()
    
    #TODO: check if the found users password hash matches
    if False:
        raise LoginError()
    
    login_user(remember=remember)
    