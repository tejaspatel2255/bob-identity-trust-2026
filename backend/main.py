import os
import uuid
import pytz
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from neo4j import Session
from pathlib import Path
from dotenv import load_dotenv

# .env auto-discovery (Fix 1)
_env_path = Path(__file__).parent / ".env"
if not _env_path.exists():
    _env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

# Supabase client import
from supabase import create_client, Client

# Local imports
from backend.db import get_db_session, Neo4jDatabase
from backend.haversine import calculate_haversine_distance
from backend.explainer import mock_score_event, generate_explanation, get_friction_action
from backend.models import (
    SessionEventRequest,
    SessionEventResponse,
    TransferEventRequest,
    EmployeeAccessEventRequest,
    StandardResponse,
    SubgraphResponse,
    EmployeeActivityResponse,
    HealthResponse,
    NodeModel,
    EdgeModel,
    AccessedAccountModel,
    ViewedCustomerModel,
    RiskScoreRequest,
    RiskScoreResponse,
    RiskEventReviewRequest,
    ReviewUpdate
)

# Wrapper to support with db.get_session() syntax in endpoint (Fix 4)
class DbWrapper:
    @staticmethod
    def get_session():
        return Neo4jDatabase.get_driver().session()
db = DbWrapper()

# Initialize FastAPI App
app = FastAPI(
    title="Setu — Unified Identity Trust Graph API",
    description="Event Ingestion & Risk Query Backend for Banking Cybersecurity Hackathon",
    version="1.0.0"
)

# Configure CORS Middleware (Allow All Origins for Frontend Dev) (Fix 3)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize Supabase Client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase_client: Optional[Client] = None

if SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL != "https://your-project.supabase.co":
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully.")
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")

# In-memory storage for local sandbox mode (when Supabase is not configured)
IN_MEMORY_RISK_EVENTS: List[Dict[str, Any]] = [
    {
        "id": "CUST_PRIYA_SHARMA",
        "entity_id": "CUST_PRIYA_SHARMA",
        "entity_type": "CUSTOMER_SESSION",
        "risk_score": 4.2,
        "shap_attributions": [
            {"feature": "behavioral_baseline_drift", "contribution": 0.04}
        ],
        "explanation": "CUSTOMER SESSION flagged at LOW risk. Authenticated on known mobile device. Operating during normal hours. Familiar IP geolocation.",
        "provider_used": "llama-3.3-70b",
        "model_id": "meta-llama/llama-3.3-70b-instruct:free",
        "fallback_used": False,
        "action": "SILENT_PASS",
        "action_level": "LOW",
        "timestamp": (datetime.now(pytz.timezone("Asia/Kolkata")) - timedelta(minutes=30)).isoformat(),
        "reviewed": False,
        "review_outcome": None
    },
    {
        "id": "CUST_UNKNOWN_ATTACKER",
        "entity_id": "CUST_UNKNOWN_ATTACKER",
        "entity_type": "CUSTOMER_SESSION",
        "risk_score": 92.5,
        "shap_attributions": [
            {"feature": "sim_swap_flag", "contribution": 0.38},
            {"feature": "is_new_device", "contribution": 0.22},
            {"feature": "geovelocity_jump", "contribution": 0.19},
            {"feature": "is_first_time_beneficiary", "contribution": 0.135}
        ],
        "explanation": "CUSTOMER SESSION flagged at HIGH risk. SIM swap detected 90 minutes ago. Device identifier is new. Geovelocity jump of 1,200km in under 1 hour. Target transfer: ₹75,000 to first-time beneficiary.",
        "provider_used": "llama-3.3-70b",
        "model_id": "meta-llama/llama-3.3-70b-instruct:free",
        "fallback_used": False,
        "action": "HARD_BLOCK",
        "action_level": "HIGH",
        "timestamp": (datetime.now(pytz.timezone("Asia/Kolkata")) - timedelta(minutes=5)).isoformat(),
        "reviewed": False,
        "review_outcome": None
    },
    {
        "id": "EMP_RAMESH_PATEL",
        "entity_id": "EMP_RAMESH_PATEL",
        "entity_type": "EMPLOYEE_ACCESS",
        "risk_score": 86.4,
        "shap_attributions": [
            {"feature": "outside_hours_access", "contribution": 0.24},
            {"feature": "bulk_account_access", "contribution": 0.28},
            {"feature": "high_balance_accessed_count", "contribution": 0.22},
            {"feature": "recovery_requests_followed", "contribution": 0.124}
        ],
        "explanation": "EMPLOYEE ACCESS flagged at HIGH risk. Branch officer logging in at 11:42 PM (outside shift hours). Accessed 3 HIGH-balance VIP customer accounts within 10 minutes. Account recovery requests followed.",
        "provider_used": "gemini-flash",
        "model_id": "google/gemini-flash-1.5",
        "fallback_used": False,
        "action": "HARD_BLOCK",
        "action_level": "HIGH",
        "timestamp": (datetime.now(pytz.timezone("Asia/Kolkata")) - timedelta(minutes=15)).isoformat(),
        "reviewed": False,
        "review_outcome": None
    }
]

