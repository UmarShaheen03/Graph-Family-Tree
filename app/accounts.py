from app.models import *
from flask_login import login_user
from app.databases import db
from werkzeug.security import generate_password_hash
from flask import current_app, url_for
from app.notifs import log_notif, get_all_admin_ids
import sys #TODO using for debug printing, remove in final
from config import WEBSITE_URL, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from jinja2 import Template
from neo4j import GraphDatabase

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

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def init_database():
    #create tables
    db.create_all()
    #clear any existing info (for testing TODO DO NOT KEEP IN FINAL)
    User.query.delete()
    Notification.query.delete()
    Tree.query.delete()

    #create mock accounts
    perma_admin = User(
        user_id=0,
        username="PermaAdmin",
        email="test@test.com", #TODO give a real email?
        verified=True,
        admin=True,
        create_time=datetime.now(),
        password_hash=str(generate_password_hash("CantResetM3"))
    )

    nima = User(
        user_id=1,
        username="Nima Dehdashti",
        email="nima519@gmail.com",
        verified=True,
        admin=True,
        create_time=datetime.now(),
        password_hash=str(generate_password_hash("CHANGEME"))
    )

    group31 = User(
        user_id=2,
        username="Group 31",
        email="cits3200group31@gmail.com",
        verified=True,
        admin=True,
        create_time=datetime.now(),
        password_hash=str(generate_password_hash("CHANGEME"))
    )

    test_user = User(
        user_id=3,
        username="user_test",
        email="user@test.com",
        verified=True,
        admin=False,
        create_time=datetime.now(),
        password_hash=str(generate_password_hash("test1234")),
        notifs_ignored=" Tree Create Tree Remove Tree Update Tree Delete Bio Edit Comments"
    )

    test_admin = User(
        user_id=4,
        username="admin_test",
        email="admin@test.com",
        verified=True,
        admin=True,
        create_time=datetime.now(),
        password_hash=str(generate_password_hash("test1234")),
        notifs_ignored=" Logout"
    )

    first_notif = Notification(
        id=0,
        user_id=-1,
        text="Databases initialised",
        time=datetime.now()
    )

    #get all tree names from the neo4j server
    with driver.session() as session:
        # Retrieve distinct labels
        result = session.run("MATCH (n) RETURN DISTINCT labels(n) AS labels")
        choices = [(label, label) for record in result for label in record["labels"]]
    
    for name in choices:
        tree = Tree(
            name=name[0],
            create_time=datetime.now(),
            users="0, 1, 3"
        )
        db.session.add(tree)


    #add mock accounts to db
    db.session.add(perma_admin)
    db.session.add(nima)
    db.session.add(group31)
    db.session.add(test_user)
    db.session.add(test_admin)
    #add first notification to db
    db.session.add(first_notif)
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


    #was getting error as type wasnt provided, currently filled with null will check with cooper
    log_notif(f"New account created for user {User.get_username(user)}",get_all_admin_ids(), "NULL") #notify all admins of new account
    login(username, password, remember)
    


def login(email_or_username, password, remember):
    user = db.session.query(User).filter((User.username == email_or_username) | (User.email == email_or_username)).first()

    if not user:
        raise LoginError("User does not exist")
    
    if not user.check_password(password):
        raise LoginError("Incorrect password")
    
    login_user(user, remember=remember)


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

    link = WEBSITE_URL + url_for("main_bp.reset_password_page") +"?token=" + str(token.hex) + "&user_id=" + str(user.user_id)

    message = MIMEMultipart("alternative")
    message["Subject"] = "Password Reset for " + user.username
    message["From"] = "Dehdashti Family Graph"
    message["To"] = receiver_email

    #html version of email
    #TODO: href works with real urls, doesn't with 127.0.0.1, change when deploying
    file = open("app/templates/email_reset.html", "r").read()
    html = Template(file).render(link=link)
    
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