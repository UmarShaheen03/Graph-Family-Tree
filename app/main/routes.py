"""Main route views"""

import os
import io
from flask import Blueprint, Flask, render_template, flash, redirect, url_for, request, session, send_file
from app.forms import *
from app.models import Biography, Comment, User
from app.accounts import *
from app.notifs import *
from app import db
from neo4j import GraphDatabase
from flask_wtf import CSRFProtect
from datetime import datetime
from flask_login import login_required, current_user, logout_user

main_bp = Blueprint('main_bp', __name__)

#test function, resets database and adds two mock users
@main_bp.before_request
def run_once_on_start():
    init_database()
    email_thread = Thread(target=check_for_emails)
    email_thread.start() #TODO may be leaking?
    print("created email thread")
    #replaces code of this function with none, so it only runs once
    run_once_on_start.__code__ = (lambda:None).__code__

@main_bp.route("/")
def home_page():
    """The landing page"""
    if current_user.is_authenticated:
        return render_template('home.html', 
                               notifications=get_users_notifs(current_user), 
                               logged_in_as=User.get_username(current_user))
    else:
        return render_template('home.html')

"""LOGIN AND SIGNUP PAGE/FORMS"""

@main_bp.route("/login")
def login_page():
    logoutForm = LogoutForm()
    loginForm = LoginForm()

    if current_user.is_authenticated:
        return render_template("login.html", loginForm=loginForm, logoutForm=logoutForm,
                               notifications=get_users_notifs(current_user), 
                               logged_in_as=User.get_username(current_user))
    else:
        return render_template("login.html", loginForm=loginForm, logoutForm=logoutForm)

@main_bp.route("/signup")
def signup_page():
    signupForm = SignupForm()

    if current_user.is_authenticated:
        return render_template("signup.html", signupForm=signupForm,
                               notifications=get_users_notifs(current_user), 
                               logged_in_as=User.get_username(current_user))
    else:
        return render_template("signup.html", signupForm=signupForm)
    

#form submissions for login
@main_bp.route("/login-form", methods=["POST"])
def login_request():
    form = LoginForm()
    logoutForm = LogoutForm()

    if form.validate_on_submit():
        username_or_email = request.form.get("username_or_email")
        password = request.form.get("password")
        remember = request.form.get("remember")

        try:
            login(username_or_email, password, remember)
        except LoginError as error:
            return render_template("login.html", loginForm=form, logoutForm=logoutForm, error=error)

        #send to home page on success TODO change to account page?
        return redirect(url_for("main_bp.home_page"))
    
    else:
        return render_template("login.html", loginForm=form, logoutForm=logoutForm, error="Invalid Form")

#form submissions for logout
@main_bp.route("/logout-form", methods=["POST"])
def logout_request():
    log_notif(f"User {User.get_username(current_user)} just logged out", get_all_admin_ids(), " Logout") #notify all admins of logout
    logout_user()
    return redirect(url_for("main_bp.home_page"))
    
#form submissions for signup
@main_bp.route("/signup-form", methods=["POST"])
def signup_request():
    form = SignupForm()

    if form.validate_on_submit():
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        repeat = request.form.get("repeat")
        remember = request.form.get("remember")

        try:
            signup(email, username, password, repeat, remember)
        except SignupError as error:
            if current_user.is_authenticated:
                return render_template("signup.html", signupForm=form, error=error,
                               notifications=get_users_notifs(current_user), 
                               logged_in_as=User.get_username(current_user))
            else:
                return render_template("signup.html", signupForm=form, error=error)


        #send to home page on success
        return redirect(url_for("main_bp.home_page"))
    
    else:
        if current_user.is_authenticated:
            return render_template("signup.html", loginForm=form, error="Invalid Form",
                    notifications=get_users_notifs(current_user), 
                    logged_in_as=User.get_username(current_user))
        else:
            return render_template("signup.html", loginForm=form, error="Invalid Form")
   

@main_bp.route("/forgot")
def forgot_password_page():
    form = ForgotPassword()

    if current_user.is_authenticated:
        return render_template("forgot.html", forgotForm=form, submitted=False,
                               notifications=get_users_notifs(current_user), 
                               logged_in_as=User.get_username(current_user))
    else:
        return render_template("forgot.html", forgotForm=form, submitted=False)