# ==========================================
# EXCEPTION HANDLERS
# ==========================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    """
    Handles standard HTTPExceptions, returning a clean JSON structure.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP Error", "detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """
    Handles request input validation errors (Pydantic).
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Validation Error", "detail": str(exc.errors())}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """
    Global catch-all exception handler to avoid raw stack trace leaks.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "detail": str(exc)}
    )

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def is_outside_hours(timestamp_str: str) -> bool:
    """
    Calculates if a timestamp (ISO 8601) is outside standard business hours (09:00 - 19:00 IST).
    """
    try:
        # Convert Z to offset for standard parsing
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timestamp format. Expected ISO-8601. Error: {e}"
        )
    
    # Target Indian Standard Time (IST)
    ist_tz = pytz.timezone("Asia/Kolkata")
    
    if dt.tzinfo is not None:
        dt_ist = dt.astimezone(ist_tz)
    else:
        # If no timezone offset is provided, treat it as already in IST
        dt_ist = ist_tz.localize(dt)
        
    hour = dt_ist.hour
    return hour < 9 or hour >= 19

def serialize_neo4j_value(val: Any) -> Any:
    """
    Converts Neo4j spatial/temporal objects into serializable JSON types.
    """
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return val

# ==========================================
# ENDPOINTS
# ==========================================

@app.post(
    "/events/session",
    response_model=SessionEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest log-in sessions and calculate geographic velocity"
)
def create_session_event(
    event: SessionEventRequest,
    db: Session = Depends(get_db_session)
):
    """
    Checks customer status, computes geovelocity jump from the previous session using the
    Haversine formula, and inserts the Device/Session nodes and relationships into Neo4j.
    """
    # 1. Verify Customer exists
    cust_check_query = "MATCH (c:Customer {id: $customer_id}) RETURN c.id AS id"
    cust_check_res = db.run(cust_check_query, {"customer_id": event.customer_id}).single()
    if not cust_check_res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{event.customer_id}' does not exist."
        )

    # 2. Get last session location to calculate geovelocity_jump_km
    last_session_query = """
        MATCH (c:Customer {id: $customer_id})-[:INITIATED]->(s:Session)
        RETURN s.geolocation_lat AS lat, s.geolocation_lng AS lng
        ORDER BY s.timestamp DESC
        LIMIT 1
    """
    last_session_res = db.run(last_session_query, {"customer_id": event.customer_id}).single()
    
    geovelocity_jump_km = 0.0
    if last_session_res:
        prev_lat = last_session_res["lat"]
        prev_lng = last_session_res["lng"]
        if prev_lat is not None and prev_lng is not None:
            geovelocity_jump_km = calculate_haversine_distance(
                prev_lat, prev_lng,
                event.geolocation_lat, event.geolocation_lng
            )

    # 3. Generate unique session ID
    session_id = f"SESS_API_{uuid.uuid4().hex[:8].upper()}"
    timestamp_str = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()

    # 4. Determine session risk label (Real-time rule engine)
    # If SIM Swap is active and the device OS matches mobile, flag as FRAUD or SUSPICIOUS
    # If the user is logging in, we label it as LEGITIMATE initially unless risk indicators co-occur
    label = "LEGITIMATE"
    if event.sim_swap_flag and geovelocity_jump_km > 800.0:
        label = "FRAUD"

    # 5. Write to Neo4j database using atomic Cypher operations
    # Storing timestamps as ISO 8601 strings as requested
    transaction_query = """
        // 1. Upsert Device node
        MERGE (d:Device {fingerprint: $device_fingerprint})
        ON CREATE SET d.os = $device_os,
                      d.is_new = true,
                      d.trust_score = 0.5
        ON MATCH SET d.os = $device_os

        // 2. Assess device novelty for this specific customer
        WITH d
        OPTIONAL MATCH (c:Customer {id: $customer_id})-[r:LOGGED_IN_FROM]->(d)
        WITH d, r IS NULL AS is_new_for_cust
        SET d.is_new = is_new_for_cust,
            d.trust_score = CASE WHEN is_new_for_cust THEN 0.4 ELSE 0.9 END

        // 3. Create Session node with behavioral metadata
        CREATE (s:Session {
            id: $session_id,
            timestamp: $timestamp,
            ip: $ip,
            city: $city,
            geolocation_lat: toFloat($geolocation_lat),
            geolocation_lng: toFloat($geolocation_lng),
            duration_seconds: toInteger($duration_seconds),
            sim_swap_flag: toBoolean($sim_swap_flag),
            label: $label,
            typing_cadence_wpm: toFloat($typing_cadence_wpm),
            swipe_speed_px_per_sec: toFloat($swipe_speed_px_per_sec),
            tap_pressure_avg: toFloat($tap_pressure_avg)
        })

        // 4. Link relationships
        WITH d, s
        MATCH (c:Customer {id: $customer_id})
        MERGE (c)-[login:LOGGED_IN_FROM]->(d)
        SET login.timestamp = $timestamp

        MERGE (c)-[init:INITIATED]->(s)
        SET init.timestamp = $timestamp

        MERGE (s)-[used:USED_DEVICE]->(d)
        SET used.geovelocity_jump_km = toFloat($geovelocity_jump_km)
    """

    db.run(
        transaction_query,
        {
            "customer_id": event.customer_id,
            "device_fingerprint": event.device_fingerprint,
            "device_os": event.device_os,
            "session_id": session_id,
            "timestamp": timestamp_str,
            "ip": event.ip,
            "city": event.city,
            "geolocation_lat": event.geolocation_lat,
            "geolocation_lng": event.geolocation_lng,
            "duration_seconds": event.behavioral_features.session_duration_seconds,
            "sim_swap_flag": event.sim_swap_flag,
            "label": label,
            "typing_cadence_wpm": event.behavioral_features.typing_cadence_wpm,
            "swipe_speed_px_per_sec": event.behavioral_features.swipe_speed_px_per_sec,
            "tap_pressure_avg": event.behavioral_features.tap_pressure_avg,
            "geovelocity_jump_km": geovelocity_jump_km
        }
    )

    return {
        "status": "success",
        "session_id": session_id,
        "device_fingerprint": event.device_fingerprint,
        "geovelocity_jump_km": geovelocity_jump_km
    }


