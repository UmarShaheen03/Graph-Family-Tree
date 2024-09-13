from app.models import User
from flask_login import login_user
from app.databases import db
from werkzeug.security import generate_password_hash
from flask import current_app, url_for

#libraries for rest password
import smtplib
import ssl
import uuid
import datetime

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
    nima = User(
        user_id=0,
        username="Nima Dehdashti",
        email="nima519@gmail.com",
        admin=True,
        password_hash=str(generate_password_hash("CHANGEME"))
    )

    group31 = User(
        user_id=1,
        username="Group 31",
        email="cits3200group31@gmail.com",
        admin=True,
        password_hash=str(generate_password_hash("CHANGEME"))
    )

    test_user = User(
        user_id=2,
        username="user_test",
        email="user@test.com",
        admin=False,
        password_hash=str(generate_password_hash("test1234"))
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
        admin = False
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



def reset_email(receiver_email):
    user = db.session.query(User).filter(User.email == receiver_email).first()

    if user == None:
        return #return without error if no matching user, vulnerable if it reports when user does/doesn't exist
    
    #generate a random uuid for the reset password link
    token = uuid.uuid4() 

    #add reset token to user in db, expire after 24 hours
    user.reset_token = token
    now = datetime.now()
    user.reset_expiry = now.timestamp + (24 * 60 * 60) #now + 24 hours


    link = url_for("main_bp.reset_page") +"?token=" + token + "&email=" + user.email

    port = 465 #ssl port
    sender_email = "cits3200group31@gmail.com"
    password = "MichaelWise#1Fans" #TODO store password securely
    context = ssl.create_default_context()

    #create message content
    message = """\
    From: %s
    To: %s
    Subject: WEBSITE NAME: Password reset request for %s

    To reset your password, please visit %s
    This link expires after 24 hours.
    (If you did not request a password reset, simply ignore this message)
    
    """ % (sender_email, receiver_email, user.username, link)

    #establish ssl conenction with gmail
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
    
    return



def verify_reset(email, token):
    if email == None or token == None: #if missing params
        return False
    
    user = db.session.query(User).filter(User.email == email).first()

    if user == None: #if no account with that email
        return False

    if user.reset_token != token: #if incorrect token
        return False

    if datetime.now() > user.reset_expire: #if reset expired
        return False
    
    return True



def reset(email, password, repeat):
    if password != repeat:
        raise SignupError("Passwords do not match")
    
    user = db.session.query(User).filter(User.email == email).first()
    
    user.set_password(password)
    
    return