"""Main route views"""
import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app
from app.forms import *
from app.models import Comment, User, Tree, Notification
from app.accounts import init_database, signup, login, SignupError, LoginError, reset_email, verify_reset, reset
from app.notifs import check_for_emails, get_users_notifs, log_notif, get_all_admin_ids, get_all_ids_with_tree, get_all_trees_with_id, create_notifs_string
from app import db
from neo4j import GraphDatabase
from datetime import datetime
from flask_login import login_required, current_user, logout_user
from itsdangerous import URLSafeTimedSerializer
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, WEBSITE_URL
from werkzeug.utils import secure_filename
from threading import Thread
from . import main_bp

# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

serializer = URLSafeTimedSerializer("SecretKey")

"""HOME AND BACKEND ROUTES"""
#runs once on start, inits databases and starts email thread
@main_bp.before_request
def run_once_on_start():
    #ONLY UNCOMMENT BELOW TO RESET DATABASE
    init_database()
    email_thread = Thread(target=check_for_emails)
    email_thread.start() #TODO may be leaking?
    print("created email thread")
    #replaces code of this function with none, so it only runs once
    run_once_on_start.__code__ = (lambda:None).__code__

#runs after every request, updates jinja global variables
@main_bp.context_processor
def inject_global_vars():
    globals = {
        "is_admin": User.is_admin(current_user),
        "is_verified": User.is_verified(current_user),
        "notifications": get_users_notifs(current_user),
        "website_url": WEBSITE_URL
    }
    return globals

#rhome page
@main_bp.route("/")
def home_page():
    """The landing page"""
    return render_template('home.html')

"""ACCOUNT ROUTES"""

#login page
@main_bp.route("/login")
def login_page():
    logoutForm = LogoutForm()
    loginForm = LoginForm()

    if current_user.is_authenticated:
        return render_template("login.html", loginForm=loginForm, logoutForm=logoutForm, logged_in_as=User.get_username(current_user))
    else:
        return render_template("login.html", loginForm=loginForm, logoutForm=logoutForm)

#signup page
@main_bp.route("/signup")
def signup_page():
    signupForm = SignupForm()

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
            user = db.session.query(User).filter((User.username == username_or_email) | (User.email == username_or_email)).first()
            log_notif(f"User {User.get_username(user)} logged in", get_all_admin_ids(), " Login") #notify all admins of succesful login
        except LoginError as error:
            return render_template("login.html", loginForm=form, logoutForm=logoutForm, error=error)

        #send to dehdashti tree if verified
        if (user.verified):
            return redirect(url_for("main_bp.tree", tree_name="Dehdashti"))
        else:
            return render_template("unverified.html")
    
    else:
        return render_template("login.html", loginForm=form, logoutForm=logoutForm, error="Invalid Form")

#form submissions for logout
@main_bp.route("/logout-form", methods=["POST"])
def logout_request():
    log_notif(f"User {User.get_username(current_user)} logged out", get_all_admin_ids(), " Logout") #notify all admins of logout
    logout_user()
    return redirect(url_for("main_bp.login_page"))
    
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
            return render_template("signup.html", signupForm=form, error=error)

        #request verification status
        request_user()
        #send to unverified explanation
        return render_template("unverified.html")
    
    else:
        return render_template("signup.html", loginForm=form, error="Invalid Form")
   
#forgot password page
@main_bp.route("/forgot")
def forgot_password_page():
    form = ForgotPassword()
    return render_template("forgot.html", forgotForm=form, submitted=False)

#form submissions for forgot password
@main_bp.route("/forgot-form", methods=["POST"])
def forgot_request():
    form = ForgotPassword()
    email = request.form.get("email")
    user = db.session.query(User).filter(User.email == email).first()
    if (user != None):
        id = user.user_id
        if (id == 0): #id 0 is a permanent account, can't change password
            return render_template("forgot.html", forgotForm=form, submitted=False, error="Cannot reset PermaAdmin's password")
    
    reset_email(email)

    return render_template("forgot.html", forgotForm=form, submitted=True)

#reset password page (linked from email)
@main_bp.route("/reset")
def reset_password_page():
    #get user_id and token from url params
    user_id = request.args.get("user_id")
    token = request.args.get("token")

    if not verify_reset(user_id, token):
        return redirect(url_for("main_bp.home_page"))
    
    form = ResetPassword()
    return render_template("reset.html", resetForm=form, token=token, user_id=user_id)