@app.post(
    "/events/transfer",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest fund transfers and update labels"
)
def create_transfer_event(
    event: TransferEventRequest,
    db: Session = Depends(get_db_session)
):
    """
    Registers a fund transfer transaction, links the session to the beneficiary,
    and updates the session risk label to FRAUD if co-occurring indicators are met.
    """
    # 1. Verify Session exists
    sess_check_query = "MATCH (s:Session {id: $session_id}) RETURN s.id AS id, s.sim_swap_flag AS sim_swap_flag"
    sess_check_res = db.run(sess_check_query, {"session_id": event.session_id}).single()
    if not sess_check_res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{event.session_id}' does not exist."
        )

    timestamp_str = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()

    # 2. Write transaction
    write_query = """
        // 1. Upsert Beneficiary
        MERGE (b:Beneficiary {id: $beneficiary_id})
        SET b.bank_ifsc = $bank_ifsc,
            b.is_first_time = toBoolean($is_first_time),
            b.amount = toFloat($amount)

        // 2. Connect Session to Beneficiary
        WITH b
        MATCH (s:Session {id: $session_id})
        MERGE (s)-[t:TRANSFERRED_TO]->(b)
        SET t.amount = toFloat($amount),
            t.timestamp = $timestamp
    """
    db.run(
        write_query,
        {
            "beneficiary_id": event.beneficiary_id,
            "bank_ifsc": event.beneficiary_bank_ifsc,
            "is_first_time": event.is_first_time_beneficiary,
            "amount": event.amount,
            "session_id": event.session_id,
            "timestamp": timestamp_str
        }
    )

    # 3. Post-transaction check: Upgrade label to FRAUD if risk indicators co-occur
    # (SIM swap, new device, geovelocity jump > 800km, first-time beneficiary, and amount > 50,000)
    label_eval_query = """
        MATCH (s:Session {id: $session_id})-[u:USED_DEVICE]->(d:Device)
        MATCH (s)-[t:TRANSFERRED_TO]->(b:Beneficiary)
        WHERE s.sim_swap_flag = true 
          AND d.is_new = true 
          AND u.geovelocity_jump_km > 800.0 
          AND b.is_first_time = true 
          AND t.amount > 50000.0
        SET s.label = 'FRAUD'
        RETURN s.label AS label
    """
    db.run(label_eval_query, {"session_id": event.session_id})

    return {
        "status": "success",
        "message": f"Transfer of {event.amount} to beneficiary {event.beneficiary_id} logged successfully."
    }


