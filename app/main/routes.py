"""Main route views"""

import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from app.forms import BiographyEditForm, CommentForm
from app.models import Biography,Comment
from datetime import datetime
from flask_login import login_required, current_user
from datetime import datetime
from flask_wtf import CSRFProtect
from neo4j import GraphDatabase
from app.forms import AddNodeForm, UpdateNode, AppendGraph, LoginForm, SignupForm, BiographyEditForm, CommentForm
from app.accounts import signup, login, SignupError, LoginError, init_database
from app import db



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
    loginForm = LoginForm()
    return render_template("login.html", loginForm=loginForm, error="")

@main_bp.route("/signup")
def signup_page():
    signupForm = SignupForm()
    return render_template("signup.html", signupForm=signupForm, error="")

#form submissions for login
@main_bp.route("/login-form", methods=["POST"])
def login_request():
    form = LoginForm()

    #form validation isn't working, so commented out
    #TODO: figure out why it isn't validating
    #if not form.validate_on_submit():
    #    return render_template("login.html", loginForm=form, error="Invalid form")
    
    username_or_email = request.form.get("username_or_email")
    password = request.form.get("password")
    remember = request.form.get("remember")

    #call login function from other file
    try:
        login(username_or_email, password, remember)
    except LoginError as error:
        return render_template("login.html", loginForm=form, error=error)

    #currently sends to home page on success
    return home_page()

#form submissions for signup
@main_bp.route("/signup-form", methods=["POST"])
def signup_request():
    form = SignupForm()

    #form validation isn't working, so commented out
    #TODO: figure out why it isn't validating
    #if not form.validate_on_submit():
    #    return render_template("signup.html", signupForm=form, error="Invalid form")
    
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")
    repeat = request.form.get("repeat")
    remember = request.form.get("remember")

    #call signup function from other file
    try:
        signup(email, username, password, repeat, remember)
    except SignupError as error:
        return render_template("signup.html", signupForm=form, error=error)
    
    #currently sends to home page on success
    return home_page()

@main_bp.route("/tree")
def tree_page():
    """A family tree page"""
    nodes, relationships = fetch_data()
    return render_template('Tree.html', nodes=nodes, relationships=relationships)

@main_bp.route('/biography/<name>', methods=['GET', 'POST'])
def biography(name):
    # Fetch person's biography details from Neo4j
    person = get_person_bio(name)
    
    if not person:
        return "Biography not found.", 404

    # Fetch comments related to this person
    comments = Comment.query.all()
    comment_form = CommentForm()

    if comment_form.validate_on_submit():
        new_comment = Comment(
            username=current_user.username,
            text=comment_form.comment.data,
            timestamp=datetime.now()
        )
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added successfully')
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
                           comments=comments, 
                           comment_form=comment_form)



@main_bp.route('/biography/edit', methods=['GET', 'POST'])
def edit_biography():
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
        return redirect(url_for('main_bp.tree_page'))

    return render_template('edit_biography.html', biography=biography, edit_form=edit_form)

    
    
    
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





NEO4J_URI='neo4j+s://633149e1.databases.neo4j.io'
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
