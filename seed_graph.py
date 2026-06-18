#!/usr/bin/env python3
"""
seed_graph.py - Unified Identity Trust Graph Synthetic Data Generator
Designed for Bank of Baroda 2026 Cybersecurity Hackathon (Theme: Identity Trust & Fraud Prevention)

This script seeds a Neo4j AuraDB or local instance with:
1. 300 Legitimate Customers with normal behavior (known devices, same city, normal hours).
2. 25 Fraud Scenarios (label: FRAUD) with co-occurring risk indicators.
3. 15 Insider Threat Scenarios (label: INSIDER) with suspicious employee behaviors.

Uses batched Cypher transactions (batch size 50) for maximum import performance.
"""

import os
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase, exceptions

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

# Load environment variables from .env file with auto-discovery
find_and_load_env()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Validate configuration
if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
    print("Error: Missing Neo4j credentials in environment variables.")
    print("Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD in your .env file.")
    sys.exit(1)

# Initialize Faker and seed for reproducibility
try:
    from faker import Faker
    fake = Faker("en_IN")  # Indian locale for realistic Indian bank IFSCs and names
except ImportError:
    print("Error: Faker library is not installed. Run 'pip install faker' first.")
    sys.exit(1)

random.seed(42)
Faker.seed(42)

# Global configuration
BATCH_SIZE = 50

# List of Indian cities for realistic geolocation data
INDIAN_CITIES = [
    {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777},
    {"name": "Delhi", "lat": 28.7041, "lng": 77.1025},
    {"name": "Bengaluru", "lat": 12.9716, "lng": 77.5946},
    {"name": "Hyderabad", "lat": 17.3850, "lng": 78.4867},
    {"name": "Ahmedabad", "lat": 23.0225, "lng": 72.5714},
    {"name": "Chennai", "lat": 13.0827, "lng": 80.2707},
    {"name": "Kolkata", "lat": 22.5726, "lng": 88.3639},
    {"name": "Pune", "lat": 18.5204, "lng": 73.8567},
    {"name": "Jaipur", "lat": 26.9124, "lng": 75.7873},
    {"name": "Lucknow", "lat": 26.8467, "lng": 80.9462},
]

def run_cypher_query(session, query, parameters=None, description=""):
    """
    Helper function to run a Cypher query with error handling.
    """
    try:
        result = session.run(query, parameters or {})
        return list(result)
    except exceptions.Neo4jError as e:
        print(f"Cypher Error during {description}: {e}")
        raise

def execute_batched(session, query, items, description=""):
    """
    Executes a query in batches of size BATCH_SIZE.
    The query must use $batch as a parameter representing a list of records.
    """
    total = len(items)
    print(f"Seeding {description} (Total: {total})...")
    
    for i in range(0, total, BATCH_SIZE):
        batch = items[i:i + BATCH_SIZE]
        try:
            session.run(query, {"batch": batch})
        except exceptions.Neo4jError as e:
            print(f"Error executing batch [{i} to {i + len(batch)}] for {description}: {e}")
            raise
    print(f"Successfully finished seeding {description}.")

def setup_constraints(session):
    """
    Sets up Neo4j uniqueness constraints for fast lookups and to prevent duplicate nodes.
    """
    print("Setting up database constraints...")
    
    constraints = [
        ("customer_id", "CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE"),
        ("device_fingerprint", "CREATE CONSTRAINT device_fingerprint IF NOT EXISTS FOR (d:Device) REQUIRE d.fingerprint IS UNIQUE"),
        ("session_id", "CREATE CONSTRAINT session_id IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE"),
        ("employee_id", "CREATE CONSTRAINT employee_id IF NOT EXISTS FOR (e:Employee) REQUIRE e.id IS UNIQUE"),
        ("account_id", "CREATE CONSTRAINT account_id IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE"),
        ("beneficiary_id", "CREATE CONSTRAINT beneficiary_id IF NOT EXISTS FOR (b:Beneficiary) REQUIRE b.id IS UNIQUE")
    ]
    
    for name, stmt in constraints:
        # We run constraints individually since DDL statements cannot be run in standard transactions together
        # Add detailed inline comments before running
        run_cypher_query(
            session,
            stmt,
            description=f"Creation of uniqueness constraint for {name}"
        )
    print("Constraints verified.")

