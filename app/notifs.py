from app.models import User, Notification, Tree
from app.databases import db
from datetime import datetime
from config import WEBSITE_URL
from threading import Thread
from time import sleep
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import desc
from jinja2 import Template, Environment, BaseLoader, FileSystemLoader
from flask import url_for
import sys

def get_users_notifs(user): #check through notif db for all notifs with user id
    if user == -1: #master log
        id = -1
        ignored = ""
    elif not user.is_authenticated: #no user
        return []
    else: #normal user
        id = User.get_id(user)
        ignored = User.get_ignored(user)

    notifications = db.session.query(Notification).filter(Notification.user_id == id).order_by(desc(Notification.time)).all()

    #clear any ignored notifs automatically
    for notif in notifications:
        if notif.type != None:
            if notif.type in ignored:
                db.session.query(Notification).filter(Notification.id == notif.id).filter(Notification.user_id == id).delete()
                notifications.remove(notif)
        
    db.session.commit()
    return notifications

def log_notif(text, users, type, goto = None): #users is a list of ids to send the notif to
    new_id = db.session.query(Notification).order_by(Notification.id.desc()).first().id
    users.append(-1) #master log, send backup of all notifs to it

    if (goto != None):
        goto = WEBSITE_URL + goto

    for user_id in users:
        new_id += 1

        notif = Notification(
            id = new_id,
            user_id = user_id,
            text = text,
            time = datetime.now(),
            type = type,
            goto = goto
        )
        db.session.add(notif)
    db.session.commit()

def check_for_emails(): #threaded task, runs every second
    while True:
        sleep(1)
        #print("Email Time: " + str(datetime.now().time())[:8])
        if(str(datetime.now().time())[:8] == "17:00:00"): #5pm
            print("sending daily emails!")
            send_emails(get_all_ids_with_daily())
            if (datetime.now().weekday() == 4): #friday
                print("sending weekly emails too!")
                send_emails(get_all_ids_with_weekly())

def send_emails(ids):
    for id in ids:
        user = db.session.query(User).filter(User.user_id == id).first()

        #smtp ssl info
        port = 465 #ssl port
        sender_email = "cits3200group31@gmail.com"
        receiver_email = User.get_email(user)
        password = "pzdm bcbj hjkv wewt" #TODO store password securely (environment variables?)
        context = ssl.create_default_context()

        notifications = get_users_notifs(user)

        if (notifications == None):
            continue #skip if no notifs for this user

        notif_amount = len(notifications)
        if (notif_amount > 10):
            notifications = notifications[:10] #slice to just first 10 notifications
        

        message = MIMEMultipart("alternative")
        message["Subject"] = "Notifications from Dehdashti Family Graph for " + user.username
        message["From"] = "Dehdashti Family Graph"
        message["To"] = receiver_email

        home_url = WEBSITE_URL + url_for("main_bp.home_page")
        unsub_url = WEBSITE_URL + url_for("main_bp.unsubscribe", user_id=id)
        account_url = WEBSITE_URL + url_for("main_bp.unsubscribe", user_id=id) #TODO set this to accounts once done

        #html version of email
        #TODO: href works with real urls, doesn't with 127.0.0.1, change when deploying
        file = open("app/templates/email_notif.html", "r").read()
        loader = FileSystemLoader(searchpath="./")
        template = Environment(loader=loader).from_string(file)
        html = template.render(notifications=notifications, 
                               home_url=home_url, 
                               unsub_url=unsub_url, 
                               account_url=account_url, 
                               notif_amount=notif_amount,
                               now=str(datetime.utcnow))
                                     
        #plaintext as backup if html doesn't load
        text = """\
        Notifications\n
        Here are the most recent notifications from Dehdashti Family Graph\n
        %s\n
        """ % (home_url)

        for notif in notifications:
            if notif.goto != None:
                text += str(notif.time) + " " + notif.goto + "\n" + notif.text + "\n"
            else:
                text += str(notif.time) + "\n" + notif.text + "\n"

        if (notif_amount > 10):
            text += "and " + str(notif_amount-10) + " more...\n"

        text += """\
        To unsubscribe from all emails, visit: %s\n
        Or to edit your email preferences, visit: %s\n
        """ % (unsub_url, account_url)

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
    
def create_notifs_string(request):
    string = ""

    if (request.form.get("login")):
        string += (" Login")
    if (request.form.get("logout")):
        string += (" Logout")
    if (request.form.get("reset")):
        string += (" Reset")
    if (request.form.get("signup")):
        string += (" Signup")

    if (request.form.get("user_req")):
        string += (" User Req")
    if (request.form.get("admin_req")):
        string += (" Admin Req")
    if (request.form.get("tree_req")):
        string += (" Tree Req")
    if (request.form.get("req_accepted")):
        string += (" Request")

    if (request.form.get("comment")):
        string += (" Comment")
    if (request.form.get("bio_edit")):
        string += (" Bio Edit")

    if (request.form.get("new_tree")):
        string += (" New Tree")
    if (request.form.get("tree_create")):
        string += (" Tree Create")
    if (request.form.get("tree_move")):
        string += (" Tree Move")
    if (request.form.get("tree_update")):
        string += (" Tree Delete")
    if (request.form.get("tree_delete")):
        string += (" Tree Delete")
    
    return string

def get_all_admin_ids(): #returns list of all admin users' ids
    admin_ids = []
    results = db.session.query(User).filter(User.admin == True).all()
    for user in results:
        admin_ids.append(User.get_id(user))
    return admin_ids

def get_all_ids(): #returns list of all user ids
    ids = []
    results = db.session.query(User).all()
    for user in results:
        ids.append(User.get_id(user))
    return ids

def get_all_ids_with_tree(name): #returns list of all users with access to this tree
    ids = []
    results = db.session.query(Tree).filter(Tree.name == name).all()
    for id in results.split(", "):
        ids.append(int(id))
    return ids

def get_all_trees_with_id(id):
    result = []
    trees = db.session.query(Tree).all()
    for tree in trees:
        if str(id) in tree.users:
            result.append(tree)
    return result

def get_all_ids_with_daily():
    ids = []
    results = db.session.query(User).filter(User.email_preference == "Daily").all()
    for user in results:
        ids.append(User.get_id(user))
    return ids

def get_all_ids_with_weekly():
    ids = []
    results = db.session.query(User).filter(User.email_preference == "Weekly").all()
    for user in results:
        ids.append(User.get_id(user))
    return ids


        

#what is logged:
#   X website starting (only master log)
#   X account creation (viewable to admins, linked to user)
#   X logins (viewable to admins, linked to user)
#   X password resets (viewable to admins, linked to user)
#   X logouts (viewable to admins, linked to user)
#   - user requests
#   X admin requests (viewable to admins, linked to user)
#   X tree requests (viewable to admins, linked to user)
#   - request acceptance (viewable to users, linked to user)
#   X tree edits [CRUD] (viewable to users, linked to tree)
#   X new tree creation
#   ~ bio edits
#   ~ comments

#TODO
# - ensure all request/tree notifs are working
# - change redirects for ux
# - add errors to more pages
# - user requests (start unverified)
# - request accepted notification
#   
# - testing
# - documentation