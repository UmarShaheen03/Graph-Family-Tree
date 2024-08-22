import os
from flask import Flask,  render_template, flash, redirect, url_for, request, session
from neo4j import GraphDatabase
from app import app


NEO4J_URI =os.environ.get('NEO4J_URI')  
NEO4J_USERNAME = os.environ.get('NEO4J_USERNAME')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')


# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def fetch_data():
    with driver.session() as session:
        nodes_result = session.run("MATCH (n:Person) RETURN n ")
        relationships_result = session.run("MATCH (a)-[r]->(b) RETURN a, r, b ")
        nodes = [{'id': record['n'].id, 'name': record['n']['FullName'], 'age': record['n']['Age'], 'about': record['n']['About'], 'location': record['n']['Location'], 'email': record['n']['Email'], 'phoneNumber': record['n']['PhoneNumber'], 'address': record['n']['Address']} for record in nodes_result]
        relationships = [{'source': record['a'].id, 'target': record['b'].id, 'type': record['r'].type} for record in relationships_result]
    return nodes, relationships

@app.route('/')
def index():       ## define the variables used in JINJA TEMPLATING
    nodes, relationships = fetch_data()
    return render_template('Graph.html', nodes=nodes, relationships=relationships)

if __name__ == '__main__':
    app.run(debug=True)