@main_bp.route("/forgot-form", methods=["POST"])
def forgot_request():
    form = ForgotPassword()
    email = request.form.get("email")
    reset_email(email)

    if current_user.is_authenticated:
        return render_template("forgot.html", forgotForm=form, submitted=True,
                               notifications=get_users_notifs(current_user), 
                               logged_in_as=User.get_username(current_user))
    else:
        return render_template("forgot.html", forgotForm=form, submitted=True)

@main_bp.route("/reset")
def reset_password_page():
    #get user_id and token from url params
    user_id = request.args.get("user_id")
    token = request.args.get("token")

    if not verify_reset(user_id, token):
        return redirect(url_for("main_bp.home_page"))
    
    form = ResetPassword()
    if current_user.is_authenticated:
        return render_template("reset.html", resetForm=form, token=token, user_id=user_id,
                               notifications=get_users_notifs(current_user), 
                               logged_in_as=User.get_username(current_user))
    else:
        return render_template("reset.html", resetForm=form, token=token, user_id=user_id)

@main_bp.route("/reset-form", methods=["POST"])
def reset_form():
    #get user_id and token from url params
    user_id = request.args.get("user_id")
    token = request.args.get("token")

    if not verify_reset(user_id, token):
        return redirect(url_for("main_bp.home_page"))
    
    form = ResetPassword()
    password = request.form.get("password")
    repeat = request.form.get("repeat")

    try:
        reset(user_id, password, repeat)
    except SignupError as error:
        if current_user.is_authenticated:
            return render_template("reset.html", resetForm=form, error=error, token=token, user_id=user_id,
                    notifications=get_users_notifs(current_user), 
                    logged_in_as=User.get_username(current_user))
        else:
            return render_template("reset.html", resetForm=form, error=error, token=token, user_id=user_id)


    user = db.session.query(User).filter(User.user_id == user_id).first()
    ids = get_all_admin_ids()
    if user_id not in ids: #if resetter is a user
        ids.append(user_id)
    log_notif(f"User {User.get_username(user)} just reset their password", ids, " Reset") #notify all admins (and user) of password reset

    loginForm = LoginForm()
    logoutForm = LogoutForm()

    if current_user.is_authenticated: #if they're already logged in, send them to home
        return redirect(url_for("main_bp.home_page"))   
    else: #otherwise, send user back to login when finished
        return render_template("login.html", loginForm=loginForm, logoutForm=logoutForm, info="Password reset succesfully, please login") 


@main_bp.route('/biography/edit', methods=['GET', 'POST'])
def edit_biography():
    check = check_login_admin()
    if check != None:
        return check
        
    
    biography = Biography.query.first()
    edit_form = BiographyEditForm()

    # Fetch nodes (FullName) for the select box for the form 
    with driver.session() as session:
        result = session.run("MATCH (n:Person) RETURN n.FullName AS name")
        nodes = [(record["name"], record["name"]) for record in result]
        
    # Set choices for the FullName dropdown field
    edit_form.fullname.choices = nodes

    # Check if the form is submitted and validated
    if edit_form.validate_on_submit():
        person_name = edit_form.fullname.data
        
        # Update the person's information in the Neo4j graph database
        with driver.session() as session:
            session.run(
                """
                MATCH (p:Person {FullName: $full_name})
                SET p.Date_Of_Birth = $DOB,
                    p.Biography = $Biography,
                    p.Location = $Location,
                    p.Email = $Email,
                    p.PhoneNumber = $PhoneNumber,
                    p.Address = $Address
                """,
                full_name=person_name,
                DOB=edit_form.dob.data,
                Biography=edit_form.biography.data,
                Location=edit_form.location.data,
                Email=edit_form.email.data,
                PhoneNumber=edit_form.phonenumber.data,
                Address=edit_form.address.data
            )
        
        flash(f'Biography for {person_name} has been updated successfully.')
        log_notif(f"User {User.get_username(current_user)} just edited the bio of {person_name} from family TODO", 
                  get_all_admin_ids() + get_all_ids_with_tree("TODO"), " Bio Edit", "/biography/" + person_name) #notify all admins/users with access about bio edit
        
        return redirect(url_for('main_bp.biography', name=person_name,
                                notifications=get_users_notifs(current_user), 
                                logged_in_as=User.get_username(current_user)))

    return render_template('edit_biography.html', biography=biography, edit_form=edit_form,
                           notifications=get_users_notifs(current_user), 
                           logged_in_as=User.get_username(current_user))
    
    

