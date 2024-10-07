from app.models import User, Notification
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
import sys


def get_users_notifs(user): #check through notif db for all notifs with user id
    #TODO auto remove notifs user doesn't want to see
    id = User.get_id(user)
    notifications = db.session.query(Notification).filter(Notification.user_id == id).order_by(desc(Notification.time)).all()
    return notifications

def log_notif(text, users, goto = None): #users is a list of ids to send the notif to
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
            goto = goto
        )
        db.session.add(notif)
    db.session.commit()

def check_for_emails(): #threaded task, runs every second
    while True:
        sleep(1)
        #print("Email Time: " + str(datetime.now().time())[:8])
        if(str(datetime.now().time())[:8] == "17:00:00"): #5pm
            send_emails(get_all_ids_with_daily())
            if (datetime.now().weekday() == 4): #friday
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
        notif_amount = len(notifications)
        if (notif_amount > 10):
            notifications = notifications[:10] #slice to just first 10 notifications

        message = MIMEMultipart("alternative")
        message["Subject"] = "Notifications from Dehdashti Family Graph for " + user.username
        message["From"] = "Dehdashti Family Graph"
        message["To"] = receiver_email

        #html version of email
        #TODO: href works with real urls, doesn't with 127.0.0.1, change when deploying
        html = ""
        

        #plaintext as backup if html doesn't load
        text = ""

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
        string.append(" Login")
    if (request.form.get("logout")):
        string.append(" Logout")
    if (request.form.get("reset")):
        string.append(" Reset")
    if (request.form.get("signup")):
        string.append(" Signup")

    if (request.form.get("admin_req")):
        string.append(" Admin Req")
    if (request.form.get("tree_req")):
        string.append(" Tree Req")
    if (request.form.get("req_accepted")):
        string.append(" Request")

    if (request.form.get("comment")):
        string.append(" Comment")
    if (request.form.get("bio_edit")):
        string.append(" Bio Edit")

    if (request.form.get("tree_create")):
        string.append(" Tree Create")
    if (request.form.get("tree_move")):
        string.append(" Tree Move")
    if (request.form.get("tree_update")):
        string.append(" Tree Delete")
    if (request.form.get("tree_delete")):
        string.append(" Tree Delete")
    
    return string

def get_all_admin_ids(): #returns list of all admin users' ids
    admin_ids = []
    results = db.session.query(User).filter(User.admin == True).all()
    for user in results:
        admin_ids.append(User.get_id(user))
    return admin_ids

def get_all_ids_with_tree(id): #returns list of all users with access to this tree
    ids = []
    #TODO once multi tree support is done
    results = []
    for user in results:
        ids.append(User.get_id(user))
    return ids

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
# waiting on requests to be done:
#   - admin requests (viewable to admins, linked to user)
#   - tree requests (viewable to admins, linked to user)
#   - request acceptance (viewable to users, linked to user)
# waiting on multi tree support to be done:
#   ~ tree edits [CRUD] (viewable to users, linked to tree)
#   ~ biography edits (viewable to users, linked to tree)
#   ~ comments (viewable to users, linked to tree)

# options
#   - toggles for each type of notification
#   - toggles for how often to email (daily, weekly, monthly?, none)



#   - put 10 most recent on email
#   - unsubscribe link on email

#   - copy of each notification sent to every relevant user
#   - when seen, delete to save space
#   - have a master log table that never gets deleted