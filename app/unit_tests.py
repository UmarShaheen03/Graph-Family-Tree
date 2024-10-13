from unittest import TestCase
import json
import unittest
import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_wtf import CSRFProtect
from .databases import db, login
from .main.routes import main_bp


from neo4j import GraphDatabase
from .accounts import signup, init_database
from .models import *


# HOW TO RUN python -m unittest unit_tests.py    

## FYI my part tests the functional database not the web app itself. It tests for  correct connection to the neo4j driver 


NEO4J_URI='neo4j+ssc://633149e1.databases.neo4j.io'
NEO4J_USERNAME='neo4j'
NEO4J_PASSWORD='1b_L2Kp4ziyuxubevqHTgHDGxZ1VjYXROCFF2USqdNE'

basedir = os.path.abspath(os.path.dirname(__file__))

class Testing():
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'test.db')

def create_app():
    """Create and configure app"""
    flask_app = Flask(__name__)
    flask_app.config.from_object(Testing)
    flask_app.config['IMAGE_UPLOADS'] = os.path.join(flask_app.root_path,'static', 'uploads')
    csrf = CSRFProtect(flask_app)

    db.init_app(flask_app)
    login.init_app(flask_app)

    flask_app.register_blueprint(main_bp)

    return flask_app


class FunctionalDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    @classmethod
    def tearDownClass(self):
        # Tear Down by CLosing the Driver 
        self.driver.close()


    def setUp(self):
        # SETTING UP THE  NEO4J DRIVER
        self.session = self.driver.session()

    def tearDown(self):
        # Making sure the real database is not affected by dummy testing variables 
        self.session.run("MATCH (p:Person {FullName: 'Person #1'}) DELETE p")
        self.session.close()

    def test_create(self):
        # CREATE TEST 
        prior= self.session.run("MATCH (p:Person ) RETURN count(p) as Prior_Count" )
        self.session.run("CREATE (p:Person {FullName: 'Person #1', Location: 'MCG ,Melbourne'})")
        result = self.session.run("MATCH (p:Person ) RETURN count(p) as Count" )
        record = result.single()
        prior_record=prior.single()
        self.assertIsNotNone(record)
        self.assertEqual(record['Count'],prior_record['Prior_Count']+1)
        print("Node Created Successfully")

    def test_read(self):
        # READ TEST
        self.session.run("CREATE (p:Person {FullName: 'Person #1', Location: 'MCG ,Melbourne'})")
        result = self.session.run("MATCH (p:Person {FullName: 'Person #1'}) RETURN p.FullName AS FullName, p.Location AS Location")
        record = result.single()
        self.assertIsNotNone(record)
        self.assertEqual(record['FullName'], 'Person #1')
        self.assertEqual(record['Location'], 'MCG ,Melbourne')
        print("Node Read Successfully")
        

    def test_update(self):
        # UPDATE TEST
        self.session.run("CREATE (p:Person {FullName: 'Person #1', Location: 'MCG,Melbourne'})")
        self.session.run("MATCH (p:Person {FullName: 'Person #1'}) SET p.Location = 'SCG,Sydney'")
        result = self.session.run("MATCH (p:Person {FullName: 'Person #1'}) RETURN p.Location AS Location")
        record = result.single()
        self.assertEqual(record['Location'], 'SCG,Sydney')
        print('Node Updated Successfully')

    def test_delete(self):
        # DELETE TEST
        self.session.run("CREATE (p:Person {FullName: 'Person #1', Location: 'Perth,WA'})")
        self.session.run("MATCH (p:Person {FullName: 'Person #1'}) DELETE p")
        result = self.session.run("MATCH (p:Person {name: 'Person #1'}) RETURN p")
        record = result.single()
        self.assertIsNone(record)
        print("Node Deleted Successfully")


