from app.models import User
from flask_login import login_user
from app.databases import db
from werkzeug.security import generate_password_hash
from flask import current_app, url_for
from notifs import log_notif, get_all_admin_ids
import sys #TODO using for debug printing, remove in final

#libraries for reset password
import smtplib
import ssl
import uuid
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SignupError(Exception):
    pass

class LoginError(Exception):
    pass



def init_database():
    #create tables
    db.create_all()
    #clear any existing info (for testing TODO DO NOT KEEP IN FINAL)
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

    cooper = User( #TODO remove this, only using it to quickly test email 
        user_id=3,
        username="cooper",
        email="cooptrooper04@gmail.com",
        admin=True,
        password_hash=str(generate_password_hash("test"))
    )
  

    #add mock accounts to db
    db.session.add(nima)
    db.session.add(group31)
    db.session.add(test_user)
    db.session.add(cooper)
    db.session.commit()



def signup(email, username, password, repeat, remember):
    if password != repeat:
        raise SignupError("Passwords do not match")
    
    if db.session.query(User).filter(User.email == email).first() != None:
        raise SignupError("Email already exists")

    if db.session.query(User).filter(User.username == username).first() != None:
        raise SignupError("Username already exists")
    
    #get a new user_id, generated from a 128 bit uuid, sliced down to 32 bits
    while True:
        new_id = uuid.uuid4()
        new_id = int(str(new_id.int)[0:8]) #slicing to first 8 characters
        if db.session.query(User).filter(User.user_id == new_id).first() == None: #if user id is new
            break

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

    log_notif(f"New account created: {User.get_username(user)}", get_all_admin_ids()) #notify all admins of new account
    login(username, password, remember)
    


def login(email_or_username, password, remember):
    user = db.session.query(User).filter((User.username == email_or_username) | (User.email == email_or_username)).first()

    if not user:
        raise LoginError("User does not exist")
    
    if not user.check_password(password):
        raise LoginError("Incorrect password")
    
    login_user(user, remember=remember)
    log_notif(f"New login from: {User.get_username(user)}", get_all_admin_ids()) #notify all admins of succesful login



def reset_email(receiver_email):
    #smtp ssl info
    port = 465 #ssl port
    sender_email = "cits3200group31@gmail.com"
    password = "pzdm bcbj hjkv wewt" #TODO store password securely (environment variables?)
    context = ssl.create_default_context()

    user = db.session.query(User).filter(User.email == receiver_email).first()

    if user == None: #if invalid, needs to be indistinguishable from valid (for security reasons)
        #login to smtp, to make wait times similar
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(sender_email, password)
        return 
    
    #generate a random uuid for the reset password link
    token = uuid.uuid4()
    now = datetime.now()
    expiry = int(now.timestamp()) + (24 * 60 * 60) #now + 24 hours

    #commit changes to db
    db.session.query(User).filter(User.email == receiver_email).\
        update({"reset_token": token.hex}, synchronize_session = False)
    db.session.query(User).filter(User.email == receiver_email).\
        update({"reset_expiry": expiry}, synchronize_session = False)
    db.session.commit()

    website_url = "127.0.0.1:5000" #TODO replace with real url when deploying
    link = website_url + url_for("main_bp.reset_password_page") +"?token=" + str(token.hex) + "&user_id=" + str(user.user_id)

    message = MIMEMultipart("alternative")
    message["Subject"] = "Password Reset for " + user.username
    message["From"] = "Dehdashti Family Graph"
    message["To"] = receiver_email

    #html version of email
    #TODO: href works with real urls, doesn't with 127.0.0.1, change when deploying
    html = """\
    <!DOCTYPE html>
    <html lang = "en">

    <head>
        <style>
            body {
                font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", "Noto Sans", "Liberation Sans", Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
                min-height: 100vh;
            
                padding-top: 25px;
                padding-bottom: 25px;
                background-repeat: no-repeat;
            }

            h1 {
                color: #593196;
            }

            .contents {
                display: flex;
                justify-content: center;
                align-items: center;
                
            }

            .texts {
                box-shadow: rgba(100, 100, 111, 0.2) 0px 7px 29px 0px;
                border-radius: 1rem;
                padding-top: 2rem; 
                padding-right:4rem;
                padding-left: 4rem;
                padding-bottom: 2rem;
                background-color: white;
            }

            #btn {
                border: none;
                color: white;
                padding: 0.5rem 1rem;
                text-decoration: none;
                display: inline-block;

                margin-top: 1rem;
                margin-bottom: 2rem;
                cursor: pointer;
                background-color: #593196;

            }

            #btn:hover {
                background-color: #664993;
            }

            .subtext{
                font-size: x-small;
                color: grey;
            }
        </style>

    </head>

    <body>
        <div class="contents">
            <div class="texts">
                <h1>Forgot password?</h1>
                <p style="color:black">Click the link below to reset it.</p>
                <div id="button">
                    <a id='btn' href="%s">Click here</a>
                </div>
                <p>TEMPORARY LINK FOR DEVELOPMENT: %s</p>
                <p class="subtext">This link is only valid for 24 hours</p>
                <p class="subtext">If you did not make this request, simply ignore this email </p>
            </div>
        </div>
    </body>
    </html>
    """ % (link, link)
    

    #plaintext as backup if html doesn't load
    text = """\
    %s
    Click the above link to reset your password
    This link will last for 24 hours
    (If you did not make this request, simply ignore this email)
    """ % (link)

    plaintext_message = MIMEText(text, "plain")
    html_message = MIMEText(html, "html")

    #second message is attempted first, fallback to first message
    message.attach(plaintext_message)
    message.attach(html_message)

    #establish ssl conenction with gmail
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
    
    return



def verify_reset(user_id, token):
    if user_id == None or token == None: #if missing params
        return False
    
    user = db.session.query(User).filter(User.user_id == user_id).first()
    #print(token, file=sys.stderr)

    if user == None: #if no account with that email
        return False

    if user.reset_token != token: #if incorrect token
        return False

    if int(datetime.now().timestamp()) > user.reset_expiry: #if reset expired
        return False
    
    return True



def reset(user_id, password, repeat):
    if password != repeat:
        raise SignupError("Passwords do not match")
    
    user = db.session.query(User).filter(User.user_id == user_id).first()

    #set password to new password    
    user.set_password(password)

    #remove tokens, so they cant be reused
    db.session.query(User).filter(User.user_id == user_id).\
        update({"reset_token": None}, synchronize_session = False)
    db.session.query(User).filter(User.user_id == user_id).\
        update({"reset_expiry": None}, synchronize_session = False)
    db.session.commit()

    return