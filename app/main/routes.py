"""Main route views"""

import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from neo4j import GraphDatabase
from datetime import datetime
from flask_wtf import CSRFProtect
from neo4j import GraphDatabase
from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from flask import Flask, flash, render_template, redirect, request, session, url_for
from app.forms import AddNodeForm, UpdateNode, AppendGraph, LoginForm, SignupForm
from app.accounts import signup, login, SignupError, LoginError, init_database


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

    if form.validate_on_submit():
        username_or_email = request.form.get("username_or_email")
        password = request.form.get("password")
        remember = request.form.get("remember")

        try:
            login(username_or_email, password, remember)
        except LoginError as error:
            return render_template("login.html", loginForm=form, error=error)

        #send to home page on success
        return home_page()
    
    else:
        return render_template("login.html", loginForm=form, error="Invalid Form")
    
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
        return home_page()
    
    else:
        return render_template("signup.html", loginForm=form, error="Invalid Form")
   

@main_bp.route("/tree")
def tree_page():
    """A family tree page"""
    nodes, relationships = fetch_data()
    return render_template('Tree.html', nodes=nodes, relationships=relationships)

@main_bp.route("/biography")
def biography_page():
    """The biography page"""
    return render_template('biography.html')


NEO4J_URI='neo4j+ssc://633149e1.databases.neo4j.io'
NEO4J_USERNAME='neo4j'
NEO4J_PASSWORD='1b_L2Kp4ziyuxubevqHTgHDGxZ1VjYXROCFF2USqdNE'


# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))



def fetch_data():
    with driver.session() as session:
        nodes_result = session.run("MATCH (n:Person) RETURN n ")
        relationships_result = session.run("MATCH (a)-[r]->(b) RETURN a, r, b ")
        nodes = [{'id': record['n'].id, 'name': record['n']['FullName'], 'age': record['n']['Age'], 'about': record['n']['About'], 'location': record['n']['Location'], 'email': record['n']['Email'], 'phoneNumber': record['n']['PhoneNumber'], 'address': record['n']['Address'],'Hierarchy': record['n']['Hierarchy']} for record in nodes_result]
        relationships = [{'source': record['a'].id, 'target': record['b'].id, 'type': record['r'].type} for record in relationships_result]
    return nodes, relationships


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
    form.new_parent.choices=nodes
    form.person_to_delete.choices=nodes
    form.person_to_shift.choices=nodes
    form.old_name.choices=nodes
    


    if form.validate_on_submit():
        if form.action.data == "add":
            with driver.session() as session:
                # Add node
                session.run(
                    "CREATE (n:Person {FullName: $full_name})",
                    full_name=form.name.data
                )

                # Build the dynamic query string to add a relationship
                query = f"""
                MATCH (a:Person {{FullName: $Parent}}), (b:Person {{FullName: $full_name}})
                MERGE (a)-[r:Parent]->(b)
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
              query = f"""
                MATCH (a:Person {{FullName: $Parent}}), (b:Person {{FullName: $full_name}})
                MERGE (a)-[r:Parent]->(b)
                """

                # Create or update relationship
              session.run(
                    query,
                    full_name=form.person_to_shift.data,
                    Parent=form.new_parent.data
                )
          
        return redirect(url_for("main_bp.tree_page"))



    return render_template('modify_graph.html', form=form)
