import os
from typing import Generator
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver, Session

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

class Neo4jDatabase:
    """
    Singleton class to manage the Neo4j Database driver.
    """
    _driver: Driver = None

    @classmethod
    def get_driver(cls) -> Driver:
        """
        Retrieves the initialized Neo4j driver singleton.
        """
        if cls._driver is None:
            if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
                raise RuntimeError("Neo4j configuration environment variables are missing.")
            
            cls._driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
            )
            # Verify connectivity immediately on creation
            cls._driver.verify_connectivity()
            
        return cls._driver

    @classmethod
    def close(cls) -> None:
        """
        Closes the Neo4j driver connection.
        """
        if cls._driver is not None:
            cls._driver.close()
            cls._driver = None

def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a new Neo4j session.
    Automatically handles session closing when the request context finishes.
    """
    driver = Neo4jDatabase.get_driver()
    session = driver.session()
    try:
        yield session
    finally:
        session.close()