#NOTIFICATION ROUTES
@main_bp.route("/unsubscribe/<user_id>", methods=['GET', 'POST'])
def unsubscribe(user_id):
    loginForm = LoginForm()
    logoutForm = LogoutForm()

    if not current_user.is_authenticated: #if not logged in
        return render_template("login.html", loginForm=loginForm, logoutForm=logoutForm, info="Please login to your account to unsubscribe")
    elif (int(user_id) != User.get_id(current_user)): #if logged in as a different user
        return render_template("login.html", loginForm=loginForm, logoutForm=logoutForm, info="Please login to your account to unsubscribe",
                                notifications=get_users_notifs(current_user), 
                                logged_in_as=User.get_username(current_user))

    user = db.session.query(User).filter(User.user_id == User.get_id(current_user)).first()
    user.set_often("None")
    db.session.commit()

    return render_template("unsubscribe.html", email=User.get_email(current_user),
                           notifications=get_users_notifs(current_user), 
                           logged_in_as=User.get_username(current_user))

@main_bp.route("/mark_as_seen/<notif_id>", methods=['POST'])
def seen_notif(notif_id):
    notif = db.session.query(Notification).filter(Notification.id == notif_id).first()
    if notif == None:
        return redirect(url_for("main_bp.home_page"))
    if notif.user_id != User.get_id(current_user): #failsafe so cant delete other users notifs
        return redirect(url_for("main_bp.home_page"))
    db.session.query(Notification).filter(Notification.id == notif_id).delete()
    db.session.commit()
    return redirect(url_for("main_bp.home_page"))

@main_bp.route("/preference_form", methods=['POST'])
def update_preferences():
    check = check_login()
    if check != None:
        return check
    
    user = db.session.query(User).filter(User.user_id == User.get_id(current_user)).first()
    user.set_ignored(create_notifs_string(request))
    db.session.commit()

    return redirect(url_for("main_bp.my_dashboard"))

@main_bp.route("/often_form", methods=['POST'])
def update_often():
    check = check_login()
    if check != None:
        return check
    
    user = db.session.query(User).filter(User.user_id == User.get_id(current_user)).first()
    user.set_often(request.form.get("preference"))
    db.session.commit()

    return redirect(url_for("main_bp.my_dashboard"))
    



#functions for checking if the current user is logged in, and if they are an admin
def check_login():
    if not current_user.is_authenticated:
        form = LoginForm()
        logoutForm  = LogoutForm()
        return render_template("login.html", loginForm=form, logoutForm=logoutForm, info="Please login or create an account to view this page")
    
    else:
        return None
    
def check_login_admin():
    check = check_login()
    if check != None:
        return check
    
    if not User.is_admin(current_user): #if user is not an admin
        form = LoginForm()
        logoutForm = LogoutForm()
        return render_template("login.html", loginForm=form, logoutForm=logoutForm, info="Admin permissions are required to view this page", logged_in_as=User.get_username(current_user))
        #TODO: make this return requests page, so user can request to become admin
    
    else:
        return None
    

@main_bp.route('/my_dashboard', methods=['GET', 'POST'])
def my_dashboard():
    check = check_login()
    if check is not None:
        return check 
    
    check2 = check_login_admin()
    if check2 is None:
        admin = True
    else:
        admin = False
    
    form1 = EmailPreference()
    form2 = IgnoreNotifs()
    return render_template('my_dashboard.html', preferenceForm=form1, ignoreForm=form2, 
                           preferences=User.get_ignored(current_user),
                           often=User.get_often(current_user),
                           admin=admin, #boolean for if admin or not #TODO make more secure?
                           notifications=get_users_notifs(current_user), 
                           logged_in_as=User.get_username(current_user)) 