def generate_synthetic_data():
    """
    Generates all nodes and relationship data in memory.
    """
    print("Generating in-memory synthetic dataset...")
    
    # ---------------------------------------------------------
    # 1. LEGITIMATE CUSTOMERS & ENTITIES
    # ---------------------------------------------------------
    customers = []
    accounts = []
    owns_rels = []
    devices = []
    logged_in_rels = []
    sessions = []
    initiated_rels = []
    used_device_rels = []
    beneficiaries = []
    transferred_rels = []
    
    # Trackers for links
    customer_account_map = {}  # Customer ID -> List of Account IDs
    high_balance_accounts = []  # List of (Account ID, Customer ID)
    
    account_idx = 0
    device_idx = 0
    session_idx = 0
    beneficiary_idx = 0
    
    for i in range(300):
        cust_id = f"CUST_{i:04d}"
        cust_name = fake.name()
        
        # Legitimate customer profile
        customers.append({
            "id": cust_id,
            "name": cust_name,
            "risk_baseline": round(random.uniform(0.01, 0.25), 4),
            "onboarding_aadhaar_verified": random.choices([True, False], weights=[0.9, 0.1])[0],
            "account_age_days": random.randint(30, 3650)
        })
        
        # Geolocation anchor for this customer (they normally log in from the same city)
        home_city = random.choice(INDIAN_CITIES)
        
        # Accounts (1 or 2 per customer)
        num_accounts = random.choices([1, 2], weights=[0.85, 0.15])[0]
        customer_account_map[cust_id] = []
        for _ in range(num_accounts):
            acc_id = f"ACC_{account_idx:04d}"
            # 25% High balance to satisfy the insider threat requirements later
            balance_tier = random.choices(["LOW", "MID", "HIGH"], weights=[0.4, 0.35, 0.25])[0]
            
            acc_node = {
                "id": acc_id,
                "balance_tier": balance_tier,
                "account_type": random.choice(["SAVINGS", "CURRENT"]),
                "is_frozen": False
            }
            accounts.append(acc_node)
            owns_rels.append({
                "customer_id": cust_id,
                "account_id": acc_id
            })
            customer_account_map[cust_id].append(acc_id)
            
            if balance_tier == "HIGH":
                high_balance_accounts.append((acc_id, cust_id))
                
            account_idx += 1
            
        # Devices (1 or 2 per customer)
        num_devices = random.choices([1, 2], weights=[0.9, 0.1])[0]
        cust_devices = []
        for _ in range(num_devices):
            dev_fp = f"DEV_FP_{device_idx:04d}_{fake.sha256()[:12].upper()}"
            dev_node = {
                "fingerprint": dev_fp,
                "os": random.choice(["Windows", "macOS", "Android", "iOS"]),
                "browser": random.choice(["Chrome", "Safari", "Edge", "Firefox"]),
                "is_new": False,
                "trust_score": round(random.uniform(0.80, 1.00), 2)
            }
            devices.append(dev_node)
            
            # Logged in relationship
            login_time = (datetime.now() - timedelta(days=random.randint(5, 30))).isoformat()
            logged_in_rels.append({
                "customer_id": cust_id,
                "device_fingerprint": dev_fp,
                "timestamp": login_time
            })
            cust_devices.append(dev_fp)
            device_idx += 1
            
        # Sessions (1 to 3 per customer)
        num_sessions = random.randint(1, 3)
        for _ in range(num_sessions):
            sess_id = f"SESS_{session_idx:04d}"
            
            # Legitimate session attributes (normal hours, known device, same city)
            # Normal working hours: 09:00 to 19:00
            session_date = datetime.now() - timedelta(days=random.randint(0, 30))
            session_hour = random.randint(9, 18)
            session_minute = random.randint(0, 59)
            session_time = session_date.replace(hour=session_hour, minute=session_minute).isoformat()
            
            sessions.append({
                "id": sess_id,
                "timestamp": session_time,
                "ip": fake.ipv4(),
                "city": home_city["name"],
                # Add small random jitter to latitude/longitude within the city
                "geolocation_lat": round(home_city["lat"] + random.uniform(-0.05, 0.05), 4),
                "geolocation_lng": round(home_city["lng"] + random.uniform(-0.05, 0.05), 4),
                "duration_seconds": random.randint(60, 1800),
                "sim_swap_flag": False,
                "label": "LEGITIMATE"
            })
            
            initiated_rels.append({
                "customer_id": cust_id,
                "session_id": sess_id,
                "timestamp": session_time
            })
            
            # Used device relationship (Legitimate -> known device)
            chosen_device = random.choice(cust_devices)
            used_device_rels.append({
                "session_id": sess_id,
                "device_fingerprint": chosen_device,
                "geovelocity_jump_km": 0.0
            })
            
            # 30% chance of money transfer
            if random.random() < 0.30:
                ben_id = f"BEN_{beneficiary_idx:04d}"
                amount = round(random.uniform(500.0, 45000.0), 2)  # Normal amount (< 50,000)
                
                beneficiaries.append({
                    "id": ben_id,
                    "bank_ifsc": f"BARB0{fake.bothify(text='######').upper()}",  # Baroda bank IFSC
                    "is_first_time": random.choices([True, False], weights=[0.15, 0.85])[0],
                    "amount": amount
                })
                
                transferred_rels.append({
                    "session_id": sess_id,
                    "beneficiary_id": ben_id,
                    "amount": amount,
                    "timestamp": session_time
                })
                beneficiary_idx += 1
                
            session_idx += 1

    # ---------------------------------------------------------
    # 2. FRAUD SCENARIOS (Total: 25, label: FRAUD)
    # ---------------------------------------------------------
    # 15 cases (0-14) must co-occur all 4 conditions:
    #   - SIM-swap flag = True
    #   - New device fingerprint (is_new = True)
    #   - Geovelocity jump > 800km (city jump in under 1 hour)
    #   - Transfer to first-time beneficiary > ₹50,000
    #
    # 10 cases (15-24) will be fraud but with partial conditions (to make it a realistic dataset)
    
    # Pick 25 random customers to target for fraud
    target_customers = random.sample(customers, 25)
    
    for f_idx, target_cust in enumerate(target_customers):
        cust_id = target_cust["id"]
        sess_id = f"SESS_FRD_{f_idx:03d}"
        
        # High geovelocity jump requires choosing a city far away from their usual login location
        # Find which city they normally use (look at one of their sessions)
        cust_legit_sessions = [s for s in sessions if any(r["customer_id"] == cust_id and r["session_id"] == s["id"] for r in initiated_rels)]
        normal_city_name = cust_legit_sessions[0]["city"] if cust_legit_sessions else "Mumbai"
        
        # Pick a far-away city
        far_city = next((c for c in INDIAN_CITIES if c["name"] != normal_city_name), INDIAN_CITIES[0])
        # Geovelocity jump: Mumbai to Delhi is ~1150km, Chennai to Delhi ~1750km. Keep it > 800km.
        geovelocity_jump = round(random.uniform(900.0, 2200.0), 2)
        
        # Determine conditions based on case index
        if f_idx < 15:
            # Case 0-14: All 4 conditions co-occur
            sim_swap_flag = True
            is_new_device = True
            velocity_jump = geovelocity_jump
            is_first_time_ben = True
            transfer_amount = round(random.uniform(50001.0, 250000.0), 2)
            has_transfer = True
        elif f_idx < 20:
            # Case 15-19: SIM-swap = True, New Device = True, but geovelocity jump = 0 and normal transfer (< 50,000)
            sim_swap_flag = True
            is_new_device = True
            velocity_jump = 0.0
            is_first_time_ben = False
            transfer_amount = round(random.uniform(1000.0, 15000.0), 2)
            has_transfer = random.choice([True, False])
        else:
            # Case 20-24: New Device = True, Geovelocity jump > 800km, Transfer > 50,000, but SIM-swap = False
            sim_swap_flag = False
            is_new_device = True
            velocity_jump = geovelocity_jump
            is_first_time_ben = True
            transfer_amount = round(random.uniform(55000.0, 180000.0), 2)
            has_transfer = True
            
        # Create Fraud Session
        fraud_time = (datetime.now() - timedelta(days=random.randint(0, 10))).isoformat()
        sessions.append({
            "id": sess_id,
            "timestamp": fraud_time,
            "ip": fake.ipv4(),
            "city": far_city["name"] if velocity_jump > 0 else normal_city_name,
            "geolocation_lat": far_city["lat"] if velocity_jump > 0 else target_cust["risk_baseline"], # placeholder-ish if not jumping
            "geolocation_lng": far_city["lng"] if velocity_jump > 0 else target_cust["risk_baseline"],
            "duration_seconds": random.randint(15, 120),  # Typically short
            "sim_swap_flag": sim_swap_flag,
            "label": "FRAUD"
        })
        
        initiated_rels.append({
            "customer_id": cust_id,
            "session_id": sess_id,
            "timestamp": fraud_time
        })
        
        # Create Fraudulent Device
        fraud_dev_fp = f"DEV_FP_FRD_{f_idx:03d}_{fake.sha256()[:12].upper()}"
        devices.append({
            "fingerprint": fraud_dev_fp,
            "os": random.choice(["Android", "iOS"]),
            "browser": random.choice(["Chrome", "Safari"]),
            "is_new": is_new_device,
            "trust_score": round(random.uniform(0.05, 0.30), 2) # Low trust score
        })
        
        # Connect Customer to Fraudulent Device
        logged_in_rels.append({
            "customer_id": cust_id,
            "device_fingerprint": fraud_dev_fp,
            "timestamp": fraud_time
        })
        
        # Connect Session to Device
        used_device_rels.append({
            "session_id": sess_id,
            "device_fingerprint": fraud_dev_fp,
            "geovelocity_jump_km": velocity_jump
        })
        
        # Create Beneficiary and Transfer if applicable
        if has_transfer:
            ben_id = f"BEN_FRD_{f_idx:03d}"
            beneficiaries.append({
                "id": ben_id,
                "bank_ifsc": f"SBIN0{fake.bothify(text='######').upper()}",  # SBI bank IFSC
                "is_first_time": is_first_time_ben,
                "amount": transfer_amount
            })
            
            transferred_rels.append({
                "session_id": sess_id,
                "beneficiary_id": ben_id,
                "amount": transfer_amount,
                "timestamp": fraud_time
            })
            
    # ---------------------------------------------------------
    # 3. INSIDER THREAT SCENARIOS (Total: 15, label: INSIDER)
    # ---------------------------------------------------------
    # Requirements:
    #   - Same Employee accesses 3+ HIGH-balance accounts in under 60 minutes
    #   - outside_hours = True (before 09:00 or after 19:00)
    #   - Within 2 hours, a RECOVERY_ATTEMPTED edge fires from those accounts
    #   - Employee role is "BRANCH_OFFICER" or "KYC_ANALYST"
    #   - Employee node has label = "INSIDER"
    
    employees = []
    accessed_rels = []
    viewed_kyc_rels = []
    recovery_rels = []
    
    # Generate 10 legitimate employees first
    for e_idx in range(10):
        emp_id = f"EMP_{e_idx:03d}"
        employees.append({
            "id": emp_id,
            "name": fake.name(),
            "role": random.choice(["TELLER", "BRANCH_OFFICER", "KYC_ANALYST", "MANAGER"]),
            "access_level": random.randint(1, 4),
            "department": random.choice(["Retail Operations", "KYC Compliance", "Customer Service"]),
            "label": "LEGITIMATE"
        })
        
        # Legitimate activities
        # Access 2-4 accounts during working hours
        for _ in range(random.randint(2, 4)):
            rand_acc = random.choice(accounts)
            accessed_time = (datetime.now() - timedelta(days=random.randint(1, 20))).replace(hour=random.randint(10, 16)).isoformat()
            accessed_rels.append({
                "employee_id": emp_id,
                "account_id": rand_acc["id"],
                "timestamp": accessed_time,
                "action_type": random.choice(["BALANCE_ENQUIRY", "ADDRESS_UPDATE", "STATEMENT_GEN"]),
                "outside_hours": False
            })
            
        # View 1-3 customers' KYC
        for _ in range(random.randint(1, 3)):
            rand_cust = random.choice(customers)
            view_time = (datetime.now() - timedelta(days=random.randint(1, 20))).replace(hour=random.randint(10, 16)).isoformat()
            viewed_kyc_rels.append({
                "employee_id": emp_id,
                "customer_id": rand_cust["id"],
                "timestamp": view_time
            })
            
    # Verify we have enough HIGH balance accounts. We need 15 insider scenarios * 3 accounts = 45 accounts.
    if len(high_balance_accounts) < 45:
        print(f"Warning: Only {len(high_balance_accounts)} HIGH-balance accounts available. Generating more to meet insider threat constraints...")
        # Upgrade some accounts to HIGH
        additional_needed = 45 - len(high_balance_accounts)
        available_low_mid = [a for a in accounts if a["balance_tier"] != "HIGH"]
        upgraded = random.sample(available_low_mid, additional_needed)
        for u_acc in upgraded:
            u_acc["balance_tier"] = "HIGH"
            # Find the customer owner
            owner_rel = next(r for r in owns_rels if r["account_id"] == u_acc["id"])
            high_balance_accounts.append((u_acc["id"], owner_rel["customer_id"]))
            
    # Shuffle high balance accounts to assign to insider threats
    random.shuffle(high_balance_accounts)
    
    # Generate 15 Insider Threat Employees
    for i_idx in range(15):
        emp_id = f"EMP_INS_{i_idx:03d}"
        employees.append({
            "id": emp_id,
            "name": fake.name(),
            "role": random.choice(["BRANCH_OFFICER", "KYC_ANALYST"]),
            "access_level": random.randint(3, 5),
            "department": random.choice(["High Net Worth operations", "KYC Verification", "Branch Credit Operations"]),
            "label": "INSIDER"
        })
        
        # Select 3 distinct HIGH-balance accounts for this employee
        assigned_accounts = [high_balance_accounts.pop() for _ in range(3)]
        
        # Base timestamp for the suspicious access (outside working hours)
        base_date = datetime.now() - timedelta(days=random.randint(2, 15))
        # Choose a late hour e.g. 21:00 to 05:00
        outside_hour = random.choice([20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6])
        base_timestamp = base_date.replace(hour=outside_hour, minute=random.randint(0, 15), second=0)
        
        # Inside the 60 minutes window:
        # Access 1 at T+0 mins, Access 2 at T+15 mins, Access 3 at T+35 mins
        offsets = [0, 15, 35]
        
        for idx, (acc_id, cust_id) in enumerate(assigned_accounts):
            access_time = (base_timestamp + timedelta(minutes=offsets[idx])).isoformat()
            
            # 1. Suspicious Access
            accessed_rels.append({
                "employee_id": emp_id,
                "account_id": acc_id,
                "timestamp": access_time,
                "action_type": "KYC_OVERRIDE_UNAUTHORIZED",
                "outside_hours": True
            })
            
            # Also view KYC of that customer for completeness
            viewed_kyc_rels.append({
                "employee_id": emp_id,
                "customer_id": cust_id,
                "timestamp": access_time
            })
            
            # 2. Account Recovery attempt within 2 hours
            recovery_delay_minutes = random.randint(15, 90) # Well within 120 minutes
            recovery_time = (base_timestamp + timedelta(minutes=offsets[idx] + recovery_delay_minutes)).isoformat()
            
            recovery_rels.append({
                "account_id": acc_id,
                "customer_id": cust_id,
                "timestamp": recovery_time,
                "new_device": random.choice([True, False]) # Recovery usually triggers new device flags
            })

    # Pack it all together
    dataset = {
        "nodes": {
            "Customer": customers,
            "Account": accounts,
            "Device": devices,
            "Session": sessions,
            "Beneficiary": beneficiaries,
            "Employee": employees
        },
        "relationships": {
            "OWNS": owns_rels,
            "LOGGED_IN_FROM": logged_in_rels,
            "INITIATED": initiated_rels,
            "USED_DEVICE": used_device_rels,
            "ACCESSED": accessed_rels,
            "VIEWED_KYC": viewed_kyc_rels,
            "TRANSFERRED_TO": transferred_rels,
            "RECOVERY_ATTEMPTED": recovery_rels
        }
    }
    return dataset

