import os
import time
from pathlib import Path
from typing import Generator
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver, Session

# .env auto-discovery (Fix 1)
_env_path = Path(__file__).parent / ".env"
if not _env_path.exists():
    _env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

# Neo4j connection retry with exponential backoff (Fix 2)
def get_driver():
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    for attempt in range(5):
        try:
            driver = GraphDatabase.driver(uri, auth=(username, password))
            driver.verify_connectivity()
            print(f"[Setu/Neo4j] Connected successfully on attempt {attempt + 1}")
            return driver
        except Exception as e:
            wait = 2 ** attempt
            print(f"[Setu/Neo4j] Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError("[Setu/Neo4j] Could not connect after 5 attempts. Check NEO4J_URI and credentials.")

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
            cls._driver = get_driver()
            # Seed demo personas if missing
            seed_demo_personas_if_missing(cls._driver)
            
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

def seed_demo_personas_if_missing(driver: Driver) -> None:
    """
    Checks if the demo personas exist in Neo4j, and if not, seeds them.
    This ensures that `/cases/CUST_PRIYA_SHARMA` and other demo links resolve
    correctly and render full graphs.
    """
    with driver.session() as session:
        # Check if Priya Sharma exists
        res = session.run("MATCH (c:Customer {id: 'CUST_PRIYA_SHARMA'}) RETURN c.id LIMIT 1").single()
        if not res:
            print("Seeding simulation personas (Priya Sharma, SIM Swap Attacker, Ramesh Patel) into Neo4j...")
            # 1. Priya Sharma
            session.run("""
                MERGE (c:Customer {id: 'CUST_PRIYA_SHARMA'})
                SET c.name = 'Priya Sharma',
                    c.risk_baseline = 0.04,
                    c.onboarding_aadhaar_verified = true,
                    c.account_age_days = 720
                
                MERGE (a:Account {id: 'ACC_PRIYA'})
                SET a.balance_tier = 'MID',
                    a.account_type = 'SAVINGS',
                    a.is_frozen = false
                
                MERGE (d:Device {fingerprint: 'DEV_PRIYA'})
                SET d.os = 'iOS',
                    d.browser = 'Safari',
                    d.is_new = false,
                    d.trust_score = 0.95
                
                MERGE (s:Session {id: 'SESS_PRIYA'})
                SET s.timestamp = datetime(),
                    s.ip = '192.168.1.5',
                    s.city = 'Mumbai',
                    s.geolocation_lat = 19.0760,
                    s.geolocation_lng = 72.8777,
                    s.duration_seconds = 300,
                    s.sim_swap_flag = false,
                    s.label = 'LEGITIMATE'
                
                MERGE (c)-[:OWNS]->(a)
                MERGE (c)-[l:LOGGED_IN_FROM]->(d)
                SET l.timestamp = datetime()
                MERGE (c)-[i:INITIATED]->(s)
                SET i.timestamp = datetime()
                MERGE (s)-[u:USED_DEVICE]->(d)
                SET u.geovelocity_jump_km = 0.0
            """)
            
            # 2. SIM Swap Attacker
            session.run("""
                MERGE (c:Customer {id: 'CUST_UNKNOWN_ATTACKER'})
                SET c.name = 'SIM Swap Target',
                    c.risk_baseline = 0.78,
                    c.onboarding_aadhaar_verified = true,
                    c.account_age_days = 500
                
                MERGE (a:Account {id: 'ACC_ATTACKER'})
                SET a.balance_tier = 'HIGH',
                    a.account_type = 'SAVINGS',
                    a.is_frozen = false
                
                MERGE (d:Device {fingerprint: 'DEV_ATTACKER'})
                SET d.os = 'Android',
                    d.browser = 'Chrome',
                    d.is_new = true,
                    d.trust_score = 0.1
                
                MERGE (s:Session {id: 'SESS_ATTACKER'})
                SET s.timestamp = datetime(),
                    s.ip = '103.241.12.89',
                    s.city = 'Delhi',
                    s.geolocation_lat = 28.7041,
                    s.geolocation_lng = 77.1025,
                    s.duration_seconds = 45,
                    s.sim_swap_flag = true,
                    s.label = 'FRAUD'
                
                MERGE (b:Beneficiary {id: 'BEN_ATTACKER'})
                SET b.bank_ifsc = 'BARB0DELHI',
                    b.is_first_time = true,
                    b.amount = 75000.0
                
                MERGE (c)-[:OWNS]->(a)
                MERGE (c)-[l:LOGGED_IN_FROM]->(d)
                SET l.timestamp = datetime()
                MERGE (c)-[i:INITIATED]->(s)
                SET i.timestamp = datetime()
                MERGE (s)-[u:USED_DEVICE]->(d)
                SET u.geovelocity_jump_km = 1200.0
                MERGE (s)-[t:TRANSFERRED_TO]->(b)
                SET t.amount = 75000.0,
                    t.timestamp = datetime()
            """)
            
            # 3. Ramesh Patel
            session.run("""
                MERGE (e:Employee {id: 'EMP_RAMESH_PATEL'})
                SET e.name = 'Ramesh Patel',
                    e.role = 'BRANCH_OFFICER',
                    e.access_level = 4,
                    e.department = 'Retail Operations',
                    e.label = 'INSIDER'
                
                MERGE (c1:Customer {id: 'CUST_VIP_1'})
                SET c1.name = 'VIP Customer 1',
                    c1.risk_baseline = 0.02,
                    c1.onboarding_aadhaar_verified = true,
                    c1.account_age_days = 1200
                
                MERGE (c2:Customer {id: 'CUST_VIP_2'})
                SET c2.name = 'VIP Customer 2',
                    c2.risk_baseline = 0.05,
                    c2.onboarding_aadhaar_verified = true,
                    c2.account_age_days = 900
                
                MERGE (c3:Customer {id: 'CUST_VIP_3'})
                SET c3.name = 'VIP Customer 3',
                    c3.risk_baseline = 0.01,
                    c3.onboarding_aadhaar_verified = true,
                    c3.account_age_days = 1500
                
                MERGE (a1:Account {id: 'ACC_VIP_1'})
                SET a1.balance_tier = 'HIGH',
                    a1.account_type = 'SAVINGS',
                    a1.is_frozen = false
                
                MERGE (a2:Account {id: 'ACC_VIP_2'})
                SET a2.balance_tier = 'HIGH',
                    a2.account_type = 'CURRENT',
                    a2.is_frozen = false
                
                MERGE (a3:Account {id: 'ACC_VIP_3'})
                SET a3.balance_tier = 'HIGH',
                    a3.account_type = 'SAVINGS',
                    a3.is_frozen = false
                
                MERGE (c1)-[:OWNS]->(a1)
                MERGE (c2)-[:OWNS]->(a2)
                MERGE (c3)-[:OWNS]->(a3)
                
                MERGE (e)-[acc1:ACCESSED]->(a1)
                SET acc1.timestamp = datetime(),
                    acc1.action_type = 'KYC_OVERRIDE_UNAUTHORIZED',
                    acc1.outside_hours = true
                
                MERGE (e)-[acc2:ACCESSED]->(a2)
                SET acc2.timestamp = datetime(),
                    acc2.action_type = 'KYC_OVERRIDE_UNAUTHORIZED',
                    acc2.outside_hours = true
                
                MERGE (e)-[acc3:ACCESSED]->(a3)
                SET acc3.timestamp = datetime(),
                    acc3.action_type = 'KYC_OVERRIDE_UNAUTHORIZED',
                    acc3.outside_hours = true
                
                MERGE (e)-[v1:VIEWED_KYC]->(c1)
                SET v1.timestamp = datetime()
                MERGE (e)-[v2:VIEWED_KYC]->(c2)
                SET v2.timestamp = datetime()
                MERGE (e)-[v3:VIEWED_KYC]->(c3)
                SET v3.timestamp = datetime()
                
                MERGE (a1)-[r1:RECOVERY_ATTEMPTED]->(c1)
                SET r1.timestamp = datetime(),
                    r1.new_device = true
                
                MERGE (a2)-[r2:RECOVERY_ATTEMPTED]->(c2)
                SET r2.timestamp = datetime(),
                    r2.new_device = true
                
                MERGE (a3)-[r3:RECOVERY_ATTEMPTED]->(c3)
                SET r3.timestamp = datetime(),
                    r3.new_device = true
            """)
            print("Simulation personas seeded successfully.")