@main_bp.route("/log")
def log():
    check = check_login_admin()
    if check != None:
        return check
    
    users = db.session.query(User).all()
    #TODO add trees
    
    return render_template("log.html",
                           users=users,
                           master_notifications=get_users_notifs(-1),
                           notifications=get_users_notifs(current_user), 
                           logged_in_as=User.get_username(current_user))

    
# Function to fetch biography from Neo4j
def get_person_bio(full_name):
    query = """
    MATCH (p:Person {FullName: $full_name})
    RETURN p.FullName AS name, 
           p.Hierarchy AS hierarchy, 
           p.Date_Of_Birth AS dob, 
           p.Biography AS biography, 
           p.Location AS location, 
           p.Email AS email, 
           p.PhoneNumber AS phone_number, 
           p.Address AS address
    """
    with driver.session() as session:
        result = session.run(query, full_name=full_name)
        return result.single()

NEO4J_URI='neo4j+ssc://633149e1.databases.neo4j.io'
NEO4J_USERNAME='neo4j'
NEO4J_PASSWORD='1b_L2Kp4ziyuxubevqHTgHDGxZ1VjYXROCFF2USqdNE'


# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def fetch_data():
    # Query all nodes, including their Lineage property
    node_query = """
        MATCH (p:Person)
        RETURN p.FullName AS name, p.Hierarchy AS hierarchy, p.Lineage AS lineage
    """

    # Query all relationships
    relationship_query = """
        MATCH (p:Person)-[r:PARENT_OF]->(c:Person)
        RETURN p.FullName AS parent, c.FullName AS child
    """

    nodes = []
    links = []

    # Fetch all nodes
    with driver.session() as session:
        node_result = session.run(node_query)
        for record in node_result:
            name = record["name"]
            hierarchy = record["hierarchy"]
            lineage = record["lineage"]  # Fetch the lineage property

            # Add node if not already in the list (to avoid duplicates)
            if not any(node['name'] == name for node in nodes):
                nodes.append({'name': name, 'hierarchy': hierarchy, 'lineage': lineage})

    # Fetch all relationships
    with driver.session() as session:
        relationship_result = session.run(relationship_query)
        for record in relationship_result:
            parent_name = record["parent"]
            child_name = record["child"]

            # Add link from parent to child
            links.append({'source': parent_name, 'target': child_name})

    return nodes, links

def calculate_age(date_of_birth_str):
    # Assuming date_of_birth_str is in the format 'YYYY-MM-DD'
    date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d')
    today = datetime.today()
    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    if age is not None:
            print(f"Calculated Age: {age}",date_of_birth_str)
    return age

