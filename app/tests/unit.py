from unittest import TestCase
import json
import unittest

from neo4j import GraphDatabase

from app import create_app, db

# HOW TO RUN python -m unittest unit.py    

## FYI my part tests the functional database not the web app itself. It tests for  correct connection to the neo4j driver 


NEO4J_URI='neo4j+s://633149e1.databases.neo4j.io'
NEO4J_USERNAME='neo4j'
NEO4J_PASSWORD='1b_L2Kp4ziyuxubevqHTgHDGxZ1VjYXROCFF2USqdNE'



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

    def test_read(self):
        # READ TEST
        self.session.run("CREATE (p:Person {FullName: 'Person #1', Location: 'MCG ,Melbourne'})")
        result = self.session.run("MATCH (p:Person {FullName: 'Person #1'}) RETURN p.FullName AS FullName, p.Location AS Location")
        record = result.single()
        self.assertIsNotNone(record)
        self.assertEqual(record['FullName'], 'Person #1')
        self.assertEqual(record['Location'], 'MCG ,Melbourne')
        

    def test_update(self):
        # UPDATE TEST
        self.session.run("CREATE (p:Person {FullName: 'Person #1', Location: 'MCG,Melbourne'})")
        self.session.run("MATCH (p:Person {FullName: 'Person #1'}) SET p.Location = 'SCG,Sydney'")
        result = self.session.run("MATCH (p:Person {FullName: 'Person #1'}) RETURN p.Location AS Location")
        record = result.single()
        self.assertEqual(record['Location'], 'SCG,Sydney')

    def test_delete(self):
        # DELETE TEST
        self.session.run("CREATE (p:Person {FullName: 'Person #1', Location: 'Perth,WA'})")
        self.session.run("MATCH (p:Person {name: 'Person #1'}) DELETE p")
        result = self.session.run("MATCH (p:Person {name: 'Person #1'}) RETURN p")
        record = result.single()
        self.assertIsNone(record)


if __name__ == '__main__':
    unittest.main()