@app.post(
    "/events/employee_access",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log internal employee access and check for insider threats"
)
def create_employee_access_event(
    event: EmployeeAccessEventRequest,
    db: Session = Depends(get_db_session)
):
    """
    Records employee database operations and compliance reviews. Calculates if the access occurred
    outside of standard hours (IST) and flags the employee as INSIDER if threat patterns match.
    """
    # 1. Verify Employee, Account, and Customer exist
    validation_query = """
        OPTIONAL MATCH (e:Employee {id: $employee_id})
        OPTIONAL MATCH (a:Account {id: $account_id})
        OPTIONAL MATCH (c:Customer {id: $customer_id})
        RETURN e IS NOT NULL AS emp_exists,
               a IS NOT NULL AS acc_exists,
               c IS NOT NULL AS cust_exists
    """
    validation_res = db.run(
        validation_query,
        {
            "employee_id": event.employee_id,
            "account_id": event.account_id,
            "customer_id": event.customer_id
        }
    ).single()

    if not validation_res:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error validating related nodes."
        )

    missing_entities = []
    if not validation_res["emp_exists"]:
        missing_entities.append(f"Employee '{event.employee_id}'")
    if not validation_res["acc_exists"]:
        missing_entities.append(f"Account '{event.account_id}'")
    if not validation_res["cust_exists"]:
        missing_entities.append(f"Customer '{event.customer_id}'")

    if missing_entities:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource not found: {', '.join(missing_entities)}."
        )

    # 2. Compute outside hours
    outside_hours = is_outside_hours(event.timestamp)

    # 3. Create the ACCESSED and VIEWED_KYC edges
    write_query = """
        MATCH (e:Employee {id: $employee_id})
        MATCH (a:Account {id: $account_id})
        MATCH (c:Customer {id: $customer_id})

        // Create ACCESSED relationship
        MERGE (e)-[acc:ACCESSED]->(a)
        SET acc.timestamp = datetime($timestamp),
            acc.action_type = $action_type,
            acc.outside_hours = toBoolean($outside_hours)

        // Create VIEWED_KYC relationship
        MERGE (e)-[view:VIEWED_KYC]->(c)
        SET view.timestamp = datetime($timestamp)
    """
    db.run(
        write_query,
        {
            "employee_id": event.employee_id,
            "account_id": event.account_id,
            "customer_id": event.customer_id,
            "timestamp": event.timestamp,
            "action_type": event.action_type,
            "outside_hours": outside_hours
        }
    )

    # 4. Evaluate for real-time Insider Threat flag
    # Same employee accessing 3+ high-balance accounts outside hours in the last 60 minutes
    insider_eval_query = """
        MATCH (e:Employee {id: $employee_id})
        WHERE e.role IN ['BRANCH_OFFICER', 'KYC_ANALYST']
        
        MATCH (e)-[r:ACCESSED {outside_hours: true}]->(a:Account {balance_tier: 'HIGH'})
        // Cast parameters to datetime objects for Neo4j compatibility
        WHERE r.timestamp >= datetime($hour_ago_str) AND r.timestamp <= datetime($current_time_str)
        
        WITH e, count(distinct a) AS high_balance_count
        WHERE high_balance_count >= 3
        SET e.label = 'INSIDER'
        RETURN e.id AS flagged_id
    """
    
    current_time = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
    hour_ago = (current_time - timedelta(minutes=60)).isoformat()
    
    db.run(
        insider_eval_query,
        {
            "employee_id": event.employee_id,
            "hour_ago_str": hour_ago,
            "current_time_str": event.timestamp
        }
    )

    return {
        "status": "success",
        "message": f"Employee access logged. Outside hours evaluated: {outside_hours}"
    }


