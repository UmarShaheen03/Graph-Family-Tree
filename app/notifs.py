from app.models import User, Notification
from app.databases import db
from datetime import datetime



def get_users_notifs(user):
    id = User.get_id(user)
    #check through notif db for all notifs with user id

def mark_as_seen(notif_id):
    pass

def log_notif(text, users): #users is a list of ids to send the notif to
    new_id = db.session.query(Notification).order_by(Notification.id.desc()).first().id
    users.append(-1) #master log, send backup of all notifs to it

    for user_id in users:
        new_id += 1
        notif = Notification(
            id = new_id,
            for_user_id = user_id,
            text = text,
            time = datetime.now()
        )
        db.session.add(notif)
    db.commit()

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
    
        

#what is logged:
#   X account creation (viewable to admins, linked to user)
#   X logins (viewable to admins, linked to user)
#   X password resets (viewable to admins, linked to user)
#   - admin requests (viewable to admins, linked to user)
#   - tree requests (viewable to admins, linked to user)

#   - request acceptance (viewable to users, linked to user)
#   - tree edits (viewable to users, linked to tree)
#   ~ biography edits (viewable to users, linked to bio)
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