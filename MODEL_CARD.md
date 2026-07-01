# Setu — Model Card
## Model Details
- **Model Name:** SetuGNN (GraphSAGE-based Identity Risk Scorer)
- **Version:** setu-mock-v1.0
- **Type:** Graph Neural Network (GraphSAGE, 2-layer)
- **Framework:** PyTorch Geometric
- **Developed By:** Tejas Patel — CHARUSAT, Bank of Baroda Hackathon 2026
- **Last Updated:** July 2026

## Intended Use
- **Primary Use:** Real-time identity event risk scoring for banking fraud
  detection and insider threat prevention
- **Intended Users:** Bank fraud analysts, compliance officers, SOC teams
- **Out-of-Scope Uses:** Not intended for credit scoring, loan decisions,
  or any use case involving protected characteristics

## How It Works
Setu ingests identity events (customer sessions, employee access logs) as
nodes in a Neo4j heterogeneous graph. A GraphSAGE model aggregates
neighborhood signals across the graph and outputs a 0–100 risk score per
event. SHAP attributions explain which features drove each score. An LLM
layer (via OpenRouter: Llama → Gemini → GPT-4o-mini → template fallback)
converts SHAP values into plain-language compliance explanations.

## Input Features
| Feature | Description | Range |
|---|---|---|
| sim_swap_flag | SIM swap detected on this session | 0 or 1 |
| is_new_device | Device fingerprint not seen before | 0 or 1 |
| geovelocity_jump_km | Distance from last known location | 0–10,000 km |
| is_first_time_beneficiary | Transfer target never seen before | 0 or 1 |
| outside_hours | Access before 9am or after 7pm IST | 0 or 1 |
| accounts_accessed_count | Accounts accessed in last 60 min | 0–N |

## Output
| Output | Description |
|---|---|
| risk_score | 0–100 float. <30 = Low, 31–65 = Medium, >65 = High |
| shap_attributions | Top contributing features with signed contribution values |
| confidence | Model confidence: HIGH / MEDIUM / LOW with reasoning |
| action | SILENT_PASS / STEP_UP_AUTH / HARD_BLOCK |
| explanation | Plain-language LLM-generated compliance narrative |

## Training Data
- Synthetic graph seeded via seed_graph.py (Neo4j AuraDB)
- 300 legitimate sessions, 25 fraud scenarios, 15 insider threat scenarios
- Labels: LEGITIMATE (0), FRAUD or INSIDER (1)
- Note: Model is trained on synthetic data. Production deployment requires
  retraining on real bank event logs with appropriate data governance approvals.

## Performance (Synthetic Data)
- Target AUC: > 0.85
- Class imbalance handled via BCELoss class weighting
- All random seeds set to 42 for reproducibility

## Limitations & Honest Caveats
- Trained on synthetic data only — real-world performance will differ
- Mock scorer (rule-based heuristics) used when setu_gnn.pt is not loaded
- SHAP explanations are approximations, not ground truth causal attribution
- LLM explanations are bounded by SHAP inputs — model cannot fabricate reasons
- Confidence score is a heuristic estimate, not a calibrated probability

## Regulatory Compliance
| Framework | How Setu Addresses It |
|---|---|
| RBI FREE-AI — Explainability | SHAP attributions computed per event |
| RBI FREE-AI — Understandable by Design | LLM explanation grounded in SHAP only |
| RBI FREE-AI — Model Register | model_version field in /health endpoint |
| RBI FREE-AI — Grievance Redressal | False Positive / Confirm Fraud review UI |
| DPDP Act 2025 — Data Minimisation | No raw PII stored; feature vectors only |
| DPDP Act 2025 — Audit Trail | Every HARD_BLOCK logged in Supabase |
| RBI FREE-AI — AI Disclosure | provider_used returned in every API response |

## Grievance Redressal
Analysts can mark any decision as False Positive via the /live-feed UI.
All reviews are logged in the risk_events table with reviewer outcome.
For model-level disputes, contact the development team via GitHub Issues.

## License
MIT — See LICENSE file
