from models import User, Notification
from app.databases import db
from datetime import datetime



def get_users_notifs(user):
    id = User.get_id(user)
    #check through notif db for all notifs with user id

def mark_as_seen(notif_id):
    pass

def log_notif(text, users): #users is a list of ids to send the notif to
    new_id = db.session.query(Notification).order_by(Notification.id.desc()).first().id
    users.append(-1)

    for user_id in users:
        new_id += 1
        notif = Notification(
            id = new_id,
            for_user_id = user_id, #creating the master log notif
            text = text,
            time = datetime.now()
        )
        db.session.add(notif)
    db.commit()

def get_all_admin_ids():
    admin_ids = []
    results = db.session.query(User).filter(User.admin == True)
    for row in results:
        admin_ids.append(row)
    
        

#what to log:
#   - account creation (viewable to admins, linked to user)
#   - logins (viewable to admins, linked to user)
#   - admin requests (viewable to admins, linked to user)
#   - tree requests (viewable to admins, linked to user)

#   - request acceptance (viewable to users, linked to user)
#   - tree edits (viewable to users, linked to tree)
#   - biography edits (viewable to users, linked to bio)
#   - comments (viewable to users, linked to bio)

# options
#   - toggles for each type of notification
#   - toggles for how often to email (daily, weekly, monthly?, none)



#   - put all on the email? or just a few
#   - have how often be per type or overall
#   - unsubscribe link on email

#   - copy of each notification sent to every relevant user
#   - when seen, delete to save space
#   - have a master log table that never gets deleted