class Testing_File_To_Graph(unittest.TestCase):

    def setUp(self):
        # SET UP THE TEST FILE 
        print("Setting up for a test")
        # Initialize the file pulled from community.csv
        self.file = """Jeff_Winger,Howard_Winger,Marilyn_Winger
Britta_Perry,Alan_Perry,Laura_Perry
Abed_Nadir,Sam_Nadir,Amina_Nadir
Shirley_Bennett,David_Bennett,Clara_Bennett
Troy_Barnes,Daniel_Barnes,Linda_Barnes
Annie_Edison,Richard_Edison,Patricia_Edison
Pierce_Hawthorne,Frank_Hawthorne,Evelyn_Hawthorne"""

    def tearDown(self):
        # DELETE THE TEST FILE
        print("Tearing down after a test")
       
        del self.file

    def test_query_generates(self):
        Nodes = ""
        # Process each line in the file
        for row_index, Family_lines in enumerate(self.file.splitlines()):  # Split by lines
            for column_index, people in enumerate(Family_lines.split(",")):  # Split by commas
                if people.strip():
                    hierarchy = column_index + 1  # Hierarchy (column number)
                    lineage = row_index + 1       # Lineage (row number)

                    # MERGE ensures that if a node with the same FullName, Hierarchy, and Lineage exists, it won't be duplicated
                    Nodes += (
                        f"MERGE (p:Node{{FullName: '{people.strip()}', Hierarchy: {hierarchy}, Lineage: {lineage}}});\n"
                    )

        # Expected Nodes generation
        expected_output = (
            "MERGE (p:Node{FullName: 'Jeff_Winger', Hierarchy: 1, Lineage: 1});\n"
            "MERGE (p:Node{FullName: 'Howard_Winger', Hierarchy: 2, Lineage: 1});\n"
            "MERGE (p:Node{FullName: 'Marilyn_Winger', Hierarchy: 3, Lineage: 1});\n"
            "MERGE (p:Node{FullName: 'Britta_Perry', Hierarchy: 1, Lineage: 2});\n"
            "MERGE (p:Node{FullName: 'Alan_Perry', Hierarchy: 2, Lineage: 2});\n"
            "MERGE (p:Node{FullName: 'Laura_Perry', Hierarchy: 3, Lineage: 2});\n"
            "MERGE (p:Node{FullName: 'Abed_Nadir', Hierarchy: 1, Lineage: 3});\n"
            "MERGE (p:Node{FullName: 'Sam_Nadir', Hierarchy: 2, Lineage: 3});\n"
            "MERGE (p:Node{FullName: 'Amina_Nadir', Hierarchy: 3, Lineage: 3});\n"
            "MERGE (p:Node{FullName: 'Shirley_Bennett', Hierarchy: 1, Lineage: 4});\n"
            "MERGE (p:Node{FullName: 'David_Bennett', Hierarchy: 2, Lineage: 4});\n"
            "MERGE (p:Node{FullName: 'Clara_Bennett', Hierarchy: 3, Lineage: 4});\n"
            "MERGE (p:Node{FullName: 'Troy_Barnes', Hierarchy: 1, Lineage: 5});\n"
            "MERGE (p:Node{FullName: 'Daniel_Barnes', Hierarchy: 2, Lineage: 5});\n"
            "MERGE (p:Node{FullName: 'Linda_Barnes', Hierarchy: 3, Lineage: 5});\n"
            "MERGE (p:Node{FullName: 'Annie_Edison', Hierarchy: 1, Lineage: 6});\n"
            "MERGE (p:Node{FullName: 'Richard_Edison', Hierarchy: 2, Lineage: 6});\n"
            "MERGE (p:Node{FullName: 'Patricia_Edison', Hierarchy: 3, Lineage: 6});\n"
            "MERGE (p:Node{FullName: 'Pierce_Hawthorne', Hierarchy: 1, Lineage: 7});\n"
            "MERGE (p:Node{FullName: 'Frank_Hawthorne', Hierarchy: 2, Lineage: 7});\n"
            "MERGE (p:Node{FullName: 'Evelyn_Hawthorne', Hierarchy: 3, Lineage: 7});\n"
        )

        # Assert that the generated Nodes string matches the expected output
        self.assertEqual(Nodes, expected_output)
        print("Successfully Parsed the file to create Nodes")

    def test_relationships(self):
    
      Relationships = ""
    
    # Split the file into lines and process each line (family)
      DATA = [line.split(",") for line in self.file.splitlines()]
    
    # First relationship
      first_family = DATA[0]  # First family (Jeff_Winger's family)
      Relationships += (
        f"MATCH (p:Node {{FullName: '{first_family[0].strip()}', Hierarchy: 1, Lineage: 1}}) "
        f"MATCH (c:Node {{FullName: '{first_family[1].strip()}', Hierarchy: 2, Lineage: 1}}) "
        f"MERGE (p)-[:PARENT_TO]->(c);\n"
    )

    # Last relationship
      last_family = DATA[-1]  # Last family (Pierce_Hawthorne's family)
      Relationships += (
        f"MATCH (p:Node {{FullName: '{last_family[1].strip()}', Hierarchy: 2, Lineage: 7}}) "
        f"MATCH (c:Node {{FullName: '{last_family[2].strip()}', Hierarchy: 3, Lineage: 7}}) "
        f"MERGE (p)-[:PARENT_TO]->(c);\n"
    )

    # Expected relationships for first and last
      expected_relationships = (
        "MATCH (p:Node {FullName: 'Jeff_Winger', Hierarchy: 1, Lineage: 1}) "
        "MATCH (c:Node {FullName: 'Howard_Winger', Hierarchy: 2, Lineage: 1}) "
        "MERGE (p)-[:PARENT_TO]->(c);\n"
        "MATCH (p:Node {FullName: 'Frank_Hawthorne', Hierarchy: 2, Lineage: 7}) "
        "MATCH (c:Node {FullName: 'Evelyn_Hawthorne', Hierarchy: 3, Lineage: 7}) "
        "MERGE (p)-[:PARENT_TO]->(c);\n"
    )

    # Assert that the generated relationships match the expected output
      self.assertEqual(Relationships, expected_relationships)
      print("Successfully Parsed the file to create relationships")

class SignupTests(unittest.TestCase):
    def setUp(self):
        flask_app = create_app()
        flask_app.app_context().push()
        init_database() 
    
    def tearDown(self):
        db.drop_all

    def test_init_db(self):
        first_user = db.session.query(User).first()
        self.assertIsNotNone(first_user)
        print(first_user.get_id())

    #def test_blank_fields(self)
    #    signup("email@email.com", "")
    #    self.assert

    #def test_invalid_email():
        pass

    #def test_passwords_dont_match():
        pass

    #def test_existing_username():
        pass

    #def test_existing_email():
        pass

    #def test_long_field():
        pass

    #def test_sqli():
        pass


if __name__ == '__main__':
    unittest.main()



