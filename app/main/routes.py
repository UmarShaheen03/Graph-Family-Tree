"""Main route views"""

import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from neo4j import GraphDatabase
from datetime import datetime
from flask_wtf import CSRFProtect
from neo4j import GraphDatabase
from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from flask import Flask, flash, render_template, redirect, request, session, url_for
from app.forms import UpdateNode,AppendGraph




main_bp = Blueprint('main_bp', __name__)

@main_bp.route("/")
def home_page():
    """The landing page"""
    return render_template('home.html')

@main_bp.route("/login")
def login_page():
    """The login page"""
    return render_template('login.html')

@main_bp.route("/tree")
def tree_page():
    """A family tree page"""
    nodes, relationships = fetch_data()
    return render_template('Tree.html', nodes=nodes, relationships=relationships)

@main_bp.route("/biography")
def biography_page():
    """The biography page"""
    return render_template('biography.html')


@main_bp.route('/addTree', methods=['GET', 'POST'])
def add_tree():
    form = AppendGraph()

    # Fetch nodes for the select box for form 
    with driver.session() as session:
        result = session.run("MATCH (n:Person) RETURN n.FullName AS name")
        nodes = [(record["name"], record["name"]) for record in result]

    # Populate choices for relationship fields
    for relationship_form in form.relationships:
        relationship_form.node.choices = nodes

    if form.validate_on_submit():
        # Add debugging output
        print("Form validated successfully. Processing submission.")

        age_Person = calculate_age(str(form.DateOfBirth.data))

        # Example of how to append nodes and relationships
        # Replace this with actual data handling logic
        with driver.session() as session:
            # Add or update node
            session.run(
                "CREATE (n:Person {FullName: $full_name, DateOfBirth: $date_of_birth, About: $about, Location: $location, Email: $email, PhoneNumber: $phone_number, Address: $address,Age:$age})",
                full_name=form.FullName.data,
                date_of_birth=form.DateOfBirth.data,
                age=age_Person,  # Ensure the date is in the correct format
                about=form.About.data,
                location=form.Location.data,
                email=form.Email.data,
                phone_number=form.PhoneNumber.data,
                address=form.Address.data
            )
        
            # Add relationships
            for relationship in form.relationships:
                node_name = relationship.node.data
                relationship_type = relationship.relationship_type.data

                # Ensure the relationship type is sanitized and valid
                relationship_type = relationship_type.upper().replace(" ", "_")

                # Build the dynamic query string
                query = f"""
                MATCH (a:Person {{FullName: $node_name}}), (b:Person {{FullName: $full_name}})
                MERGE (a)-[r:{relationship_type}]->(b)
                """

                # Create or update relationship
                session.run(
                    query,
                    node_name=node_name,
                    full_name=form.FullName.data
                )

        print("Data processed. Redirecting to index.")
        return redirect(url_for("index"))
    else:
        # Add debugging output
        print("Form validation failed.")
        print(form.errors)  # Print form validation errors if any

    return render_template('AddNode.html', form=form)


@main_bp.route('/updateTree', methods=['GET', 'POST'])
def update_tree():
    Updateform = UpdateNode()
    return render_template('UpdateNode.html', Updateform=Updateform)




NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def fetch_data():
    with driver.session() as session:
        nodes_result = session.run("MATCH (n:Person) RETURN n ")
        relationships_result = session.run("MATCH (a)-[r]->(b) RETURN a, r, b ")
        nodes = [{'id': record['n'].id, 'name': record['n']['FullName'], 'age': record['n']['Age'], 'about': record['n']['About'], 'location': record['n']['Location'], 'email': record['n']['Email'], 'phoneNumber': record['n']['PhoneNumber'], 'address': record['n']['Address']} for record in nodes_result]
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