# ---------------------------------------------------------
# CYPHER SEEDING QUERIES (WITH DETAILED INLINE EXPLANATIONS)
# ---------------------------------------------------------

CYPHER_QUERIES = {
    "Customer": """
        // UNWIND transforms the input batch parameter list into individual rows
        UNWIND $batch AS row
        // MERGE matches or creates a Customer node by its unique ID
        MERGE (c:Customer {id: row.id})
        // SET updates all other properties on the Customer node
        SET c.name = row.name,
            c.risk_baseline = toFloat(row.risk_baseline),
            c.onboarding_aadhaar_verified = toBoolean(row.onboarding_aadhaar_verified),
            c.account_age_days = toInteger(row.account_age_days)
    """,
    
    "Account": """
        // UNWIND converts the collection of account rows into individual elements
        UNWIND $batch AS row
        // MERGE locates or inserts the Account node uniquely by ID
        MERGE (a:Account {id: row.id})
        // SET defines parameters like tier status, type, and freeze state
        SET a.balance_tier = row.balance_tier,
            a.account_type = row.account_type,
            a.is_frozen = toBoolean(row.is_frozen)
    """,
    
    "Device": """
        // UNWIND processes the batch containing Device fingerprints
        UNWIND $batch AS row
        // MERGE identifies the Device node by its unique physical fingerprint
        MERGE (d:Device {fingerprint: row.fingerprint})
        // SET assigns browser, OS details, trust evaluation score, and novelty flag
        SET d.os = row.os,
            d.browser = row.browser,
            d.is_new = toBoolean(row.is_new),
            d.trust_score = toFloat(row.trust_score)
    """,
    
    "Session": """
        // UNWIND processes each Session configuration in the batch
        UNWIND $batch AS row
        // MERGE locates or creates a Session node based on its session ID
        MERGE (s:Session {id: row.id})
        // SET assigns operational indicators, geolocation coordinates, SIM state, and labels
        SET s.timestamp = datetime(row.timestamp),
            s.ip = row.ip,
            s.city = row.city,
            s.geolocation_lat = toFloat(row.geolocation_lat),
            s.geolocation_lng = toFloat(row.geolocation_lng),
            s.duration_seconds = toInteger(row.duration_seconds),
            s.sim_swap_flag = toBoolean(row.sim_swap_flag),
            s.label = row.label
    """,
    
    "Beneficiary": """
        // UNWIND handles the collection of funds recipients
        UNWIND $batch AS row
        // MERGE checks for or inserts a unique Beneficiary node
        MERGE (b:Beneficiary {id: row.id})
        // SET updates routing info, trust status, and the amount transfer history
        SET b.bank_ifsc = row.bank_ifsc,
            b.is_first_time = toBoolean(row.is_first_time),
            b.amount = toFloat(row.amount)
    """,
    
    "Employee": """
        // UNWIND iterates through the input batch of corporate staff records
        UNWIND $batch AS row
        // MERGE establishes a unique Employee node based on employee ID
        MERGE (e:Employee {id: row.id})
        // SET configures administrative privileges, department placement, roles, and training labels
        SET e.name = row.name,
            e.role = row.role,
            e.access_level = toInteger(row.access_level),
            e.department = row.department,
            e.label = row.label
    """,
    
    "OWNS": """
        // UNWIND parses the ownership mappings in the current batch
        UNWIND $batch AS row
        // MATCH queries the database for the unique Customer node
        MATCH (c:Customer {id: row.customer_id})
        // MATCH queries the database for the unique Account node
        MATCH (a:Account {id: row.account_id})
        // MERGE creates a directed OWNS relationship if it does not already exist
        MERGE (c)-[:OWNS]->(a)
    """,
    
    "LOGGED_IN_FROM": """
        // UNWIND iterates through login events mapped in the batch
        UNWIND $batch AS row
        // MATCH finds the relevant Customer by ID
        MATCH (c:Customer {id: row.customer_id})
        // MATCH finds the hardware Device by fingerprint
        MATCH (d:Device {fingerprint: row.device_fingerprint})
        // MERGE establishes the logging audit line connecting them
        MERGE (c)-[r:LOGGED_IN_FROM]->(d)
        // SET records the timestamp on the relationship edge
        SET r.timestamp = datetime(row.timestamp)
    """,
    
    "INITIATED": """
        // UNWIND iterates through user-initiated session connections
        UNWIND $batch AS row
        // MATCH obtains the Customer starting the transaction sequence
        MATCH (c:Customer {id: row.customer_id})
        // MATCH gets the targeted Session record
        MATCH (s:Session {id: row.session_id})
        // MERGE creates the INITIATED timeline link
        MERGE (c)-[r:INITIATED]->(s)
        // SET maps the initialization timestamp
        SET r.timestamp = datetime(row.timestamp)
    """,
    
    "USED_DEVICE": """
        // UNWIND processes the Session-to-Device configuration batch
        UNWIND $batch AS row
        // MATCH gets the Session node
        MATCH (s:Session {id: row.session_id})
        // MATCH gets the Device node
        MATCH (d:Device {fingerprint: row.device_fingerprint})
        // MERGE establishes the physical context of the Session
        MERGE (s)-[r:USED_DEVICE]->(d)
        // SET writes the evaluated geographic distance jump between logins
        SET r.geovelocity_jump_km = toFloat(row.geovelocity_jump_km)
    """,
    
    "ACCESSED": """
        // UNWIND parses employee account review incidents
        UNWIND $batch AS row
        // MATCH finds the Employee agent node
        MATCH (e:Employee {id: row.employee_id})
        // MATCH finds the accessed Account node
        MATCH (a:Account {id: row.account_id})
        // MERGE registers the ACCESSED event edge
        MERGE (e)-[r:ACCESSED]->(a)
        // SET records operation parameters, action tags, and business hours flags
        SET r.timestamp = datetime(row.timestamp),
            r.action_type = row.action_type,
            r.outside_hours = toBoolean(row.outside_hours)
    """,
    
    "VIEWED_KYC": """
        // UNWIND maps Employee reviews of customer identity documents
        UNWIND $batch AS row
        // MATCH finds the Employee executor node
        MATCH (e:Employee {id: row.employee_id})
        // MATCH finds the Customer whose files were inspected
        MATCH (c:Customer {id: row.customer_id})
        // MERGE links the compliance review event
        MERGE (e)-[r:VIEWED_KYC]->(c)
        // SET logs the inspection timestamp
        SET r.timestamp = datetime(row.timestamp)
    """,
    
    "TRANSFERRED_TO": """
        // UNWIND processes outgoing financial routing batches
        UNWIND $batch AS row
        // MATCH locates the triggering Session
        MATCH (s:Session {id: row.session_id})
        // MATCH locates the Beneficiary target
        MATCH (b:Beneficiary {id: row.beneficiary_id})
        // MERGE instantiates the money transfer relationship
        MERGE (s)-[r:TRANSFERRED_TO]->(b)
        // SET saves the monetary amount and execution time directly onto the edge
        SET r.amount = toFloat(row.amount),
            r.timestamp = datetime(row.timestamp)
    """,
    
    "RECOVERY_ATTEMPTED": """
        // UNWIND loops through account recovery events
        UNWIND $batch AS row
        // MATCH references the Account under recovery
        MATCH (a:Account {id: row.account_id})
        // MATCH references the Customer verifying details
        MATCH (c:Customer {id: row.customer_id})
        // MERGE records the recovery event bridge
        MERGE (a)-[r:RECOVERY_ATTEMPTED]->(c)
        // SET stores verification execution time and flags new device alerts
        SET r.timestamp = datetime(row.timestamp),
            r.new_device = toBoolean(row.new_device)
    """
}