@main_bp.route("/modify_graph", methods=['GET', 'POST'])
def modify_graph():
    """The Add node page"""
    check = check_login_admin()
    if check != None:
        return check
    
    form = AddNodeForm()
    
    # Fetch nodes for the select box for form 
    with driver.session() as session:
        result = session.run("MATCH (n:Person) RETURN n.FullName AS name")
        nodes = [(record["name"], record["name"]) for record in result]
        
    form.parent.choices = nodes
    form.new_parent.choices = nodes
    form.person_to_delete.choices = nodes
    form.person_to_shift.choices = nodes
    form.old_name.choices = nodes

    if form.validate_on_submit():
        if form.action.data == "add":
            with driver.session() as session:
                # Retrieve the parent's hierarchy
                parent_hierarchy_query = """
                MATCH (p:Person {FullName: $Parent})
                RETURN p.Hierarchy AS parent_hierarchy
                """
                parent_result = session.run(
                    parent_hierarchy_query, Parent=form.parent.data
                )
                
                parent_hierarchy = parent_result.single()["parent_hierarchy"]

                # Add new node with hierarchy as parent's hierarchy + 1
                session.run(
                    """
                    CREATE (n:Person {FullName: $full_name, Hierarchy: $new_hierarchy})
                    """,
                    full_name=form.name.data,
                    new_hierarchy=parent_hierarchy + 1  # Child's hierarchy is parent's + 1
                )

                # Build the dynamic query string to add a relationship
                query = """
                MATCH (a:Person {FullName: $Parent}), (b:Person {FullName: $full_name})
                MERGE (a)-[r:PARENT_OF]->(b)
                """

                # Create or update relationship
                session.run(
                    query,
                    full_name=form.name.data,
                    Parent=form.parent.data
                )

            print("Data processed. Redirecting to index.")
            return redirect(url_for("main_bp.tree_page"))
        else:
            print("Selected action is not 'Add Person'.")
    else:
        # Add debugging output
        print("Form validation failed.")
        print(form.errors)  # Print form validation errors if any

    
    
    if form.action.data == "edit":
            with driver.session() as session:
                # Add node
                session.run(
                    """
                   MATCH (n:Person {FullName: $old_name})
                   SET n.FullName = $new_name
                   """,
    old_name=form.old_name.data,
    new_name=form.new_name.data
                )
            return redirect(url_for("main_bp.tree_page"))
    

    if form.action.data == "delete":
        with driver.session() as session:
        # Delete person logic
           session.run(
            """
            MATCH (n:Person {FullName: $person_to_delete})
            DETACH DELETE n
            """,
            person_to_delete=form.person_to_delete.data
        )
        return redirect(url_for("main_bp.tree_page"))
    
    if form.action.data == "shift":
        with driver.session() as session:
        # Retrieve the new parent's hierarchy
            parent_hierarchy_query = """
        MATCH (p:Person {FullName: $Parent})
        RETURN p.Hierarchy AS parent_hierarchy
        """
            parent_result = session.run(parent_hierarchy_query, Parent=form.new_parent.data)
            parent_hierarchy = parent_result.single()["parent_hierarchy"]

        # Update the hierarchy of the person being shifted
            update_hierarchy_query = """
            MATCH (b:Person {FullName: $full_name})
            SET b.Hierarchy = $new_hierarchy
            """
            session.run(
            update_hierarchy_query,
            full_name=form.person_to_shift.data,
            new_hierarchy=parent_hierarchy + 1  # New hierarchy is parent's hierarchy + 1
        )

        # Create or update the relationship between the new parent and the person being shifted
            update_relationship_query = """
        MATCH (a:Person {FullName: $Parent}), (b:Person {FullName: $full_name})
        MERGE (a)-[r:PARENT_OF]->(b)
        """
            session.run(
                update_relationship_query,
                full_name=form.person_to_shift.data,
                Parent=form.new_parent.data
        )

            print("Person shifted and hierarchy updated. Redirecting to index.")
            return redirect(url_for("main_bp.tree_page"))
    return render_template('modify_graph.html', form=form)

#functions for checking if the user is logged in, and if they are an admin
def check_login():
    if not current_user.is_authenticated:
        form = LoginForm()
        logoutForm = LogoutForm()
        return render_template("login.html", loginForm=form, logoutForm=logoutForm, info="Please login or create an account to view this page")
    
    else:
        return None
    
def check_login_admin():
    check = check_login()
    if check != None:
        return check
    
    if not User.is_admin(current_user): #if user is not an admin
        form = LoginForm()
        logoutForm = LogoutForm()
        return render_template("login.html", loginForm=form, logoutForm=logoutForm, info="Admin permissions are required to view this page", logged_in_as=User.get_username(current_user))
        #TODO: make this return requests page, so user can request to become admin
    
    else:
        return None

