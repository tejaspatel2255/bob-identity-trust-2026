from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# ==========================================
# SUB-MODELS
# ==========================================

class BehavioralFeatures(BaseModel):
    """
    Sub-model for biometric and behavioral typing features.
    """
    typing_cadence_wpm: float = Field(..., description="Average typing speed in words per minute")
    swipe_speed_px_per_sec: float = Field(..., description="Average swipe movement speed on mobile browser")
    session_duration_seconds: int = Field(..., description="Duration of the session in seconds")
    tap_pressure_avg: float = Field(..., description="Average pressure of key taps on mobile touch screens")


# ==========================================
# REQUEST MODELS
# ==========================================

class SessionEventRequest(BaseModel):
    """
    Schema for log-in session ingestion events.
    """
    customer_id: str = Field(..., description="ID of the customer initiating the session")
    device_fingerprint: str = Field(..., description="Hardware fingerprint signature of the device")
    device_os: str = Field(..., description="Operating system running on the client device")
    ip: str = Field(..., description="IP address of the client connection")
    city: str = Field(..., description="Resolved city location of the client IP")
    geolocation_lat: float = Field(..., description="Resolved latitude coordinate")
    geolocation_lng: float = Field(..., description="Resolved longitude coordinate")
    sim_swap_flag: bool = Field(..., description="Indicates if a SIM swap was flagged on the carrier line recently")
    behavioral_features: BehavioralFeatures = Field(..., description="Behavioral and biometric metrics")


class TransferEventRequest(BaseModel):
    """
    Schema for funds transfer ingestion events.
    """
    session_id: str = Field(..., description="The ID of the session that authorized this transfer")
    beneficiary_id: str = Field(..., description="The unique ID of the beneficiary receiving funds")
    beneficiary_bank_ifsc: str = Field(..., description="Indian Financial System Code of recipient branch")
    amount: float = Field(..., description="Transaction amount in INR")
    is_first_time_beneficiary: bool = Field(..., description="Is this the first time transferring to this recipient")


class EmployeeAccessEventRequest(BaseModel):
    """
    Schema for banking staff account access audits.
    """
    employee_id: str = Field(..., description="Employee ID performing the action")
    account_id: str = Field(..., description="Account ID being viewed or modified")
    customer_id: str = Field(..., description="Customer ID associated with the account")
    action_type: str = Field(..., description="Role operation type (e.g. UPDATE_KYC, OVERRIDE_LIMIT)")
    timestamp: str = Field(..., description="ISO 8601 timestamp of when the action occurred")


# ==========================================
# RESPONSE MODELS
# ==========================================

class SessionEventResponse(BaseModel):
    status: str
    session_id: str
    device_fingerprint: str
    geovelocity_jump_km: float


class StandardResponse(BaseModel):
    status: str
    message: str


class NodeModel(BaseModel):
    id: str
    type: str
    properties: Dict[str, Any]


class EdgeModel(BaseModel):
    source: str
    target: str
    type: str
    properties: Dict[str, Any]


class SubgraphResponse(BaseModel):
    nodes: List[NodeModel]
    edges: List[EdgeModel]


class AccessedAccountModel(BaseModel):
    account_id: str
    timestamp: str
    action_type: str
    outside_hours: bool


class ViewedCustomerModel(BaseModel):
    customer_id: str
    timestamp: str


class EmployeeActivityResponse(BaseModel):
    employee_id: str
    accessed_accounts: List[AccessedAccountModel]
    viewed_customers: List[ViewedCustomerModel]


class HealthResponse(BaseModel):
    neo4j_connected: bool
    total_nodes: int
    total_edges: int
    flagged_last_24h: int
    model_version: str


# ==========================================
# RISK EXPLAINER MODELS
# ==========================================

class RiskScoreRequest(BaseModel):
    entity_type: str = Field(..., description="CUSTOMER_SESSION | EMPLOYEE_ACCESS")
    entity_id: str = Field(..., description="ID of the session or employee being evaluated")
    event_data: Dict[str, Any] = Field(..., description="Raw features matching mock_score_event keys")


class RiskScoreResponse(BaseModel):
    entity_id: str
    entity_type: str
    customer_id: Optional[str] = None
    risk_score: float
    shap_attributions: List[Dict[str, Any]]
    explanation: str
    provider_used: str
    fallback_used: bool
    model_id: str
    action: Dict[str, Any]
    timestamp: str


class RiskEventReviewRequest(BaseModel):
    reviewed: bool = Field(..., description="True if the event has been reviewed by staff")
    review_outcome: str = Field(..., description="Outcome: FALSE_POSITIVE | CONFIRMED_FRAUD")


class ReviewUpdate(BaseModel):
    reviewed: bool
    review_outcome: str  # "FALSE_POSITIVE" | "CONFIRMED_FRAUD" | "CONFIRMED_INSIDER"


