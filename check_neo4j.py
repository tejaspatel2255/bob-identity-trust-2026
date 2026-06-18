import os
from neo4j import GraphDatabase

NEO4J_URI = "neo4j+s://d9338079.databases.neo4j.io"
NEO4J_PASSWORD = "mSKo4DGVpZWkfmeojQnyAzEtfp6hUGs2DrOenq2XFZw"

usernames = ["d9338079", "neo4j"]

for username in usernames:
    print(f"Testing connectivity with username: {username} ...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(username, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print(f"SUCCESS: Connected with username: {username}")
        # Run a simple query
        with driver.session() as session:
            res = session.run("MATCH (e:Employee {id: 'EMP_RAMESH_PATEL'}) RETURN e.id").single()
            print("EMP_RAMESH_PATEL exists:", res is not None)
        driver.close()
        break
    except Exception as e:
        print(f"FAILED for {username}: {e}")