@main_bp.route("/create_tree", methods=['GET', 'POST'])
def create_tree():
    form = submit_File()
    error_message = None  # Initialize an error message variable
    if form.validate_on_submit():
        file = form.file.data
        name = form.name.data
        if file:
            # Check if the file is a CSV
            if not file.filename.endswith('.csv'):
                error_message = 'Invalid file format. Please upload a CSV file.'
                return render_template("create_tree.html", form=form, error_message=error_message)

            file_data = file.read().decode('utf-8')
            DATA = []
            Nodes = ""
            Relationships = ""

            for row in file_data.splitlines():
                List_Of_Families = row.strip().split(",")
                DATA.append(List_Of_Families)

            # First, ensure all nodes are created and merged (without relationships)
            for row_index, Family_lines in enumerate(DATA):
                for column_index, people in enumerate(Family_lines):
                    if people.strip():
                        hierarchy = column_index + 1  # Hierarchy (column number)
                        lineage = row_index + 1       # Lineage (row number)

                        # MERGE ensures that if a node with the same FullName, Hierarchy, and Lineage exists, it won't be duplicated
                        Nodes += (
                            f"MERGE (p:{name} {{FullName: '{people.strip()}', Hierarchy: {hierarchy}, Lineage: {lineage}}});\n"
                        )

            # Then, create relationships between those merged nodes
            for row_index, Family_lines in enumerate(DATA):
                for i in range(len(Family_lines) - 1):
                    if Family_lines[i].strip() and Family_lines[i + 1].strip():
                        parent_hierarchy = i + 1
                        parent_lineage = row_index + 1
                        child_hierarchy = i + 2
                        child_lineage = row_index + 1

                        Relationships += (
                            f"MATCH (p:{name} {{FullName: '{Family_lines[i].strip()}', Hierarchy: {parent_hierarchy}, Lineage: {parent_lineage}}}) "
                            f"MATCH (c:{name} {{FullName: '{Family_lines[i + 1].strip()}', Hierarchy: {child_hierarchy}, Lineage: {child_lineage}}}) "
                            f"MERGE (p)-[:PARENT_TO]->(c);\n"
                        )

            # Add nodes and relationships to the Neo4j Database
            with driver.session() as session:
                # Run all the node creation queries first to ensure no duplicates
                for node_query in Nodes.splitlines():
                    session.run(node_query)

                # Run the relationship creation queries after nodes are merged
                for relationship_query in Relationships.splitlines():
                    session.run(relationship_query)

            return redirect(url_for('main_bp.tree', tree_name=name))

    return render_template("create_tree.html", form=form, error_message=error_message)