#form submission for reset password
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
        return render_template("reset.html", resetForm=form, error=error, token=token, user_id=user_id)


    user = db.session.query(User).filter(User.user_id == user_id).first()
    ids = get_all_admin_ids()
    if int(user_id) not in ids: #if resetter is a user
        ids.append(user_id)

    log_notif(f"User {User.get_username(user)} reset their password", ids, " Reset") #notify all admins (and user) of password reset

    loginForm = LoginForm()
    logoutForm = LogoutForm()
    
    if current_user.is_authenticated: #if they're already logged in, send them to home
        return redirect(url_for("main_bp.home_page"))   
    else: #otherwise, send user back to login when finished
        return render_template("login.html", loginForm=loginForm, logoutForm=logoutForm, info="Password reset succesfully, please login") 

"""TREE AND BIOGRAPHY ROUTES"""

#tree page (tree_name is the tree displayed)
@main_bp.route("/tree/<tree_name>", methods=['GET', 'POST'])
def tree(tree_name):
    check = check_login()
    if check != None:
        return check
    
    check = check_login_admin()
    if check != None:  # check for tree access, only if not an admin
        users_with_access = get_all_ids_with_tree(tree_name)
        print(users_with_access)
        if User.get_id(current_user) not in users_with_access:
            return redirect(url_for("main_bp.my_dashboard", tree_info=f"Access forbidden to Tree {tree_name}. Request access here")) 
    
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
    no_parent_option = [("No Parent", "No Parent")]

    form_modify.parent.choices = nodes_choices + no_parent_option
    form_modify.new_parent.choices = nodes_choices
    form_modify.person_to_delete.choices = nodes_choices
    form_modify.person_to_shift.choices = nodes_choices
    form_modify.old_name.choices = nodes_choices
    
    if form_modify.submit_modify.data and form_modify.validate_on_submit():
        if form_modify.action.data == "add":
            with driver.session() as session:
                if form_modify.parent.data == "No Parent":
                    # Add new node with no parent relationship
                    session.run(f"""
                        CREATE (n:{tree_name} {{FullName: $full_name, Hierarchy: 1}})
                    """, full_name=form_modify.name.data)
                else:
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
                        MERGE (a)-[r:PARENT_OF]->(b)
                    """
                    # Create or update relationship
                    session.run(query, full_name=form_modify.name.data, Parent=form_modify.parent.data)

            log_notif(f"User {User.get_username(current_user)} added Person {form_modify.name.data} to Tree {tree_name}", 
            get_all_admin_ids() + get_all_ids_with_tree(tree_name), " Tree Create", "tree/" + tree_name)
                
            return redirect(url_for("main_bp.tree", tree_name=tree_name))
        
        elif form_modify.action.data == "edit":
            with driver.session() as session:
                # Update the node's name
                session.run(f"""
                    MATCH (n:{tree_name} {{FullName: $old_name}})
                    SET n.FullName = $new_name
                """, old_name=form_modify.old_name.data, new_name=form_modify.new_name.data)
                
            log_notif(f"User {User.get_username(current_user)} renamed Person {form_modify.old_name.data} from Tree {tree_name} to {form_modify.new_name.data}", 
            get_all_admin_ids() + get_all_ids_with_tree(tree_name), " Tree Update", "tree/" + tree_name)

            return redirect(url_for("main_bp.tree", tree_name=tree_name))

        elif form_modify.action.data == "delete":
            with driver.session() as session:
                # Delete person logic
                session.run(f"""
                    MATCH (n:{tree_name} {{FullName: $person_to_delete}})
                    DETACH DELETE n
                """, person_to_delete=form_modify.person_to_delete.data)

            log_notif(f"User {User.get_username(current_user)} deleted Person {form_modify.person_to_delete.data} from Tree {tree_name}", 
            get_all_admin_ids() + get_all_ids_with_tree(tree_name), " Tree Delete", "tree/" + tree_name)

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
                    MATCH (old_parent:{tree_name})-[r:PARENT_OF]->(b:{tree_name} {{FullName: $full_name}})
                    DELETE r
                """
                session.run(remove_old_relationship_query, full_name=form_modify.person_to_shift.data)

                # Step 2: Create the new relationship between the new parent and the person being shifted
                update_relationship_query = f"""
                    MATCH (a:{tree_name} {{FullName: $Parent}}), (b:{tree_name} {{FullName: $full_name}})
                    MERGE (a)-[r:PARENT_OF]->(b)
                """
                session.run(update_relationship_query, full_name=form_modify.person_to_shift.data, Parent=form_modify.new_parent.data)
                
                log_notif(f"User {User.get_username(current_user)} moved Person {form_modify.person_to_shift.data} from Tree {tree_name} to under {form_modify.new_parent.data}", 
                          get_all_admin_ids() + get_all_ids_with_tree(tree_name), " Tree Move", "tree/" + tree_name)
                return redirect(url_for("main_bp.tree", tree_name=tree_name))

    # Fetch nodes and relationships for rendering the tree
    node_query = f"""
        MATCH (p:{tree_name})
        RETURN p.FullName AS name, p.Hierarchy AS hierarchy, p.Lineage AS lineage
    """
    relationship_query = f"""
        MATCH (p:{tree_name})-[r:PARENT_OF]->(c:{tree_name})
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

    return render_template('tree.html', nodes=nodes, relationships=links, form_search=form, tree_name=tree_name, form_modify=form_modify)

#modify tree page (and form submission)
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

#create tree page (and form submission)
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
                            f"MERGE (p)-[:PARENT_OF]->(c);\n"
                        )

            # Add nodes and relationships to the Neo4j Database
            with driver.session() as session:
                # Run all the node creation queries first to ensure no duplicates
                for node_query in Nodes.splitlines():
                    session.run(node_query)

                # Run the relationship creation queries after nodes are merged
                for relationship_query in Relationships.splitlines():
                    session.run(relationship_query)

            log_notif(f"User {User.get_username(current_user)} created a new Tree {name}", 
            get_all_admin_ids(), " New Tree", "tree/" + name)

            return redirect(url_for('main_bp.tree', tree_name=name))

    return render_template("create_tree.html", form=form, error_message=error_message)

#biography page (name is the person displayed)
@main_bp.route('/biography/<name>', methods=['GET', 'POST'])
def biography(name):
    check = check_login()
    if check != None:
        return check
 
    # Fetch person's biography details
    person = get_person_bio(name)
    
    if not person:
        return "Biography not found.", 404
    if person:
        print(f"Profile Image URL: {person.get('image_url')}")
        with driver.session() as session:
            # Query to get the labels of the node
            query = """
                MATCH (n {FullName: $name}) 
                RETURN labels(n) AS labels
            """
            result = session.run(query, name=name)
            record = result.single()
            if record and record['labels']:
                # Use the first label, assuming the node has only one main label
                tree_name = record['labels'][0]  # Dynamically set the tree_name (label)
         
     # Handle image upload
    if request.method == 'POST':
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and allowed_file(file.filename):
                # Save the file
                filename = secure_filename(file.filename)
                upload_dir = current_app.config['IMAGE_UPLOADS']
                
                filepath = os.path.join(upload_dir, filename)
                filepath = filepath.replace("\\", "/")
                print(filepath + "-------------------------------------")
                file.save(filepath)

                # Update Neo4j with image URL
                with driver.session() as session:
                    query = """
                    MATCH (p {FullName: $full_name})
                    SET p.image_url = $image_url
                    """
                    session.run(query, full_name=name, image_url=filename)

                flash('Image uploaded successfully.')
                return redirect(url_for('main_bp.biography', name=name))
    # Fetch comments related to this person
    comments = Comment.query.filter(Comment.bio_name == name).all()
    comment_form = CommentForm()

    if comment_form.validate_on_submit():
        new_comment = Comment(
            username=current_user.username,
            text=comment_form.comment.data,
            timestamp=datetime.now(),
            bio_name=name
        )
        db.session.add(new_comment)
        db.session.commit()

        flash('Comment added successfully')
        log_notif(f"User {User.get_username(current_user)} commented on Person {name} from Tree {tree_name}", 
                  get_all_ids_with_tree(tree_name), " Comment", "biography/" + name) #notify all admins/users with access about comment
        
        return redirect(url_for('main_bp.biography', name=name))  # Pass 'name' to redirect properly

    # Pass the fetched biography details and comments to the template
    return render_template('biography.html', 
                           full_name=person['name'], 
                           dob=person.get('dob', 'Unknown'), 
                           bio=person.get('biography', 'No biography available'), 
                           location=person.get('location', 'Unknown'),
                           email=person.get('email', 'No email provided'),
                           phone_number=person.get('phone_number', 'No phone number provided'),
                           address=person.get('address', 'No address provided'),
                           profile_image=person.get('image_url'),
                           comments=comments, 
                           comment_form=comment_form)

#biography edit page (and form submission)
@main_bp.route('/biography/edit/<person_name>', methods=['GET', 'POST'])
def edit_biography(person_name):
    check = check_login_admin()
    if check is not None:
        return check
    
    # Get the person's name and default tree_name
    tree_name = 'Person'  # Default label if no tree_name is found

    # If a person_name is provided, dynamically fetch the node's label
    if person_name:
        with driver.session() as session:
            # Query to get the labels of the node
            query = """
                MATCH (n {FullName: $name}) 
                RETURN labels(n) AS labels
            """
            result = session.run(query, name=person_name)
            record = result.single()
            if record and record['labels']:
                # Use the first label, assuming the node has only one main label
                tree_name = record['labels'][0]  # Dynamically set the tree_name (label)

    # Create the form
    edit_form = BiographyEditForm()

    # Fetch nodes (FullName) for the select box for the form
    with driver.session() as session:
        query = f"MATCH (n:{tree_name}) RETURN n.FullName AS name"
        result = session.run(query)
        nodes = [(record["name"], record["name"]) for record in result]

    # Set choices for the FullName dropdown field
    edit_form.fullname.choices = nodes

    # Set the default value for fullname to person_name from the URL
    if person_name:
        edit_form.fullname.data = person_name  # This will pre-select the person_name in the dropdown

    # Check if the form is submitted and validated
    if edit_form.validate_on_submit():
        person_name = edit_form.fullname.data
        
        # Dynamically set the label to match tree_name in the update query
        with driver.session() as session:
            update_query = f"""
                MATCH (p:{tree_name} {{FullName: $full_name}})
                SET p.Date_Of_Birth = $DOB,
                    p.Biography = $Biography,
                    p.Location = $Location,
                    p.Email = $Email,
                    p.PhoneNumber = $PhoneNumber,
                    p.Address = $Address
            """
            session.run(
                update_query,
                full_name=person_name,
                DOB=edit_form.dob.data,
                Biography=edit_form.biography.data,
                Location=edit_form.location.data,
                Email=edit_form.email.data,
                PhoneNumber=edit_form.phonenumber.data,
                Address=edit_form.address.data
            )        
        
        flash(f'Biography for {person_name} has been updated successfully.')
        log_notif(f"User {User.get_username(current_user)} edited the biography of Person {person_name} from Tree {tree_name}", 
            get_all_ids_with_tree(tree_name), " Bio Edit", "biography/" + person_name) #notify all admins/users with access about comment

        return redirect(url_for('main_bp.biography', name=person_name))

    return render_template('edit_biography.html', biography=biography, edit_form=edit_form, tree_name=tree_name)

  
@main_bp.route('/biography/delete_image/<name>', methods=['POST'])
def delete_image(name):
    # Fetch the person to get their current image URL
    person = get_person_bio(name)

    if person and person.get('image_url'):
        image_url = person['image_url']

        # Remove the image file from the local directory
        upload_dir = current_app.config['IMAGE_UPLOADS']
        full_path = os.path.join(upload_dir, os.path.basename(image_url))  # Ensure correct local path

        try:
            os.remove(full_path)
        except OSError as e:
            print(f"Error deleting image file: {e}")

        # Update Neo4j to set the image URL to null
        with driver.session() as session:
            query = """
            MATCH (p {FullName: $full_name})
            SET p.image_url = null
            """
            session.run(query, full_name=name)

        flash('Profile image deleted successfully.')

    return redirect(url_for('main_bp.biography', name=name))
    
"""NOTIFICATION AND DASHBOARD ROUTES"""

#dashboard page
@main_bp.route('/my_dashboard', methods=['GET', 'POST'])
def my_dashboard():
    check = check_login()
    if check is not None:
        return check 
    
    form1 = EmailPreference()
    form2 = IgnoreNotifs()
    form3 = Request_Tree()
   
    accessible = get_all_trees_with_id(User.get_id(current_user))
    all_trees = db.session.query(Tree).all()
    noAccess = []
    for tree in all_trees:
        if tree not in accessible:
            noAccess.append(tree)

    tree_info = request.args.get('tree_info')
    admin_info = request.args.get('admin_info')
    email_info = request.args.get('email_info')
    ignore_info = request.args.get('ignore_info')

    print(f"{tree_info}, {admin_info}, {email_info}, {ignore_info}")

    return render_template('my_dashboard.html', preferenceForm=form1, ignoreForm=form2, treeForm = form3, 
                           accessible_trees=get_all_trees_with_id(User.get_id(current_user)),
                           all_trees = db.session.query(Tree).all(),
                           no_access_trees = noAccess,
                           preferences=User.get_ignored(current_user),
                           often=User.get_often(current_user),
                           tree_info=tree_info,
                           admin_info=admin_info,
                           email_info=email_info,
                           ignore_info=ignore_info)

#form submission for tree access requests
@main_bp.route("/request_tree", methods=['POST'])
def request_tree():
    uid = User.get_id(current_user)
    tree = request.form.get('tree_name')
    comb = str(uid) +'/'+ tree
    token = serializer.dumps(comb, salt="tree-request")
    approval_link = f"approve_tree?token={token}"
    log_notif(f" User {User.get_username(current_user)} is requesting access to the Tree {tree}", get_all_admin_ids(), " Tree Request", approval_link)
    return redirect(url_for("main_bp.my_dashboard", tree_info="Request made succesfully"))

#acceptance of a tree access request
@main_bp.route("/approve_tree", methods=['POST'])
def approve_tree():
    check = check_login_admin()
    if check != None:
        return check
    
    token = request.args.get('token')
    try:
        string = serializer.loads(token, salt="tree-request", max_age=86400)
    except Exception as e:
        return "Invalid or expired token."

    split = string.split('/')
    tree = Tree.query.filter_by(name = split[1]).first()
    if (split[0] not in tree.users):
        tree.users += ", " + split[0]
    db.session.commit()

    log_notif(f"Your request to access Tree {split[1]} has been accepted", [int(split[0])], " Request Accept", "tree/" + split[1])

#form submission for admin requests
@main_bp.route("/request_admin", methods=['POST'])
def request_admin():
    uid = User.get_id(current_user)
    comb = str(uid)
    token = serializer.dumps(comb, salt="admin-request")
    approval_link = f"approve_admin?token={token}"
    log_notif(f" User {User.get_username(current_user)} is requesting admin access", get_all_admin_ids(), " Admin Request", approval_link)
    return redirect(url_for("main_bp.my_dashboard", admin_info="Request made succesfully"))

#acceptance of admin requests
@main_bp.route("/approve_admin", methods=['POST'])
def approve_admin():
    check = check_login_admin()
    if check != None:
        return check
    
    token = request.args.get('token')
    try:
        string = serializer.loads(token, salt="admin-request", max_age=86400)
    except Exception as e:
        return "Invalid or expired token."

    user = db.session.query(User).filter(User.user_id == int(string)).first()
    user.admin = True

    #add admin to all trees access
    trees = Tree.query.all()
    for tree in trees:
        if str(user.user_id) not in tree.users: #avoid duplicates
            tree.users += ", " + str(user.user_id)

    db.session.commit()

    log_notif(f"Your request for Admin status has been accepted", [user.user_id], " Request Accept")

#form submission for user verification requests
@main_bp.route("/request_user", methods=['POST'])
def request_user():
    uid = User.get_id(current_user)
    comb = str(uid)
    token = serializer.dumps(comb, salt="user-request")
    approval_link = f"approve_user?token={token}"
    log_notif(f"User {User.get_username(current_user)} is requesting verification", get_all_admin_ids(), " User Request", approval_link)

#acceptance of user verification requests
@main_bp.route("/approve_user", methods=['POST'])
def approve_user():
    check = check_login_admin()
    if check != None:
        return check
    
    token = request.args.get('token')
    try:
        string = serializer.loads(token, salt="user-request", max_age=86400)
    except Exception as e:
        return "Invalid or expired token."

    user = db.session.query(User).filter(User.user_id == int(string)).first()
    user.verified = True
    db.session.commit()

    log_notif(f"Your request for User status has been accepted", [user.user_id], " Request Accept")

#rejection of user verification requests
@main_bp.route("/reject_user", methods=['POST'])
def reject_user():
    check = check_login_admin()
    if check != None:
        return check
    
    token = request.args.get('token')
    try:
        string = serializer.loads(token, salt="user-request", max_age=86400)
    except Exception as e:
        return "Invalid or expired token."
    
    user = db.session.query(User).filter(User.user_id == int(string)).first()

    if (user.verified == False): #only allow deletion of unverified accounts
        db.session.query(User).filter(User.user_id == int(string)).delete()
        db.session.commit()

        log_notif(f"User {user.username}'s user request has been denied, and the account has been deleted", get_all_admin_ids(), " Request Accept")

#form submission for ignored notifs
@main_bp.route("/preference_form", methods=['POST'])
def update_preferences():
    check = check_login()
    if check != None:
        return check
    
    user = db.session.query(User).filter(User.user_id == User.get_id(current_user)).first()
    user.set_ignored(create_notifs_string(request))
    db.session.commit()

    return redirect(url_for("main_bp.my_dashboard", ignore_info="Preferences changed succesfully"))

#form submission for how often notif emails are sent
@main_bp.route("/often_form", methods=['POST'])
def update_often():
    check = check_login()
    if check != None:
        return check
    
    user = db.session.query(User).filter(User.user_id == User.get_id(current_user)).first()
    user.set_often(request.form.get("preference"))
    db.session.commit()

    return redirect(url_for("main_bp.my_dashboard", email_info="Preferences changed succesfully"))

#unsubscribe page (linked to by email)
@main_bp.route("/unsubscribe/<user_id>", methods=['GET', 'POST'])
def unsubscribe(user_id):
    loginForm = LoginForm()
    logoutForm = LogoutForm()

    if not current_user.is_authenticated: #if not logged in
        return render_template("login.html", loginForm=loginForm, logoutForm=logoutForm, info="Please login to your account to unsubscribe")
    elif (int(user_id) != User.get_id(current_user)): #if logged in as a different user
        return render_template("login.html", loginForm=loginForm, logoutForm=logoutForm, info="Please login to your account to unsubscribe")

    user = db.session.query(User).filter(User.user_id == User.get_id(current_user)).first()
    user.set_often("None")
    db.session.commit()

    return render_template("unsubscribe.html", email=User.get_email(current_user))

#form submission for marking notifs as seen
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
    
@main_bp.route("/log")
def log():
    check = check_login_admin()
    if check != None:
        return check
    
    users = db.session.query(User).all()
    trees = db.session.query(Tree).all()
    
    return render_template("log.html",
                           users=users,
                           trees=trees,
                           master_notifications=get_users_notifs(-1),
                           url=WEBSITE_URL)

"""HELPER FUNCTIONS"""

#returns None if user, or returns login page if not user 
def check_login():
    if not current_user.is_authenticated: #if not logged in
        form = LoginForm()
        logoutForm  = LogoutForm()
        return render_template("login.html", loginForm=form, logoutForm=logoutForm, info="Please login or create an account to view this page")
    
    elif not User.is_verified(current_user): #if unverified
        return render_template("unverified.html") 
    
    else:
        return None

#returns None if admin, or returns dashboard with admin request highlighted if user  
def check_login_admin():
    check = check_login()
    if check != None:
        return check
    
    if not User.is_admin(current_user): #if user is not an admin
        return redirect(url_for("main_bp.my_dashboard", admin_info="Admin permissions required, request them here"))
    
    else:
        return None

#fetch biography info from neo4j
def get_person_bio(full_name):
    query = """
    MATCH (p {FullName: $full_name})
    RETURN p.FullName AS name, 
           p.Hierarchy AS hierarchy, 
           p.Date_Of_Birth AS dob, 
           p.Biography AS biography, 
           p.Location AS location, 
           p.Email AS email, 
           p.PhoneNumber AS phone_number, 
           p.Address AS address,
           p.image_url AS image_url
    """
    with driver.session() as session:
        result = session.run(query, full_name=full_name)
        return result.single()

#fetch tree info from neo4j
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

#calculate age from dob string, for biography
def calculate_age(date_of_birth_str):
    # Assuming date_of_birth_str is in the format 'YYYY-MM-DD'
    date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d')
    today = datetime.today()
    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    if age is not None:
            print(f"Calculated Age: {age}",date_of_birth_str)
    return age
    
#function for checking if image has right extension
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS