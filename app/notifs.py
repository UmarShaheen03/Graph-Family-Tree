from app.models import User, Notification
from app.databases import db
from datetime import datetime
from config import WEBSITE_URL
from threading import Thread
from time import sleep
import sys


def get_users_notifs(user): #check through notif db for all notifs with user id
    id = User.get_id(user)
    notifications = db.session.query(Notification).filter(Notification.user_id == id).all()
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
        print("Email Time: " + str(datetime.now().time())[:8])
        if(str(datetime.now().time())[:8] == "17:00:00"): #5pm
            send_emails(get_all_ids_with_daily())
            if (datetime.now().weekday() == 4): #friday
                send_emails(get_all_ids_with_weekly())

def send_emails():
    pass

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