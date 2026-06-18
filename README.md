# Setu — Unified Identity Trust Graph & Fraud Prevention

**Setu** (meaning *Bridge* in Sanskrit) is a production-grade Unified Identity Trust Graph and real-time event ingestion platform built for the **Bank of Baroda 2026 Cybersecurity Hackathon** under the theme **Identity Trust & Fraud Prevention**.

The platform is designed to identify compromised user accounts, device takeover attempts, SIM-swap attacks, and internal staff compliance threats using high-performance graph representations in **Neo4j** and real-time ingestion endpoints in **FastAPI**.

---

## 🚀 Project Status
- [x] **Phase 1**: Graph Schema & Uniqueness Constraints setup.
- [x] **Phase 1**: Synthetic Data Generator Seeding Script (`seed_graph.py`) with 300+ Customers, 25 Fraud scenarios, and 15 Insider threats.
- [x] **Phase 2**: Event Ingestion REST API (`FastAPI`, `Pydantic v2`, Parameterized Cypher Queries, CORS enabled).
- [ ] **Phase 4**: Explainability LLM Layer (Groq → Gemini → OpenAI Fallback). *(Next)*
- [ ] **Phase 5**: Next.js Cyber-themed Interactive Dashboard.

---

## 🛠️ Architecture & Folder Structure

```text
/bob-2026
│   .env.example        # Env configuration template for Neo4j database
│   .gitignore          # Secure file exclusion list (ignores secrets/venvs)
│   requirements.txt    # Base python libraries (neo4j, python-dotenv, faker)
│   schema.md           # Formal database schema definition in markdown table
│   seed_graph.py       # Batched Python seeder script for Neo4j database
│   README.md           # Project documentation
│
└───backend/
    │   .env.example    # Configuration template for the backend server
    │   db.py           # Neo4j Driver Connection Singleton & Session Context
    │   Dockerfile      # Container build instructions for Railway/Render
    │   haversine.py    # Geovelocity calculation logic (earth-surface distance)
    │   main.py         # FastAPI router, real-time rules, and error handlers
    │   models.py       # Pydantic validation schemas
    │   requirements.txt# FastAPI and Uvicorn runtime dependencies
```

---

## 🗄️ Graph Database Schema

### 1. Nodes
- **`Customer`**: `{ id, name, risk_baseline, onboarding_aadhaar_verified, account_age_days }`
- **`Device`**: `{ fingerprint, os, browser, is_new, trust_score }`
- **`Session`**: `{ id, timestamp, ip, city, geolocation_lat, geolocation_lng, duration_seconds, sim_swap_flag, label }`
- **`Employee`**: `{ id, name, role, access_level, department, label }`
- **`Account`**: `{ id, balance_tier, account_type, is_frozen }`
- **`Beneficiary`**: `{ id, bank_ifsc, is_first_time, amount }`

### 2. Relationships
- `(Customer)-[:OWNS]->(Account)`
- `(Customer)-[:LOGGED_IN_FROM { timestamp }]->(Device)`
- `(Customer)-[:INITIATED { timestamp }]->(Session)`
- `(Session)-[:USED_DEVICE { geovelocity_jump_km }]->(Device)`
- `(Session)-[:TRANSFERRED_TO { amount, timestamp }]->(Beneficiary)`
- `(Employee)-[:ACCESSED { timestamp, action_type, outside_hours }]->(Account)`
- `(Employee)-[:VIEWED_KYC { timestamp }]->(Customer)`
- `(Account)-[:RECOVERY_ATTEMPTED { timestamp, new_device }]->(Customer)`

Detailed properties and constraints are documented in [schema.md](./schema.md).

---

## ⚙️ Quick Setup & Run Instructions

Ensure Python 3.11+ is installed.

### 1. Clone & Set Up Virtual Environment
```bash
# Clone the repository
git clone <your-repository-url>
cd bob-2026

# Create and activate Python virtual environment
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On macOS/Linux:
# source .venv/bin/activate
```

### 2. Credentials Configuration
Create a `.env` file in the root directory:
```env
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

Copy the configuration to the backend server directory:
```bash
# Windows PowerShell
copy .env backend\.env

# macOS/Linux
# cp .env backend/.env
```

### 3. Install Requirements & Seed Database
```bash
# Install core packages
pip install -r requirements.txt

# Run the seeding script
python seed_graph.py
```

### 4. Start the FastAPI API Server
```bash
# Install server runtime dependencies
pip install -r backend/requirements.txt

# Start the uvicorn dev server
uvicorn backend.main:app --reload --port 8000
```
Open **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** in your browser to inspect and trigger the event ingestion endpoints interactively!