def seed_database(driver, dataset):
    """
    Connects to Neo4j and imports the generated nodes and edges in batches.
    """
    with driver.session() as session:
        # 1. Constraints setup
        setup_constraints(session)
        
        # 2. Seed Nodes
        print("\n=== Seeding Nodes ===")
        for node_type, nodes_list in dataset["nodes"].items():
            query = CYPHER_QUERIES[node_type]
            execute_batched(session, query, nodes_list, f"{node_type} nodes")
            
        # 3. Seed Relationships
        print("\n=== Seeding Relationships ===")
        for rel_type, rel_list in dataset["relationships"].items():
            query = CYPHER_QUERIES[rel_type]
            execute_batched(session, query, rel_list, f"[:{rel_type}] relationships")

def print_summary(driver):
    """
    Executes aggregation queries in Neo4j to output database statistics and counts.
    """
    print("\n" + "="*50)
    print("           SEEDING SUCCESSFUL - SUMMARY REPORT")
    print("="*50)
    
    with driver.session() as session:
        # Total nodes by type
        print("\n[Node Counts by Label]")
        node_counts_query = """
            MATCH (n)
            UNWIND labels(n) AS label
            RETURN label, count(*) AS count
            ORDER BY label
        """
        records = run_cypher_query(session, node_counts_query, description="Node counts summary")
        for rec in records:
            print(f"  • {rec['label']}: {rec['count']}")
            
        # Total relationships by type
        print("\n[Relationship Counts by Type]")
        rel_counts_query = """
            MATCH ()-[r]->()
            RETURN type(r) AS type, count(*) AS count
            ORDER BY type
        """
        records = run_cypher_query(session, rel_counts_query, description="Relationship counts summary")
        for rec in records:
            print(f"  • {rec['type']}: {rec['count']}")
            
        # Fraud node count
        print("\n[Target Label Analysis]")
        fraud_query = """
            MATCH (s:Session {label: 'FRAUD'})
            RETURN count(s) AS count
        """
        fraud_count = run_cypher_query(session, fraud_query, description="Fraud count")[0]['count']
        print(f"  • Session nodes with FRAUD label: {fraud_count} (Expected: 25)")
        
        # Insider employee count
        insider_query = """
            MATCH (e:Employee {label: 'INSIDER'})
            RETURN count(e) AS count
        """
        insider_count = run_cypher_query(session, insider_query, description="Insider count")[0]['count']
        print(f"  • Employee nodes with INSIDER label: {insider_count} (Expected: 15)")
        
        # Verify 4-condition co-occurrence for fraud (validation check)
        cooccur_query = """
            MATCH (c:Customer)-[:INITIATED]->(s:Session {label: 'FRAUD', sim_swap_flag: true})
            MATCH (s)-[u:USED_DEVICE]->(d:Device {is_new: true})
            MATCH (s)-[t:TRANSFERRED_TO]->(b:Beneficiary {is_first_time: true})
            WHERE u.geovelocity_jump_km > 800.0 AND t.amount > 50000.0
            RETURN count(s) AS count
        """
        cooccur_count = run_cypher_query(session, cooccur_query, description="Fraud co-occurrence count")[0]['count']
        print(f"  • Fraud sessions with all 4 co-occurring conditions: {cooccur_count} (Expected >= 15)")
        
        # Verify Insider Threat scenarios (validation check)
        insider_verify_query = """
            MATCH (e:Employee {label: 'INSIDER'})-[a:ACCESSED {outside_hours: true}]->(acc:Account {balance_tier: 'HIGH'})
            MATCH (acc)-[r:RECOVERY_ATTEMPTED]->(c:Customer)
            // Ensure recovery attempt is within 2 hours of employee access
            WHERE duration.between(a.timestamp, r.timestamp).seconds <= 7200 
              AND duration.between(a.timestamp, r.timestamp).seconds >= 0
            RETURN count(distinct e) AS distinct_employees, count(distinct acc) AS distinct_compromised_accounts
        """
        res = run_cypher_query(session, insider_verify_query, description="Insider scenarios verification")[0]
        print(f"  • Labeled Insider Employees acting as threats: {res['distinct_employees']} (Expected: 15)")
        print(f"  • High-balance accounts compromised and recovered: {res['distinct_compromised_accounts']} (Expected: 45)")
        
    print("\n" + "="*50)

def main():
    print(f"Connecting to Neo4j database at {NEO4J_URI}...")
    
    # Establish Connection Driver
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        # Verify connectivity
        driver.verify_connectivity()
        print("Connected successfully.")
    except Exception as e:
        print(f"\nConnection Error: Unable to connect to Neo4j. Details: {e}")
        print("Please check your Neo4j instance status and .env configuration.")
        sys.exit(1)
        
    # Generate data
    dataset = generate_synthetic_data()
    
    # Seed database
    try:
        seed_database(driver, dataset)
        # Verify and print statistics
        print_summary(driver)
    except Exception as e:
        print(f"\nSeeding failed with error: {e}")
        sys.exit(1)
    finally:
        driver.close()
        print("Database driver closed.")

if __name__ == "__main__":
    main()
