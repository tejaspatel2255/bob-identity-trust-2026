# Setu — Unified Identity Trust Graph & Fraud Prevention

**Setu** (meaning *Bridge* in Sanskrit) is a production-grade Unified Identity Trust Graph and real-time event ingestion platform built for the **Bank of Baroda 2026 Cybersecurity Hackathon** under the theme **Identity Trust & Fraud Prevention**.

The platform is designed to identify compromised user accounts, device takeover attempts, SIM-swap attacks, and internal staff compliance threats using high-performance graph representations in **Neo4j**, real-time ingestion and GNN scoring endpoints in **FastAPI**, and a cyber-themed interactive monitoring dashboard in **Next.js**.

---

## 🚀 Project Status & Features
- [x] **Phase 1**: Graph Schema & Uniqueness Constraints setup.
- [x] **Phase 2**: Synthetic Data Generator Seeding Script (`seed_graph.py`) with 300+ Customers, 25 Fraud scenarios, and 15 Insider threats.
- [x] **Phase 3**: Event Ingestion REST API (`FastAPI`, `Pydantic v2`, Parameterized Cypher Queries).
- [x] **Phase 4**: Explainability LLM Layer (Sequential fallbacks via OpenRouter: Llama 3.3 70B -> Gemini Flash -> GPT-4o-Mini -> local templates).
- [x] **Phase 5**: Next.js 14 Interactive Cybersecurity SOC Dashboard (featuring real-time incident streams, signal breakdown charts, and D3 force-directed topological subgraphs).
- [x] **Phase 6**: Compliance Mapping (`compliance_map.md`) & Automated Test Suite (`demo_runner.py`).

### 🌟 Phase 6+ Real-Time & Compliance Extensions
1. **Server-Sent Events (SSE) Live Feed**: The SOC Dashboard now connects via a reactive EventSource stream to `/stream/events` on the backend. Page polling is fully replaced; threats and simulation logs are pushed to the UI instantly without browser redraws.
2. **Model Confidence Scoring Engine**: Estimates the confidence (`HIGH`, `MEDIUM`, `LOW`) of risk predictions based on decision boundaries and SHAP attribution concentration. Badges are displayed in all event list items and audit pages.
3. **Random Threat Simulator**: A 4th simulation persona in `/personas` generating randomized cyber threat profiles (e.g. SIM swaps, impossible travels, bulk privilege queries) on the fly with dynamic payload parameters.
4. **Compliance Audit PDF Exports**: Zero-dependency PDF generation in `pdf_generator.py` serving printable, secure forensic case sheets directly from `/risk/events/{event_id}/pdf` in one click.

---

## 🛠️ Architecture & Folder Structure

```text
/bob-2026
│   .env.example        # Environment variable templates
│   .gitignore          # Secure file exclusion list (ignores secrets/builds/venvs)
│   requirements.txt    # Base python libraries (neo4j, python-dotenv, faker)
│   schema.md           # Formal database schema definition
│   seed_graph.py       # Batched Python seeder script for Neo4j database
│   demo_runner.py      # Automated terminal testing client for threat simulation
│   compliance_map.md   # Regulatory compliance matrix (RBI guidelines, SOC2, GDPR)
│   README.md           # Project documentation
│
├───backend/
│   │   db.py           # Neo4j Driver Connection Singleton & Session Context
│   │   explainer.py    # Mock GNN Scorer, confidence scorer, and OpenRouter LLM fallbacks
│   │   haversine.py    # Geovelocity calculation logic
│   │   main.py         # FastAPI router, SSE stream broadcaster, and REST endpoints
│   │   models.py       # Pydantic validation schemas
│   │   pdf_generator.py # Zero-dependency reportlab PDF generator
│   │   requirements.txt# FastAPI, Uvicorn, and ReportLab dependencies
│
└───frontend/
    │   package.json    # Next.js dependencies (react-force-graph-2d, recharts, lucide-react)
    │   tailwind.config.ts # Cyberpunk-themed color palettes and styles
    │
    ├───app/
    │   │   layout.tsx  # Root shell and design provider
    │   │   page.tsx    # Redirect handler to dashboard
    │   │   dashboard/  # Main operations view with SSE connection badge
    │   │   graph-view/ # Full global network topology analyzer
    │   │   personas/   # Threat sandbox featuring the Random Attack Generator
    │   │   cases/      # Forensic deep dive with PDF download controls
    │   │
    │   ├───components/ # Custom reusable components (GraphCanvas, Charts, Cards)
    │   └───lib/        # API client helpers, Types, and SSE custom hooks
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

Ensure Python 3.11+ and Node.js 18+ are installed.

### 1. Clone & Set Up Backend Environment
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

# Optional: Add OpenRouter API key for live LLM explanations
OPENROUTER_API_KEY=your-openrouter-key
```

Copy the `.env` file to the backend:
```bash
# Windows PowerShell
copy .env backend\.env

# macOS/Linux
# cp .env backend/.env
```

### 3. Install Backend Requirements & Seed Database
```bash
# Install core packages
pip install -r requirements.txt

# Run the seeding script to populate Neo4j with simulation patterns
python seed_graph.py
```

### 4. Start the FastAPI API Server
```bash
# Install server runtime dependencies
pip install -r backend/requirements.txt

# Start the uvicorn dev server on port 8000
python -m uvicorn backend.main:app --reload --port 8000
```
Open **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** to inspect the interactive Swagger API documentation.

### 5. Start the Next.js Frontend
Open a new terminal window:
```bash
cd frontend

# Install package dependencies
npm install

# Run the Next.js local development server
npm run dev
```

Open **[http://localhost:3000/dashboard](http://localhost:3000/dashboard)** in your browser to view the live cybersecurity operations dashboard!

---

## 🛡️ Core Demo Features
1. **Threat Simulation Sandbox** (`/personas`): Trigger real-time transaction ingestion vectors. Includes default personas (Priya, Ramesh, Attacker) and the **Random Threat Generator** to spawn infinite customized vectors.
2. **Operations Dashboard** (`/dashboard`): Monitor active incident feeds, radar vector breakdowns, and Neo4j database health metrics. Runs entirely over Server-Sent Events for instant reactive updates.
3. **Forensic Investigator** (`/cases/[id]`): Drill down into a specific flagged customer or staff member. Features dynamic topological visualization to trace multi-hop fraud paths, custom confidence markers, and **One-Click Audit PDF download**.
4. **Global Graph Analyzer** (`/graph-view`): Interactive visualization of the entire identity trust graph.
5. **Command Line Demo Script** (`demo_runner.py`): Test the threat calculation engine directly from your terminal. Run `python demo_runner.py` to trigger parallel requests to the API.
