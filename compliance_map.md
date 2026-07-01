# Setu — Regulatory Compliance Mapping

| Framework | Requirement | Setu Component | File |
|---|---|---|---|
| RBI FREE-AI | Explainability tools (SHAP/LIME mandatory) | SHAP attribution computed per event | explainer.py |
| RBI FREE-AI | Understandable by Design — no black-box decisions | LLM explanation grounded in SHAP only; system prompt forbids fabrication | explainer.py → generate_explanation() |
| RBI FREE-AI | Model register / lineage / traceability | model_version in /health; norm_params.json from Colab | main.py, setu_gnn_train.ipynb |
| RBI FREE-AI | Grievance redressal channel | False Positive / Confirm Fraud buttons in /live-feed; PATCH /risk/events/:id | live-feed/page.tsx, main.py |
| RBI Revised Fraud Framework | AI-driven mule detection | Mule flags ingestable as graph edges; upstream compatible with MuleHunter.AI | seed_graph.py, main.py |
| DPDP Act 2025 | Reasonable security safeguards | No raw biometrics stored; only normalized feature vectors | main.py (all endpoints) |
| DPDP Act 2025 | Data minimisation | Only embeddings stored; no raw PII in risk_events table | db.py, models.py |
| UIDAI Aadhaar | e-KYC compliance | Aadhaar outcome consumed as onboarding_aadhaar_verified on Customer node | seed_graph.py |
| DPDP Act 2025 | Breach audit trail | Every HARD_BLOCK generates explanation + audit row in Supabase | explainer.py, main.py |
| RBI FREE-AI | AI disclosure to consumer | provider_used returned in every API response; shown in UI as "Explained by: Llama" | explainer.py, EventCard.tsx |