def get_static_mock_subgraph(entity_id: str) -> dict:
    # 1. Priya Sharma
    if "priya" in entity_id.lower():
        return {
            "nodes": [
                {"id": "CUST_PRIYA_SHARMA", "type": "Customer", "properties": {"name": "Priya Sharma", "risk_baseline": 0.04, "onboarding_aadhaar_verified": True, "account_age_days": 720}},
                {"id": "ACC_PRIYA", "type": "Account", "properties": {"balance_tier": "MID", "account_type": "SAVINGS", "is_frozen": False}},
                {"id": "DEV_PRIYA", "type": "Device", "properties": {"os": "iOS", "browser": "Safari", "is_new": False, "trust_score": 0.95}},
                {"id": "SESS_PRIYA", "type": "Session", "properties": {"timestamp": "2026-07-01T10:00:00", "ip": "192.168.1.5", "city": "Mumbai", "sim_swap_flag": False, "label": "LEGITIMATE"}}
            ],
            "edges": [
                {"source": "CUST_PRIYA_SHARMA", "target": "ACC_PRIYA", "type": "OWNS", "properties": {}},
                {"source": "CUST_PRIYA_SHARMA", "target": "DEV_PRIYA", "type": "LOGGED_IN_FROM", "properties": {}},
                {"source": "CUST_PRIYA_SHARMA", "target": "SESS_PRIYA", "type": "INITIATED", "properties": {}},
                {"source": "SESS_PRIYA", "target": "DEV_PRIYA", "type": "USED_DEVICE", "properties": {"geovelocity_jump_km": 0.0}}
            ]
        }
    # 2. SIM Swap Attacker
    elif "attacker" in entity_id.lower() or "atk" in entity_id.lower():
        return {
            "nodes": [
                {"id": "CUST_UNKNOWN_ATTACKER", "type": "Customer", "properties": {"name": "SIM Swap Target", "risk_baseline": 0.78, "onboarding_aadhaar_verified": True, "account_age_days": 500}},
                {"id": "ACC_ATTACKER", "type": "Account", "properties": {"balance_tier": "HIGH", "account_type": "SAVINGS", "is_frozen": False}},
                {"id": "DEV_ATTACKER", "type": "Device", "properties": {"os": "Android", "browser": "Chrome", "is_new": True, "trust_score": 0.1}},
                {"id": "SESS_ATTACKER", "type": "Session", "properties": {"timestamp": "2026-07-01T10:15:00", "ip": "103.241.12.89", "city": "Delhi", "sim_swap_flag": True, "label": "FRAUD"}},
                {"id": "BEN_ATTACKER", "type": "Beneficiary", "properties": {"bank_ifsc": "BARB0DELHI", "is_first_time": True, "amount": 75000.0}}
            ],
            "edges": [
                {"source": "CUST_UNKNOWN_ATTACKER", "target": "ACC_ATTACKER", "type": "OWNS", "properties": {}},
                {"source": "CUST_UNKNOWN_ATTACKER", "target": "DEV_ATTACKER", "type": "LOGGED_IN_FROM", "properties": {}},
                {"source": "CUST_UNKNOWN_ATTACKER", "target": "SESS_ATTACKER", "type": "INITIATED", "properties": {}},
                {"source": "SESS_ATTACKER", "target": "DEV_ATTACKER", "type": "USED_DEVICE", "properties": {"geovelocity_jump_km": 1200.0}},
                {"source": "SESS_ATTACKER", "target": "BEN_ATTACKER", "type": "TRANSFERRED_TO", "properties": {"amount": 75000.0}}
            ]
        }
    # 3. Ramesh Patel
    elif "ramesh" in entity_id.lower() or "emp_rp" in entity_id.lower():
        return {
            "nodes": [
                {"id": "EMP_RAMESH_PATEL", "type": "Employee", "properties": {"name": "Ramesh Patel", "role": "BRANCH_OFFICER", "access_level": 4, "department": "Retail Operations", "label": "INSIDER"}},
                {"id": "ACC_VIP_1", "type": "Account", "properties": {"balance_tier": "HIGH", "account_type": "SAVINGS", "is_frozen": False}},
                {"id": "ACC_VIP_2", "type": "Account", "properties": {"balance_tier": "HIGH", "account_type": "CURRENT", "is_frozen": False}},
                {"id": "ACC_VIP_3", "type": "Account", "properties": {"balance_tier": "HIGH", "account_type": "SAVINGS", "is_frozen": False}},
                {"id": "CUST_VIP_1", "type": "Customer", "properties": {"name": "VIP Customer 1", "risk_baseline": 0.02, "onboarding_aadhaar_verified": True, "account_age_days": 1200}},
                {"id": "CUST_VIP_2", "type": "Customer", "properties": {"name": "VIP Customer 2", "risk_baseline": 0.05, "onboarding_aadhaar_verified": True, "account_age_days": 900}},
                {"id": "CUST_VIP_3", "type": "Customer", "properties": {"name": "VIP Customer 3", "risk_baseline": 0.01, "onboarding_aadhaar_verified": True, "account_age_days": 1500}}
            ],
            "edges": [
                {"source": "EMP_RAMESH_PATEL", "target": "ACC_VIP_1", "type": "ACCESSED", "properties": {"action_type": "KYC_OVERRIDE_UNAUTHORIZED", "outside_hours": True}},
                {"source": "EMP_RAMESH_PATEL", "target": "ACC_VIP_2", "type": "ACCESSED", "properties": {"action_type": "KYC_OVERRIDE_UNAUTHORIZED", "outside_hours": True}},
                {"source": "EMP_RAMESH_PATEL", "target": "ACC_VIP_3", "type": "ACCESSED", "properties": {"action_type": "KYC_OVERRIDE_UNAUTHORIZED", "outside_hours": True}},
                {"source": "EMP_RAMESH_PATEL", "target": "CUST_VIP_1", "type": "VIEWED_KYC", "properties": {}},
                {"source": "EMP_RAMESH_PATEL", "target": "CUST_VIP_2", "type": "VIEWED_KYC", "properties": {}},
                {"source": "EMP_RAMESH_PATEL", "target": "CUST_VIP_3", "type": "VIEWED_KYC", "properties": {}},
                {"source": "CUST_VIP_1", "target": "ACC_VIP_1", "type": "OWNS", "properties": {}},
                {"source": "CUST_VIP_2", "target": "ACC_VIP_2", "type": "OWNS", "properties": {}},
                {"source": "CUST_VIP_3", "target": "ACC_VIP_3", "type": "OWNS", "properties": {}}
            ]
        }
    else:
        return {"nodes": [], "edges": []}

