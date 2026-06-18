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

# Local imports
from backend.db import get_db_session, Neo4jDatabase
from backend.haversine import calculate_haversine_distance
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
    ViewedCustomerModel
)

# Initialize FastAPI App
app = FastAPI(
    title="Setu — Unified Identity Trust Graph API",
    description="Event Ingestion & Risk Query Backend for Banking Cybersecurity Hackathon",
    version="1.0.0"
)

# Configure CORS Middleware (Allow All Origins for Frontend Dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        SET acc.timestamp = $timestamp,
            acc.action_type = $action_type,
            acc.outside_hours = toBoolean($outside_hours)

        // Create VIEWED_KYC relationship
        MERGE (e)-[view:VIEWED_KYC]->(c)
        SET view.timestamp = $timestamp
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
        // ISO string lexicographical comparison for ISO-8601 strings
        WHERE r.timestamp >= $hour_ago_str AND r.timestamp <= $current_time_str
        
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
    # Verify Customer exists first
    check_query = "MATCH (c:Customer {id: $customer_id}) RETURN c.id"
    if not db.run(check_query, {"customer_id": customer_id}).single():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found."
        )

    # Get nodes and relationships in 2 hops
    subgraph_query = """
        MATCH (c:Customer {id: $customer_id})
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
        WHERE acc.timestamp >= $cutoff_time
        
        OPTIONAL MATCH (e)-[view:VIEWED_KYC]->(c:Customer)
        WHERE view.timestamp >= $cutoff_time
        
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


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Get system health and basic graph metrics"
)
def health_check(
    db: Session = Depends(get_db_session)
):
    """
    Monitors database connectivity and retrieves real-time node, edge, and fraud status metrics.
    """
    neo4j_connected = False
    total_nodes = 0
    total_edges = 0
    flagged_last_24h = 0

    try:
        # Check connectivity
        db.run("RETURN 1").single()
        neo4j_connected = True

        # Total nodes
        nodes_res = db.run("MATCH (n) RETURN count(n) AS count").single()
        total_nodes = nodes_res["count"] if nodes_res else 0

        # Total edges
        edges_res = db.run("MATCH ()-[r]->() RETURN count(r) AS count").single()
        total_edges = edges_res["count"] if edges_res else 0

        # Flagged in last 24h
        cutoff_time_str = (datetime.now(pytz.timezone("Asia/Kolkata")) - timedelta(hours=24)).isoformat()
        flagged_res = db.run(
            """
            MATCH (s:Session {label: 'FRAUD'})
            WHERE s.timestamp >= $cutoff_time
            RETURN count(s) AS count
            """,
            {"cutoff_time": cutoff_time_str}
        ).single()
        
        flagged_last_24h = flagged_res["count"] if flagged_res else 0

    except Exception as e:
        # If DB connection fails, we report neo4j_connected=False but still return 200 health check response
        # or raise an exception. The requirements say return neo4j_connected: bool, so we handle it gracefully.
        print(f"Health check warning: {e}")

    return {
        "neo4j_connected": neo4j_connected,
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "flagged_last_24h": flagged_last_24h,
        "model_version": "Setu-GNN-v1.0.0"
    }


@app.on_event("shutdown")
def shutdown_event():
    """
    Cleans up resources at server shutdown.
    """
    Neo4jDatabase.close()
    print("Neo4j connection closed.")
