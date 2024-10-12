"""Main route views"""

import os
import io
from flask import Blueprint, Flask, render_template, flash, redirect, url_for, request, session, send_file, send_from_directory
from app.forms import *
from app.forms import BiographyEditForm, ImageUploadForm
from app.models import Biography, Comment, User
from app.accounts import *
from app import db
from neo4j import GraphDatabase
from flask_wtf import CSRFProtect, FlaskForm
from datetime import datetime
from flask_login import login_required, current_user, logout_user
from werkzeug.utils import secure_filename
from neo4j import Driver
import sys #TODO using for debug printing, remove in final
import logging


logging.basicConfig(level=logging.DEBUG)


main_bp = Blueprint('main_bp', __name__)

#test function, resets database and adds two mock users
@main_bp.before_request
def run_once_on_start():
    init_database()
    #replaces code of this function with none, so it only runs once
    run_once_on_start.__code__ = (lambda:None).__code__

@main_bp.route("/")
def home_page():
    """The landing page"""
    return render_template('home.html')

"""LOGIN AND SIGNUP PAGE/FORMS"""

@main_bp.route("/login")
def login_page():
    logoutForm = LogoutForm()
    loginForm = LoginForm()

    if current_user.is_authenticated:
        print("already logged in", sys.stderr)
        return render_template("login.html", loginForm=loginForm, logoutForm=logoutForm, logged_in_as=User.get_username(current_user))
    else:
        return render_template("login.html", loginForm=loginForm, logoutForm=logoutForm)

@main_bp.route("/signup")
def signup_page():
    signupForm = SignupForm()
    return render_template("signup.html", signupForm=signupForm, error="")

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

        #send to home page on success
        return render_template('home.html')
    
    else:
        return render_template("login.html", loginForm=form, logoutForm=logoutForm, error="Invalid Form")

#form submissions for logout
@main_bp.route("/logout-form", methods=["POST"])
def logout_request():
    logout_user()
    return render_template('home.html')
    
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

        #send to home page on success
        return render_template('home.html')
    
    else:
        return render_template("signup.html", loginForm=form, error="Invalid Form")
   

@main_bp.route("/forgot")
def forgot_password_page():
    form = ForgotPassword()
    return render_template("forgot.html", forgotForm=form, submitted=False)

@main_bp.route("/forgot-form", methods=["POST"])
def forgot_request():
    form = ForgotPassword()
    email = request.form.get("email")
    reset_email(email)
    return render_template("forgot.html", forgotForm=form, submitted=True)

@main_bp.route("/reset")
def reset_password_page():
    #get user_id and token from url params
    user_id = request.args.get("user_id")
    token = request.args.get("token")

    if not verify_reset(user_id, token):
        return render_template('home.html')
    
    form = ResetPassword()
    return render_template("reset.html", resetForm=form, token=token, user_id=user_id)

@main_bp.route("/reset-form", methods=["POST"])
def reset_form():
    #get user_id and token from url params
    user_id = request.args.get("user_id")
    token = request.args.get("token")

    if not verify_reset(user_id, token):
        return render_template('home.html')
    
    form = ResetPassword()
    password = request.form.get("password")
    repeat = request.form.get("repeat")

    try:
        reset(user_id, password, repeat)
    except SignupError as error:
        return render_template("reset.html", resetForm=form, error=error, token=token, user_id=user_id)

    loginForm = LoginForm()
    logoutForm = LogoutForm()
    return render_template("login.html", loginForm=loginForm, logoutForm=logoutForm, info="Password reset succesfully, please login") #send user back to login when finished



@main_bp.route("/tree")
def tree_page():
    check = check_login()
    if check != None:
        return check
    
    """A family tree page"""
    form=Search_Node()
    with driver.session() as session:
        result = session.run("MATCH (n:Person) RETURN n.FullName AS name")
        nodes = [(record["name"], record["name"]) for record in result]
    # Set choices for the FullName dropdown field
    form.fullname.choices = nodes
    nodes, relationships = fetch_data()
    return render_template('Tree.html', nodes=nodes, relationships=relationships,form=form)


app=Flask(__name__)
app.config["IMAGE_UPLOADS"] = os.path.join('static', 'uploads') # Directory for storing uploaded images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@main_bp.route('/biography/<name>', methods=['GET', 'POST'])
def biography(name):
    check = check_login()
    if check is not None:
        return check
    print(f"Rendering biography for {name}") 
    # Fetch comments related to this person
    comments = Comment.query.all()
    comment_form = CommentForm()

    # Handle new comment submission
    if comment_form.validate_on_submit():
        new_comment = Comment(
            username=current_user.username,
            text=comment_form.comment.data,
            timestamp=datetime.now()
        )
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added successfully')
        return redirect(url_for('main_bp.biography', name=name))
    
    # Handle image upload
    if request.method == 'POST' and 'image' in request.files:
        image = request.files['image']

        if image.filename != '' and allowed_file(image.filename):
            try:
                # Save the image to the uploads directory
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config["IMAGE_UPLOADS"], filename)
                image.save(image_path)

                # Update the image URL in Neo4j
                image_url = os.path.join('uploads', filename)  # Relative URL for the image
                update_person_image_in_neo4j(name, image_url)

                flash("Image uploaded successfully.")
                return redirect(url_for('main_bp.biography', name=name))
            except Exception as e:
                flash(f"An error occurred while uploading the image: {str(e)}")
                return redirect(request.url)
        else:
            flash("Invalid file type. Please upload a valid image.")
            return redirect(request.url)

    # Fetch person's biography details from Neo4j
    person = get_person_bio(name)
    profile_image = person.get('image_url') if person.get('image_url') else 'default-profile.png'

    return render_template(
        'biography.html',
        name=person['name'], 
        dob=person.get('dob', 'Unknown'), 
        bio=person.get('biography', 'No biography available'), 
        location=person.get('location', 'Unknown'),
        email=person.get('email', 'No email provided'),
        phone_number=person.get('phone_number', 'No phone number provided'),
        address=person.get('address', 'No address provided'),
        comments=comments, 
        comment_form=comment_form,
        admin=User.is_admin(current_user),
        profile_image=profile_image  # This will dynamically show the user's image
    )
    