def get_static_full_mock_graph() -> dict:
    priya = get_static_mock_subgraph("priya")
    attacker = get_static_mock_subgraph("attacker")
    ramesh = get_static_mock_subgraph("ramesh")
    
    nodes = {n["id"]: n for n in priya["nodes"] + attacker["nodes"] + ramesh["nodes"]}
    edges = []
    seen_edges = set()
    for e in priya["edges"] + attacker["edges"] + ramesh["edges"]:
        edge_key = f"{e['source']}-{e['target']}-{e['type']}"
        if edge_key not in seen_edges:
            seen_edges.add(edge_key)
            edges.append(e)
            
    return {
        "nodes": list(nodes.values()),
        "edges": edges
    }

@app.get(
    "/graph/subgraph/{customer_id}",
    response_model=SubgraphResponse,
    summary="Retrieve a 2-hop subgraph for graph visualizations"
)
def get_customer_subgraph(
    customer_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Queries the database and returns all nodes and edges within 2 hops of the Customer.
    Used primarily for D3.js or react-force-graph visualizations.
    """
    from backend.db import MockDriver
    if isinstance(Neo4jDatabase.get_driver(), MockDriver):
        return get_static_mock_subgraph(customer_id)

    # Verify node exists first
    check_query = "MATCH (n) WHERE n.id = $customer_id OR n.fingerprint = $customer_id RETURN n LIMIT 1"
    if not db.run(check_query, {"customer_id": customer_id}).single():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity with ID '{customer_id}' not found."
        )

    # Get nodes and relationships in 2 hops
    subgraph_query = """
        MATCH (c) WHERE c.id = $customer_id OR c.fingerprint = $customer_id
        OPTIONAL MATCH path = (c)-[*1..2]-(n)
        WITH c, path
        UNWIND (case when path is null then [c] else nodes(path) end) AS node
        UNWIND (case when path is null then [] else relationships(path) end) AS rel
        RETURN collect(distinct node) AS nodes, collect(distinct rel) AS rels
    """
    record = db.run(subgraph_query, {"customer_id": customer_id}).single()

    nodes_out = []
    edges_out = []

    if record:
        for node in record["nodes"]:
            label = list(node.labels)[0] if node.labels else "Unknown"
            node_id = node.get("fingerprint") if label == "Device" else node.get("id")
            
            # Serialize parameters (dates, lists, etc.)
            properties = {k: serialize_neo4j_value(v) for k, v in node.items()}
            
            nodes_out.append(
                NodeModel(
                    id=str(node_id),
                    type=label,
                    properties=properties
                )
            )

        for rel in record["rels"]:
            start_node = rel.start_node
            end_node = rel.end_node
            
            start_label = list(start_node.labels)[0] if start_node.labels else "Unknown"
            end_label = list(end_node.labels)[0] if end_node.labels else "Unknown"
            
            source_id = start_node.get("fingerprint") if start_label == "Device" else start_node.get("id")
            target_id = end_node.get("fingerprint") if end_label == "Device" else end_node.get("id")
            
            properties = {k: serialize_neo4j_value(v) for k, v in rel.items()}

            edges_out.append(
                EdgeModel(
                    source=str(source_id),
                    target=str(target_id),
                    type=rel.type,
                    properties=properties
                )
            )

    return {
        "nodes": nodes_out,
        "edges": edges_out
    }


@app.get("/graph/all")
def get_full_graph():
    """
    Returns up to 500 nodes and all edges between them.
    Used by the /graph-view frontend page.
    """
    from backend.db import MockDriver
    if isinstance(Neo4jDatabase.get_driver(), MockDriver):
        return get_static_full_mock_graph()

    query = """
    MATCH (n)
    WITH n LIMIT 500
    OPTIONAL MATCH (n)-[r]->(m)
    WHERE m IS NOT NULL
    RETURN
        collect(DISTINCT {id: toString(id(n)), type: labels(n)[0], properties: properties(n)}) AS nodes,
        collect(DISTINCT {
            source: toString(id(n)),
            target: toString(id(m)),
            type: type(r),
            properties: properties(r)
        }) AS edges
    """
    with db.get_session() as session:
        result = session.run(query).single()
        if not result:
            return {"nodes": [], "edges": []}
        edges = [e for e in result["edges"] if e["target"] is not None]
        return {"nodes": result["nodes"], "edges": edges}



@app.get(
    "/graph/employee/{employee_id}",
    response_model=EmployeeActivityResponse,
    summary="Get employee activities in the last 24 hours"
)
def get_employee_activity(
    employee_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Fetches all Account nodes and Customer nodes that the employee accessed or inspected
    within the last 24 hours.
    """
    # Check Employee exists
    emp_check = db.run("MATCH (e:Employee {id: $employee_id}) RETURN e.id", {"employee_id": employee_id}).single()
    if not emp_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID '{employee_id}' not found."
        )

    # 24 hours ago timestamp
    cutoff_time_str = (datetime.now(pytz.timezone("Asia/Kolkata")) - timedelta(hours=24)).isoformat()

    # Query accessed accounts and viewed customer KYCs
    # Using string-based ISO 8601 lexicographical comparisons
    activity_query = """
        MATCH (e:Employee {id: $employee_id})
        
        OPTIONAL MATCH (e)-[acc:ACCESSED]->(a:Account)
        WHERE acc.timestamp >= datetime($cutoff_time)
        
        OPTIONAL MATCH (e)-[view:VIEWED_KYC]->(c:Customer)
        WHERE view.timestamp >= datetime($cutoff_time)
        
        WITH e, 
             case when a is not null then {
               account_id: a.id,
               timestamp: acc.timestamp,
               action_type: acc.action_type,
               outside_hours: acc.outside_hours
             } else null end AS acc_info,
             case when c is not null then {
               customer_id: c.id,
               timestamp: view.timestamp
             } else null end AS view_info
             
        RETURN 
          collect(distinct acc_info) AS accessed,
          collect(distinct view_info) AS viewed
    """

    res = db.run(activity_query, {"employee_id": employee_id, "cutoff_time": cutoff_time_str}).single()

    accessed_accounts = []
    viewed_customers = []

    if res:
        # Filter out null elements
        for item in res["accessed"]:
            if item and item.get("account_id") is not None:
                accessed_accounts.append(
                    AccessedAccountModel(
                        account_id=item["account_id"],
                        timestamp=serialize_neo4j_value(item["timestamp"]),
                        action_type=item["action_type"],
                        outside_hours=bool(item["outside_hours"])
                    )
                )

        for item in res["viewed"]:
            if item and item.get("customer_id") is not None:
                viewed_customers.append(
                    ViewedCustomerModel(
                        customer_id=item["customer_id"],
                        timestamp=serialize_neo4j_value(item["timestamp"])
                    )
                )

    return {
        "employee_id": employee_id,
        "accessed_accounts": accessed_accounts,
        "viewed_customers": viewed_customers
    }


