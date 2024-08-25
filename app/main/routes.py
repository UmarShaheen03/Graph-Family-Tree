"""Main route views"""

import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from neo4j import GraphDatabase

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

