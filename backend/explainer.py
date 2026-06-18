import os
import httpx
import json
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}" if OPENROUTER_API_KEY else "",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://setu-trustgraph.app",   # Required by OpenRouter
    "X-Title": "Setu Identity Trust Graph"           # Shown in OpenRouter dashboard
}

SYSTEM_PROMPT = """You are a bank fraud analyst assistant for Bank of Baroda's Setu Identity Trust system.
You ONLY explain fraud/risk decisions based on the SHAP feature attributions provided.
Never add information not present in the attributions. Never guess or speculate.
Write in plain language a compliance officer or bank auditor can understand and sign off on.
Be concise: 2 sentences maximum. Start with the entity type and risk level."""

# Model fallback order — all routed through the single OpenRouter API key
MODELS = [
    {"id": "meta-llama/llama-3.3-70b-instruct:free", "label": "llama-3.3-70b", "timeout": 8.0},
    {"id": "google/gemini-flash-1.5",                "label": "gemini-flash",  "timeout": 10.0},
    {"id": "openai/gpt-4o-mini",                     "label": "gpt-4o-mini",   "timeout": 12.0},
]

async def call_openrouter(prompt: str, model_id: str, timeout: float) -> str:
    """
    Calls the specified model via OpenRouter's unified /v1/chat/completions endpoint.
    Raises httpx.HTTPError or TimeoutException on failure to trigger fallback.
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not configured in the environment.")

    body = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt}
        ],
        "max_tokens": 120,
        "temperature": 0.1
    }
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(OPENROUTER_URL, headers=OPENROUTER_HEADERS, json=body)
        r.raise_for_status()
        data = r.json()
        
        # OpenRouter returns an OpenAI-compatible completion format
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
        else:
            raise KeyError("Malformed completion response from OpenRouter.")

def template_fallback(risk_score: float, shap_attrs: list, entity_type: str) -> str:
    """
    Deterministic offline fallback. No external API call required.
    Used when ALL OpenRouter model attempts fail (due to API issues, network down, etc.)
    """
    top = shap_attrs[0]["feature"].replace("_", " ") if len(shap_attrs) > 0 else "anomalous behavior"
    second = shap_attrs[1]["feature"].replace("_", " ") if len(shap_attrs) > 1 else "unusual access pattern"
    level = "HIGH" if risk_score >= 66 else "MEDIUM" if risk_score >= 31 else "LOW"
    return (
        f"This {entity_type} event is flagged at {level} risk (score: {risk_score:.0f}/100) "
        f"primarily driven by {top} and {second}. "
        f"Manual review is recommended before allowing this transaction to proceed."
    )

async def generate_explanation(risk_score: float, shap_attrs: list, entity_type: str) -> dict:
    """
    Main orchestration function. Evaluates models sequentially and falls back to
    the next model in the chain if any call fails, ending on a local template.
    """
    prompt = (
        f"Entity type: {entity_type}\n"
        f"Risk score: {risk_score:.1f}/100\n"
        f"Top contributing SHAP factors:\n{json.dumps(shap_attrs[:5], indent=2)}\n"
        f"Write a 2-sentence plain-language explanation for a bank compliance officer."
    )

    # Attempt API calls sequentially
    for model in MODELS:
        try:
            explanation = await call_openrouter(prompt, model["id"], model["timeout"])
            return {
                "explanation": explanation,
                "provider_used": model["label"],
                "fallback_used": False,
                "model_id": model["id"]
            }
        except Exception as e:
            print(f"[Setu/OpenRouter] {model['label']} failed: {e}. Trying next model...")
            continue

    # Fallback to the local deterministic template if all API endpoints fail
    explanation = template_fallback(risk_score, shap_attrs, entity_type)
    return {
        "explanation": explanation,
        "provider_used": "template",
        "fallback_used": True,
        "model_id": "template"
    }

# ==========================================
# FRICTION DECISION ENGINE
# ==========================================

def get_friction_action(risk_score: float) -> dict:
    """
    Evaluates policy rules and determines what action to take (pass, challenge, block)
    based on the numeric GNN risk score.
    """
    if risk_score <= 30:
        return {
            "action": "SILENT_PASS",
            "level": "LOW",
            "color": "green",
            "message": None,
            "route_to": None
        }
    elif risk_score <= 65:
        return {
            "action": "STEP_UP_AUTH",
            "level": "MEDIUM",
            "color": "amber",
            "message": "Additional verification required. Biometric or OTP prompt triggered.",
            "route_to": "FRAUD_MONITORING_QUEUE"
        }
    else:
        return {
            "action": "HARD_BLOCK",
            "level": "HIGH",
            "color": "red",
            "message": "Transaction blocked. Case file auto-routed to fraud desk.",
            "route_to": "FRAUD_INVESTIGATION_DESK"
        }

# ==========================================
# MOCK GNN SCORER
# ==========================================

def mock_score_event(event_data: dict) -> tuple[float, list]:
    """
    Mock Graph Neural Network (GNN) scorer that returns a risk score and SHAP
    feature attribution weights for model explainability.
    """
    score = 5.0
    attrs = []
    
    if event_data.get("sim_swap_flag"):
        score += 35
        attrs.append({"feature": "sim_swap_flag", "contribution": 0.38})
        
    if event_data.get("is_new_device"):
        score += 20
        attrs.append({"feature": "is_new_device", "contribution": 0.22})
        
    if event_data.get("geovelocity_jump_km", 0) > 500:
        score += 18
        attrs.append({"feature": "geovelocity_jump", "contribution": 0.19})
        
    if event_data.get("is_first_time_beneficiary"):
        score += 12
        attrs.append({"feature": "is_first_time_beneficiary", "contribution": 0.13})
        
    if event_data.get("outside_hours"):
        score += 22
        attrs.append({"feature": "outside_hours_access", "contribution": 0.24})
        
    if event_data.get("accounts_accessed_count", 0) >= 3:
        score += 25
        attrs.append({"feature": "bulk_account_access", "contribution": 0.28})
        
    # Introduce small random noise for realistic variability
    score = min(score + random.uniform(-3, 3), 100)
    score = max(score, 0.0)  # Bound at 0.0 minimum
    
    if not attrs:
        attrs = [{"feature": "behavioral_baseline_drift", "contribution": 0.05}]
        
    # Sort SHAP attributions by contribution magnitude descending
    attrs = sorted(attrs, key=lambda x: x["contribution"], reverse=True)
    
    return round(score, 1), attrs