@app.get("/health")
async def health_check():
    neo4j_ok = False
    total_nodes = 0
    total_edges = 0
    try:
        with db.get_session() as session:
            node_result = session.run("MATCH (n) RETURN count(n) AS count").single()
            edge_result = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()
            total_nodes = node_result["count"] if node_result else 0
            total_edges = edge_result["count"] if edge_result else 0
            neo4j_ok = True
    except Exception as e:
        print(f"[Setu/Health] Neo4j check failed: {e}")

    flagged_24h = 0
    sb = get_supabase()
    if sb:
        try:
            from datetime import datetime, timedelta, timezone
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
            result = (sb.table("risk_events")
                      .select("id", count="exact")
                      .gte("timestamp", cutoff)
                      .neq("action_level", "LOW")
                      .execute())
            flagged_24h = result.count or 0
        except Exception as e:
            print(f"[Setu/Health] Supabase check failed: {e}")

    return {
        "neo4j_connected": neo4j_ok,
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "flagged_last_24h": flagged_24h,
        "model_version": "setu-mock-v1.0",
        "supabase_connected": sb is not None
    }


@app.on_event("shutdown")
def shutdown_event():
    """
    Cleans up resources at server shutdown.
    """
    Neo4jDatabase.close()
    print("Neo4j connection closed.")