def update_person_image_in_neo4j(name, image_url):
    """Update the Person node in Neo4j with the image URL."""
    with driver.session() as session:
        session.run(
            """
            MATCH (p:Person {FullName: $name})
            SET p.image_url = $image_url
            """,
            name=name,
            image_url=image_url
        )

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
     
    edit_form.fullname.choices = nodes

    # Check if the form is submitted and validated
    if edit_form.validate_on_submit():
        person_name = edit_form.fullname.data
        
        # Update the person's information in the Neo4j graph database
        with driver.session() as session:
            session.run(
                """
                MATCH (p:Person {FullName: $name})
                SET p.Date_Of_Birth = $DOB,
                    p.Biography = $Biography,
                    p.Location = $Location,
                    p.Email = $Email,
                    p.PhoneNumber = $PhoneNumber,
                    p.Address = $Address
                """,
                name=person_name,
                DOB=edit_form.dob.data,
                Biography=edit_form.biography.data,
                Location=edit_form.location.data,
                Email=edit_form.email.data,
                PhoneNumber=edit_form.phonenumber.data,
                Address=edit_form.address.data
            )
        
        flash(f'Biography for {person_name} has been updated successfully.')
        return redirect(url_for('main_bp.biography', name=person_name))
    return render_template('edit_biography.html', biography=biography, edit_form=edit_form)

    
    
    
# Function to fetch biography from Neo4j
def get_person_bio(name):
    query = """
    MATCH (p:Person {FullName: $name})
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
        result = session.run(query, name=name)
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
@main_bp.route("/Create_Tree", methods=['GET', 'POST'])
def Create_Tree():
    form = submit_File()
    error_message = None  # Initialize an error message variable
    if form.validate_on_submit():
        file = form.file.data
        name = form.name.data
        if file:
            # Check if the file is a CSV
            if not file.filename.endswith('.csv'):
                error_message = 'Invalid file format. Please upload a CSV file.'
                return render_template("Create_Tree.html", form=form, error_message=error_message)

            file_data = file.read().decode('utf-8')
            DATA = []
            Nodes = ""
            Relationships = ""

            
            unique_nodes_by_column = {}

            for row in file_data.splitlines():
                List_Of_Families = row.strip().split(",")  
                DATA.append(List_Of_Families)

            
            for row_index, Family_lines in enumerate(DATA):
                for column_index, people in enumerate(Family_lines):
                    if people.strip():  
                        hierarchy = column_index + 1  # Hierarchy (column number)
                        lineage = row_index + 1       # Lineage (row number)

                        
                        node_key = (hierarchy, people.strip())

                       
                        if node_key not in unique_nodes_by_column:
                            unique_nodes_by_column[node_key] = True  # Mark this node as created
                            Nodes += f"CREATE (p:{name} {{FullName: '{people.strip()}', Hierarchy: {hierarchy}, Lineage: {lineage}}});\n"

            # Create relationships between nodes
            for Family_lines in DATA:
                for i in range(len(Family_lines) - 1):
                    # Check if both current and next nodes are non-empty
                    if Family_lines[i].strip() and Family_lines[i + 1].strip():
                        Relationships += f"MERGE (p:{name} {{FullName: '{Family_lines[i].strip()}'}})-[:PARENT_TO]->(c:{name} {{FullName: '{Family_lines[i + 1].strip()}'}});\n"

            # Add nodes and relationships to the Neo4j Database
            with driver.session() as session:
                for node_query in Nodes.splitlines():
                    session.run(node_query)

                for relationship_query in Relationships.splitlines():
                    session.run(relationship_query)

            return redirect(url_for('main_bp.Multiple_Tree', tree_name=name))

    return render_template("Create_Tree.html", form=form, error_message=error_message)



@main_bp.route("/Multiple_Tree")
def Multiple_Tree():
    tree_name = request.args.get('tree_name')  # Get the tree name from the URL parameter
    form=Search_Node()
    with driver.session() as session:
        query=f"""
    MATCH (p:{tree_name})
    RETURN p.FullName AS name"""
        result = session.run(query)
        nodes = [(record["name"], record["name"]) for record in result]
    # Set choices for the FullName dropdown field
    form.fullname.choices = nodes
    
    

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

    return render_template('Multiple_Trees.html', nodes=nodes, relationships=links,form=form,tree_name=tree_name)


@main_bp.route("/Request_Tree", methods=['GET', 'POST'])
def Request_Multiple_Tree():
    form = Request_Tree()
    with driver.session() as session:
        # Retrieve distinct labels except for 'Person'
        result = session.run("MATCH (n) WHERE NOT 'Person' IN labels(n) RETURN DISTINCT labels(n) AS labels")
        choices = [(label, label) for record in result for label in record["labels"]]
    form.Tree_Name.choices=choices

    if form.validate_on_submit():
        # Redirect to Multiple_Tree with the selected tree name as a parameter
        return redirect(url_for('main_bp.Multiple_Tree', tree_name=form.Tree_Name.data))

    return render_template("Request_Tree.html", form=form)

