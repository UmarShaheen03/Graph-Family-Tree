from neo4j import GraphDatabase

NEO4J_URI='neo4j+s://633149e1.databases.neo4j.io'
NEO4J_USERNAME='neo4j'
NEO4J_PASSWORD='1b_L2Kp4ziyuxubevqHTgHDGxZ1VjYXROCFF2USqdNE'

driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session() as session:
    result = session.run("MATCH (n) RETURN n LIMIT 1")
    for record in result:
        print(record)
