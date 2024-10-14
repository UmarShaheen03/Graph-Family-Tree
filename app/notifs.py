from app.models import User, Notification, Tree
from app.databases import db
from datetime import datetime
from config import WEBSITE_URL
from time import sleep
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import desc
from jinja2 import Environment, FileSystemLoader
from app import create_app

#returns all the notifs related to this user id
#filters out ignored notifs, marks them as seen automatically
def get_users_notifs(user):
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

#sends a notification to all users in users
#sends a backup copy to user -1 (the master log)
#goto link can be None
def log_notif(text, users, type, goto = None): 
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

#ran in a seperate thread, once every second
#checks for 5pm and friday, and sends daily/weekly emails
def check_for_emails():
    app = create_app()
    while True:
        sleep(1)
        print("Email Time: " + str(datetime.now().time())[:8])
        if(str(datetime.now().time())[:8] == "17:00:00"): #5pm
            print("sending daily emails!")
            
            ids = []
            with app.app_context():
                results = User.query.filter(User.email_preference == "Daily").all()
            for user in results:
                ids.append(User.get_id(user))

            print("to..." + str(ids))
            send_emails(ids)
            if (datetime.now().weekday() == 4): #friday
                print("sending weekly emails too!")

                ids = []
                with app.app_context():
                    results = User.query.filter(User.email_preference == "Weekly").all()
                for user in results:
                    ids.append(User.get_id(user))
                
                print("to..." + str(ids))
                send_emails(ids)

#sends the notification email to all users in the id list
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
        account_url = WEBSITE_URL + url_for("main_bp.my_dashboard")

        #html version of email
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

#takes the ignore notifs forms output and formats it into a string
#e.g. " Tree Create Tree Move Tree Update Tree Delete Bio Edit Comments"
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
        string += (" User Request")
    if (request.form.get("admin_req")):
        string += (" Admin Request")
    if (request.form.get("tree_req")):
        string += (" Tree Request")
    if (request.form.get("req_accepted")):
        string += (" Request Accept")

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

"""GET ID FUNCTIONS"""
#these all return a list of user ids, filtered by some property, for use with log_notifs

#returns all admins
def get_all_admin_ids(): 
    admin_ids = []
    results = db.session.query(User).filter(User.admin == True).all()
    for user in results:
        admin_ids.append(User.get_id(user))
    return admin_ids

#returns all users (verified and unverified), used for logs
def get_all_ids():
    ids = []
    results = db.session.query(User).all()
    for user in results:
        ids.append(User.get_id(user))
    return ids

#returns all users with access to the tree <name>
def get_all_ids_with_tree(name):
    ids = []
    tree = db.session.query(Tree).filter(Tree.name == name).first()

    if tree == None:
        return []
    
    for user in tree.users.split(", "):
        ids.append(int(user))
    return ids

#returns all trees accessible to user <id>
def get_all_trees_with_id(id):
    result = []
    trees = db.session.query(Tree).all()
    for tree in trees:
        if str(id) in tree.users:
            result.append(tree)
    return result