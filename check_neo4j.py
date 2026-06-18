import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

def find_and_load_env():
    # check current directory, parent, and grandparent
    paths = [
        Path.cwd(),
        Path.cwd().parent,
        Path.cwd().parent.parent
    ]
    for p in paths:
        env_file = p / '.env'
        if env_file.exists():
            load_dotenv(dotenv_path=env_file)
            print(f"Loaded .env from: {env_file.resolve()}")
            return
    # Fallback to standard dotenv loading
    load_dotenv()

find_and_load_env()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
    print("Error: Missing Neo4j credentials. Check your .env file.")
    exit(1)

print(f"Testing connectivity to {NEO4J_URI} using username: {NEO4J_USERNAME} ...")
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    driver.verify_connectivity()
    print("SUCCESS: Connected successfully!")
    driver.close()
except Exception as e:
    print(f"FAILED: {e}")