@main_bp.route("/tree/<tree_name>", methods=['GET', 'POST'])
def tree(tree_name):
    form = Search_Node()
    
    # Fetch nodes for the form
    with driver.session() as session:
        query = f"""
            MATCH (p:{tree_name})
            RETURN p.FullName AS name"""
        result = session.run(query)
        nodes_choices = [(record["name"], record["name"]) for record in result]
    form.fullname.choices = nodes_choices
    form_modify = AddNodeForm()

    form_modify.parent.choices = nodes_choices
    form_modify.new_parent.choices = nodes_choices
    form_modify.person_to_delete.choices = nodes_choices
    form_modify.person_to_shift.choices = nodes_choices
    form_modify.old_name.choices = nodes_choices
    
    if form_modify.submit.data and form_modify.validate_on_submit():
        if form_modify.action.data == "add":
            with driver.session() as session:
                # Retrieve the parent's hierarchy
                parent_hierarchy_query = f"""
                    MATCH (p:{tree_name} {{FullName: $Parent}})
                    RETURN p.Hierarchy AS parent_hierarchy
                """
                parent_result = session.run(parent_hierarchy_query, Parent=form_modify.parent.data)
                parent_hierarchy = parent_result.single()["parent_hierarchy"]
                
                # Add new node with hierarchy as parent's hierarchy + 1
                session.run(f"""
                    CREATE (n:{tree_name} {{FullName: $full_name, Hierarchy: $new_hierarchy}})
                """, full_name=form_modify.name.data, new_hierarchy=parent_hierarchy + 1)
                
                # Build the dynamic query string to add a relationship
                query = f"""
                    MATCH (a:{tree_name} {{FullName: $Parent}}), (b:{tree_name} {{FullName: $full_name}})
                    MERGE (a)-[r:PARENT_TO]->(b)
                """
                # Create or update relationship
                session.run(query, full_name=form_modify.name.data, Parent=form_modify.parent.data)
            print("Data processed. Redirecting to index.")
            return redirect(url_for("main_bp.tree", tree_name=tree_name))
        
        elif form_modify.action.data == "edit":
            with driver.session() as session:
                # Update the node's name
                session.run(f"""
                    MATCH (n:{tree_name} {{FullName: $old_name}})
                    SET n.FullName = $new_name
                """, old_name=form_modify.old_name.data, new_name=form_modify.new_name.data)
            return redirect(url_for("main_bp.tree", tree_name=tree_name))

        elif form_modify.action.data == "delete":
            with driver.session() as session:
                # Delete person logic
                session.run(f"""
                    MATCH (n:{tree_name} {{FullName: $person_to_delete}})
                    DETACH DELETE n
                """, person_to_delete=form_modify.person_to_delete.data)
            return redirect(url_for("main_bp.tree", tree_name=tree_name))

        elif form_modify.action.data == "shift":
            with driver.session() as session:
                # Retrieve the new parent's hierarchy
                parent_hierarchy_query = f"""
                    MATCH (p:{tree_name} {{FullName: $Parent}})
                    RETURN p.Hierarchy AS parent_hierarchy
                """
                parent_result = session.run(parent_hierarchy_query, Parent=form_modify.new_parent.data)
                parent_hierarchy = parent_result.single()["parent_hierarchy"]

                # Update the hierarchy of the person being shifted
                update_hierarchy_query = f"""
                    MATCH (b:{tree_name} {{FullName: $full_name}})
                    SET b.Hierarchy = $new_hierarchy
                """
                session.run(update_hierarchy_query, full_name=form_modify.person_to_shift.data, new_hierarchy=parent_hierarchy + 1)

                # Step 1: Remove the current parent-child relationship for the person being shifted
                remove_old_relationship_query = f"""
                    MATCH (old_parent:{tree_name})-[r:PARENT_TO]->(b:{tree_name} {{FullName: $full_name}})
                    DELETE r
                """
                session.run(remove_old_relationship_query, full_name=form_modify.person_to_shift.data)

                # Step 2: Create the new relationship between the new parent and the person being shifted
                update_relationship_query = f"""
                    MATCH (a:{tree_name} {{FullName: $Parent}}), (b:{tree_name} {{FullName: $full_name}})
                    MERGE (a)-[r:PARENT_TO]->(b)
                """
                session.run(update_relationship_query, full_name=form_modify.person_to_shift.data, Parent=form_modify.new_parent.data)

                print("Person shifted, old parent relationship deleted, and hierarchy updated. Redirecting to index.")
                return redirect(url_for("main_bp.tree", tree_name=tree_name))

    # Fetch nodes and relationships for rendering the tree
    node_query = f"""
        MATCH (p:{tree_name})
        RETURN p.FullName AS name, p.Hierarchy AS hierarchy, p.Lineage AS lineage
    """
    relationship_query = f"""
        MATCH (p:{tree_name})-[r:PARENT_TO]->(c:{tree_name})
        RETURN p.FullName AS parent, c.FullName AS child
    """
    nodes = []
    links = []
    # Fetch all nodes
    with driver.session() as session:
        node_result = session.run(node_query)
        for record in node_result:
            name = record["name"]
            hierarchy = record["hierarchy"]
            lineage = record["lineage"]
            # Add node if not already in the list (to avoid duplicates)
            if not any(node['name'] == name for node in nodes):
                nodes.append({'name': name, 'hierarchy': hierarchy, 'lineage': lineage})

    # Fetch all relationships
    with driver.session() as session:
        relationship_result = session.run(relationship_query)
        for record in relationship_result:
            parent_name = record["parent"]
            child_name = record["child"]
            # Add link from parent to child
            links.append({'source': parent_name, 'target': child_name})

    return render_template('tree.html', nodes=nodes, relationships=links, form=form, tree_name=tree_name,form_modify=form_modify)

@main_bp.route("/request_tree", methods=['GET', 'POST'])
def Request_Multiple_Tree():
    form = Request_Tree()
    with driver.session() as session:
        # Retrieve distinct labels except for 'Person'
        result = session.run("MATCH (n) WHERE NOT 'Person' IN labels(n) RETURN DISTINCT labels(n) AS labels")
        choices = [(label, label) for record in result for label in record["labels"]]
    form.Tree_Name.choices=choices

    if form.validate_on_submit():
        # Redirect to Multiple_Tree with the selected tree name as a parameter
        return redirect(url_for('main_bp.tree', tree_name=form.Tree_Name.data))

    return render_template("request_tree.html", form=form)
