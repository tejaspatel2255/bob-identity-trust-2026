"""
Setu Demo Runner — fires all 3 personas against the live API and prints results.
Usage: python demo_runner.py
Requires: pip install httpx python-dotenv
"""
import httpx, asyncio, json, time, os
from pathlib import Path
from dotenv import load_dotenv

_env = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_env)
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

PERSONAS = [
    {
        "name": "Priya Sharma",
        "label": "LEGITIMATE CUSTOMER",
        "payload": {
            "entity_type": "CUSTOMER_SESSION",
            "entity_id": "CUST_PRIYA_001",
            "event_data": {
                "sim_swap_flag": False,
                "is_new_device": False,
                "geovelocity_jump_km": 8,
                "is_first_time_beneficiary": False,
                "outside_hours": False,
                "accounts_accessed_count": 0
            }
        },
        "expected": "< 30"
    },
    {
        "name": "Unknown Attacker",
        "label": "SIM-SWAP FRAUD",
        "payload": {
            "entity_type": "CUSTOMER_SESSION",
            "entity_id": "CUST_ATK_9921",
            "event_data": {
                "sim_swap_flag": True,
                "is_new_device": True,
                "geovelocity_jump_km": 1247,
                "is_first_time_beneficiary": True,
                "outside_hours": False,
                "accounts_accessed_count": 0
            }
        },
        "expected": "> 70"
    },
    {
        "name": "Ramesh Patel, Branch Officer",
        "label": "INSIDER THREAT",
        "payload": {
            "entity_type": "EMPLOYEE_ACCESS",
            "entity_id": "EMP_RP_0042",
            "event_data": {
                "sim_swap_flag": False,
                "is_new_device": False,
                "geovelocity_jump_km": 0,
                "is_first_time_beneficiary": False,
                "outside_hours": True,
                "accounts_accessed_count": 4
            }
        },
        "expected": "> 65"
    }
]

async def run_persona(p: dict):
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    RESET  = "\033[0m"
    BOLD   = "\033[1m"

    print(f"\n{'='*62}")
    print(f"  {BOLD}{p['label']}: {p['name']}{RESET}")
    print(f"  Expected score: {p['expected']}")
    print(f"{'='*62}")

    t0 = time.time()
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            r = await client.post(f"{API_BASE}/risk/score", json=p["payload"])
            r.raise_for_status()
            d = r.json()
            ms = int((time.time() - t0) * 1000)
            score = d.get("risk_score", 0)
            color = GREEN if score < 31 else YELLOW if score < 66 else RED
            print(f"  Risk Score  : {color}{BOLD}{score:.1f}/100{RESET}")
            print(f"  Level       : {d.get('action', {}).get('level', '?')}")
            print(f"  Action      : {d.get('action', {}).get('action', '?')}")
            print(f"  Provider    : {d.get('provider_used', '?')}")
            print(f"  Explanation : {d.get('explanation', 'N/A')}")
            print(f"  Response    : {ms}ms")
        except Exception as e:
            print(f"  ERROR: {e}")
            print(f"  Make sure backend is running at {API_BASE}")

async def main():
    print(f"\n{'='*62}")
    print(f"  SETU IDENTITY TRUST GRAPH — DEMO RUNNER")
    print(f"  API Target: {API_BASE}")
    print(f"{'='*62}")
    for p in PERSONAS:
        await run_persona(p)
        await asyncio.sleep(2)
    print(f"\n{'='*62}")
    print("  All 3 personas complete.")
    print("  Open http://localhost:3000/personas for the UI demo.")
    print(f"{'='*62}\n")

if __name__ == "__main__":
    asyncio.run(main())