@app.post(
    "/risk/score",
    response_model=RiskScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute risk score and generate plain-language explanation"
)
async def get_risk_score(event: RiskScoreRequest):
    """
    Computes GNN risk score and attributions, queries OpenRouter models sequentially
    to explain the risk, decides policy friction action, logs it to Supabase, and returns the result.
    """
    # 1. Compute mock score and attributions
    risk_score, shap_attrs = mock_score_event(event.event_data)

    # 2. Generate LLM explanation using OpenRouter fallback chain
    explanation_res = await generate_explanation(risk_score, shap_attrs, event.entity_type)

    # 3. Determine friction action
    action_dict = get_friction_action(risk_score)

    timestamp_str = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()
    event_uuid = str(uuid.uuid4())

    # Resolve customer_id (Fix 8)
    customer_id = event.entity_id if event.entity_type == "CUSTOMER_SESSION" else None

    # Create event dictionary for local in-memory storage
    local_row = {
        "id": event_uuid,
        "entity_id": event.entity_id,
        "entity_type": event.entity_type,
        "customer_id": customer_id,
        "risk_score": risk_score,
        "shap_attributions": shap_attrs,
        "explanation": explanation_res["explanation"],
        "provider_used": explanation_res["provider_used"],
        "model_id": explanation_res["model_id"],
        "fallback_used": explanation_res["fallback_used"],
        "action": action_dict["action"],
        "action_level": action_dict["level"],
        "timestamp": timestamp_str,
        "reviewed": False,
        "review_outcome": None
    }
    
    # Save to local in-memory feed
    IN_MEMORY_RISK_EVENTS.append(local_row)

    # 4. Insert records into Supabase if client is initialized
    sb = get_supabase()
    if sb:
        try:
            supabase_row = {
                "id": event_uuid,
                "entity_id": event.entity_id,
                "entity_type": event.entity_type,
                "customer_id": customer_id,
                "risk_score": risk_score,
                "shap_attributions": shap_attrs,
                "explanation": explanation_res["explanation"],
                "provider_used": explanation_res["provider_used"],
                "model_id": explanation_res["model_id"],
                "fallback_used": explanation_res["fallback_used"],
                "action": action_dict["action"],
                "action_level": action_dict["level"],
                "timestamp": timestamp_str,
                "reviewed": False,
                "review_outcome": None
            }
            sb.table("risk_events").insert(supabase_row).execute()
        except Exception as e:
            print(f"Error logging risk event to Supabase: {e}")
    else:
        print("Warning: Supabase client not initialized. Skipping DB insert.")

    return {
        "entity_id": event.entity_id,
        "entity_type": event.entity_type,
        "customer_id": customer_id,
        "risk_score": risk_score,
        "shap_attributions": shap_attrs,
        "explanation": explanation_res["explanation"],
        "provider_used": explanation_res["provider_used"],
        "fallback_used": explanation_res["fallback_used"],
        "model_id": explanation_res["model_id"],
        "action": action_dict,
        "timestamp": timestamp_str
    }


@app.get(
    "/risk/events",
    summary="Get all logged risk events"
)
def get_risk_events():
    """
    Returns all logged risk events. If Supabase is connected, queries Supabase.
    Otherwise, returns the in-memory array.
    """
    if supabase_client:
        try:
            res = supabase_client.table("risk_events").select("*").order("timestamp", desc=True).execute()
            if res.data:
                return res.data
        except Exception as e:
            print(f"Error reading from Supabase, falling back to in-memory: {e}")
    
    # Return in-memory events sorted by timestamp descending
    return sorted(IN_MEMORY_RISK_EVENTS, key=lambda x: x["timestamp"], reverse=True)


def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key or url == "https://your-project.supabase.co" or "your-anon" in key:
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        print(f"Failed to create Supabase client: {e}")
        return None

@app.patch("/risk/events/{event_id}")
async def review_event(event_id: str, update: ReviewUpdate):
    """Update review outcome of a flagged event. Used by /live-feed review buttons."""
    # Update in-memory storage for demo mode
    for ev in IN_MEMORY_RISK_EVENTS:
        if ev.get("id") == event_id or ev.get("entity_id") == event_id:
            ev["reviewed"] = update.reviewed
            ev["review_outcome"] = update.review_outcome

    sb = get_supabase()
    if not sb:
        # Return mock success if Supabase not configured (demo mode)
        return {"id": event_id, "reviewed": update.reviewed,
                "review_outcome": update.review_outcome, "mock": True}
    try:
        # Try updating by ID first
        result = sb.table("risk_events").update({
            "reviewed": update.reviewed,
            "review_outcome": update.review_outcome
        }).eq("id", event_id).execute()
        
        # If no rows were updated, try updating by entity_id
        if not result.data:
            result = sb.table("risk_events").update({
                "reviewed": update.reviewed,
                "review_outcome": update.review_outcome
            }).eq("entity_id", event_id).execute()
            
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/risk/events/{event_id}")
async def get_event(event_id: str):
    """Fetch a single risk event by ID. Used by /cases/[id] page."""
    # Try in-memory first to support offline/demo mode out of the box
    for ev in IN_MEMORY_RISK_EVENTS:
        if ev.get("id") == event_id or ev.get("entity_id") == event_id:
            return ev
            
    sb = get_supabase()
    if not sb:
        raise HTTPException(status_code=503,
            detail="Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY in .env")
    try:
        # Try finding by ID first
        result = sb.table("risk_events").select("*").eq("id", event_id).execute()
        if result.data:
            return result.data[0]
            
        # Otherwise try finding by entity_id
        result = sb.table("risk_events").select("*").eq("entity_id", event_id).execute()
        if result.data:
            return result.data[0]
            
        raise HTTPException(status_code=404, detail="Event not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
