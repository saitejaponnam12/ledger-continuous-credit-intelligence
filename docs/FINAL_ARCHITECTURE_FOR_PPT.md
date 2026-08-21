# LEDGER — FINAL SYSTEM ARCHITECTURE SPECIFICATION
**One Synchrony Campus Hackathon • Release Candidate 1.0**
*Complete, fact-checked architectural documentation for the final presentation deck (PPT/PDF).*

---

## 1. EXECUTIVE ARCHITECTURE OVERVIEW

LEDGER is architected as an **event-driven, explainable credit intelligence platform**. It replaces static, one-time credit bureau snapshots with a continuous **Financial Twin** that updates in real time as alternative financial evidence and behavioral signals arrive.

```
                                  APPLICANT / UNDERWRITER
                                             │
                                             ▼
                        ┌───────────────────────────────────────────┐
                        │      REACT UNDERWRITING CONSOLE           │
                        │   • Command Center  • Case Workbench      │
                        │   • Financial Twin  • What Changed?       │
                        └────────────────────┬──────────────────────┘
                                             │
                                             ▼
                        ┌───────────────────────────────────────────┐
                        │       FASTAPI ASYNCHRONOUS API LAYER      │
                        │   • JWT Auth / RBAC • WebSocket Stream    │
                        │   • REST Endpoints  • Audit Logging       │
                        └─────────┬───────────────────────┬─────────┘
                                  │                       │
                    ┌─────────────▼────────────┐    ┌─────▼────────────────────┐
                    │  MULTIMODAL EVIDENCE     │    │   BOUNDED RAG COPILOT    │
                    │  • PDF / Image / CSV     │    │   • Policy Retrieval     │
                    │  • Local OCR Extraction  │    │   • Read-Only Tools      │
                    │  • Entity Validation     │    │   • Grounded Explainer   │
                    └─────────────┬────────────┘    └─────▲────────────────────┘
                                  │                       │
                                  ▼                       │ (Context Citing)
                    ┌──────────────────────────┐          │
                    │ 12-FEATURE CASHFLOW PIPELINE        │
                    └─────────────┬────────────┘          │
                                  │                       │
                                  ▼                       │
                    ┌──────────────────────────┐          │
                    │  XGBOOST + CALIBRATION   │          │
                    │  • Calibrated Default P  │          │
                    │  • SHAP TreeExplainer    │──────────┘
                    └─────────────┬────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  CREDIT PATHWAY ENGINE   │
                    │  (Deterministic Rules)   │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │      FINANCIAL TWIN      │
                    │  Continuous Trajectory   │
                    └──────────────────────────┘
```

---

## 2. LAYERED ARCHITECTURE

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              LEDGER 6-LAYER ARCHITECTURE                               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  LAYER 1: PRESENTATION & INTERACTION (React 19 + TypeScript + Vite 8)                  │
│  ├── Executive Command Center (/dashboard) — Portfolio aggregates & anomaly alerts     │
│  ├── Underwriter Case Workbench (/applications) — Real-time search & case triage       │
│  ├── Financial Twin Intelligence Console (/applications/:id) — Radar & trajectory     │
│  └── 7 Signature Interaction Panels: Multimodal, What Changed, NBE, CF, Copilot, Audit │
│                                                                                        │
│  LAYER 2: API ROUTING, AUTHENTICATION & RBAC (FastAPI + JWT + passlib)                 │
│  ├── Stateless HS256 JWT tokens & salted bcrypt password hashing                       │
│  ├── Role-Based Access Control: Underwriter (Sarah Chen) vs Demo Admin (Admin)         │
│  └── RESTful endpoints (/api/v1/applications, /events, /copilot, /demo)                │
│                                                                                        │
│  LAYER 3: MULTIMODAL DOCUMENT INTELLIGENCE (Local Python OCR)                          │
│  ├── 5-Step Pipeline: Ingestion ──► Classification ──► Layout OCR ──► Entity ──► Check│
│  └── Local parsers: pdfplumber, pytesseract, regex entity extractors (zero cloud APIs) │
│                                                                                        │
│  LAYER 4: CASHFLOW & BEHAVIORAL FEATURE ENGINEERING (12-Feature Pipeline)              │
│  ├── Computes 12 mathematically defensible cashflow and volatility metrics            │
│  └── Evaluates Data Completeness Score (0.0 to 1.0) to model epistemic uncertainty    │
│                                                                                        │
│  LAYER 5: DETERMINISTIC DECISION & EXPLAINABILITY ENGINE (XGBoost + SHAP)              │
│  ├── 12-Tree XGBoost Base Classifier with CalibratedClassifierCV (Isotonic)           │
│  ├── shap.TreeExplainer exact Shapley attribution & delta calculations                │
│  └── Deterministic Credit Pathway Rule Engine (Full, Conditional, Request Evidence)   │
│                                                                                        │
│  LAYER 6: DATA PERSISTENCE & BOUNDED RAG (SQLAlchemy 2.0 Async + sentence-transformers)│
│  ├── Relational schema: Users, Customers, Applications, Accounts, Txns, RiskScores    │
│  ├── Append-only audit events ledger recording actor, timestamp, payload hash, version │
│  └── Dense vector policy search (all-MiniLM-L6-v2) feeding read-only Copilot tools    │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. END-TO-END DATA FLOW (THE 20-STEP HERO SEQUENCE)

```
[Applicant / Thin-File Profile Ingestion]
        │
        ▼ (Step 1-3)
[Sparse Baseline Data: 1 Month History] ──► [compute_features(): Completeness = 35%]
        │
        ▼ (Step 4-7)
[XGBoost Rescore: 11.0% Risk] ──► [Rule 2: Low Completeness] ──► [Pathway: REQUEST_EVIDENCE]
        │
        ▼ (Step 8-13)
[Upload 6M Bank Statement PDF] ──► [5-Step Local OCR Engine] ──► [Extracted: Salary ₹64,820, 24 Txns]
        │
        ▼ (Step 14-16)
[Incorporate into Twin] ──► [Completeness Jumps 35% ──► 85%] ──► [Confidence Rises 56.5% ──► 78.0%]
        │
        ▼ (Step 17-18)
[Rule 5: Verified Low Risk] ──► [Pathway Promotes: CONDITIONAL_APPROVAL (₹50,000 Limit)]
        │
        ▼ (Step 19-20)
[What Changed? 7-Stage Animation] ──► [TreeExplainer SHAP Δ Waterfall] ──► [RAG Copilot Explains]
```

---

## 4. COMPONENT RESPONSIBILITIES MATRIX

| Component Name | Source Code Module | Primary Architectural Responsibility | Deterministic vs AI |
|---|---|---|:---:|
| **Underwriting Console** | `frontend/src/` | Interactive state visualization, trajectory charts, and case triage | UI / Presentation |
| **API Router & Auth** | `backend/app/api/`, `core/security.py` | Request routing, JWT validation, and RBAC permission enforcement | Deterministic |
| **Multimodal Extractor** | `backend/app/api/applications.py` | Local PDF/image layout OCR, regex entity parsing, and checksum balance check | Deterministic |
| **Feature Engineer** | `backend/app/ml/feature_engineering.py` | Derives 12 cashflow features and data completeness score from raw txns | Deterministic |
| **Risk Classifier** | `backend/app/ml/` (Trained Model) | XGBoost ensemble + Isotonic calibration estimating $P(\text{default})$ | Deterministic ML |
| **SHAP Explainer** | `backend/app/ml/shap_utils.py` | Computes exact mathematical Shapley values ($\phi_i$) and delta vectors ($\Delta \text{SHAP}$) | Deterministic Math |
| **Credit Pathway Engine**| `backend/app/ml/pathway_engine.py` | Applies policy rules to assign pathways and dynamic exposure limits | Deterministic Rules |
| **WebSocket Engine** | `backend/app/events/websocket_manager.py` | Broadcasts real-time twin updates to connected underwriter browser clients | Real-time Streaming |
| **RAG Policy Retriever** | `backend/app/rag/retriever.py` | Semantic vector search retrieving relevant underwriting policy sections | Dense Retrieval |
| **AI Copilot** | `backend/app/copilot/` | Synthesizes retrieved policy chunks and read-only model context into natural language | Bounded LLM / Mock |
| **Audit Ledger** | `backend/app/models/models.py` | Append-only immutable log of all underwriting and system actions | Audit & Governance |

---

## 5. FRONTEND ARCHITECTURE

### Technology & Libraries
- **Framework**: React 19.2.8 with TypeScript 6.0.2
- **Build Engine**: Vite 8.2.2 (ESM, sub-second HMR)
- **Styling**: TailwindCSS 4.3.3 (Custom dark FinTech glassmorphism design tokens)
- **Animation**: Framer Motion 13.1.0 (7-stage causal state machine micro-animations)
- **Data Visualization**: Recharts 3.10.1 (Multi-point Risk Trajectory, 6-Dimension Radar Chart)
- **State Management**: Zustand 5.0.15 (`authStore.ts` for JWT tokens & role persistence)
- **HTTP & WS Clients**: Axios 1.19.0 with JWT interceptors + native browser WebSocket API

### Major Product Surfaces
1. **Executive Command Center (`/dashboard`)**:
   - Portfolio-level intelligence: 4 top KPI cards, Credit Pathway Allocation progress bars, Risk Band breakdown, Anomaly alert feed.
2. **Underwriter Case Workbench (`/applications`)**:
   - Case triage workbench: Real-time search bar, pathway filter pills, persona tags, calibrated risk/confidence meters, direct `Open Twin →` CTA.
3. **Financial Twin Intelligence Console (`/applications/:id`)**:
   - Persistent Twin State: 6-Dimension Financial Health Radar, calibrated default gauge, single-point baseline / multi-point evolution trajectory.
   - Contextual Deep-Dive Panels:
     - **Multimodal Evidence**: Document dropzone, 5-step local OCR progress stepper, and structured entity viewer.
     - **What Changed?**: 7-stage causal sequence animation with real before/after metrics and TreeExplainer SHAP delta waterfall.
     - **What Would Change My Mind?**: Ranked Next-Best-Evidence recommendations with expected uncertainty reduction.
     - **Counterfactual Simulator**: Interactive parameter sliders with real-time trajectory fork simulation.
     - **RAG AI Copilot**: Grounded chat interface displaying executed tool calls and policy citations.
     - **Evidence Network**: Relational entity graph connecting applicant, employers, accounts, and flows.
     - **Responsible AI & Audit Trail**: Governance disclaimers and append-only immutable event history.
4. **Admin Demo Control Panel (`/demo`)**:
   - Scenario reset triggers (`Scenario A` through `E`), bulk scenario seeding, and simulated event triggers.

---

## 6. BACKEND & API ARCHITECTURE

### Framework & Core Services
- **Framework**: FastAPI (Async Python 3.11+) on Uvicorn ASGI server.
- **Data Validation**: Pydantic v2 with strict type schemas and custom field validators.
- **ORM & Database**: SQLAlchemy 2.0 AsyncEngine with `async_sessionmaker`.

### API Route Mapping

| HTTP Method | API Route Path | Controller / Service | Primary Function |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | `api/auth.py` | Issues stateless HS256 JWT access token upon credential verification |
| `GET` | `/api/v1/auth/me` | `api/auth.py` | Returns authenticated user profile and RBAC role |
| `GET` | `/api/v1/applications` | `api/applications.py` | Returns paginated applications list with latest risk scores and pathways |
| `GET` | `/api/v1/applications/{id}` | `api/applications.py` | Fetches complete Financial Twin state, customer profile, and accounts |
| `POST` | `/api/v1/applications/{id}/analyze` | `api/applications.py` | Runs feature engineering, XGBoost, SHAP, and pathway evaluation |
| `GET` | `/api/v1/applications/{id}/risk` | `api/applications.py` | Returns historical risk trajectory observations (Point 1 $\rightarrow$ Point N) |
| `GET` | `/api/v1/applications/{id}/explanation` | `api/applications.py` | Returns top positive/negative SHAP drivers and TreeExplainer deltas |
| `GET` | `/api/v1/applications/{id}/next-best-evidence` | `api/applications.py` | Evaluates missing features and returns ranked uncertainty reduction |
| `POST` | `/api/v1/applications/{id}/counterfactual` | `api/applications.py` | Runs what-if simulation without mutating persisted database records |
| `POST` | `/api/v1/applications/{id}/documents/upload` | `api/applications.py` | Ingests PDF/image, runs local OCR, and extracts structured entities |
| `POST` | `/api/v1/applications/{id}/documents/{doc_id}/incorporate` | `api/applications.py` | Incorporates verified document transactions and re-scores Twin |
| `POST` | `/api/v1/events/simulate` | `api/events.py` | Ingests financial event, recomputes twin, and broadcasts via WebSocket |
| `WS` | `/api/v1/events/ws/{app_id}` | `api/events.py` | WebSocket streaming endpoint for live Financial Twin updates |
| `POST` | `/api/v1/copilot/query` | `api/copilot.py` | Executes grounded RAG search and read-only tools for decision explanation |
| `POST` | `/api/v1/demo/reset/{scenario}` | `api/demo.py` | Resets demo persona (e.g. Scenario A Ananya) to canonical baseline |
| `GET` | `/api/v1/demo/status` | `api/demo.py` | Returns portfolio status of all active demo scenarios |

---

## 7. DATABASE & PERSISTENCE ARCHITECTURE

```
┌──────────────────┐           ┌──────────────────┐           ┌──────────────────┐
│      users       │           │    customers     │           │   applications   │
├──────────────────┤           ├──────────────────┤           ├──────────────────┤
│ id (PK)          │           │ id (PK)          │◄──────────┤ id (PK)          │
│ email (UQ)       │           │ display_name     │           │ customer_id (FK) │
│ hashed_password  │           │ persona_tag      │           │ status           │
│ role (underwriter│           │ age              │           │ consent_given    │
│      /admin)     │           │ city             │           │ created_at       │
└──────────────────┘           └────────┬─────────┘           └────────┬─────────┘
                                        │                              │
                                        │                              │
                                        ▼                              ▼
                               ┌──────────────────┐           ┌──────────────────┐
                               │financial_accounts│           │   risk_scores    │
                               ├──────────────────┤           ├──────────────────┤
                               │ id (PK)          │           │ id (PK)          │
                               │ customer_id (FK) │           │ application_id(FK│
                               │ account_type     │           │ risk_probability │
                               │ opened_at        │           │ confidence       │
                               └────────┬─────────┘           │ shap_values JSON │
                                        │                     │ 6 twin dimensions│
                                        │                     └──────────────────┘
                                        ▼                              │
                               ┌──────────────────┐                    ▼
                               │   transactions   │           ┌──────────────────┐
                               ├──────────────────┤           │    decisions     │
                               │ id (PK)          │           ├──────────────────┤
                               │ account_id (FK)  │           │ id (PK)          │
                               │ amount           │           │ application_id(FK│
                               │ direction        │           │ pathway          │
                               │ category         │           │ exposure_limit   │
                               │ occurred_at      │           │ monitoring_days  │
                               └──────────────────┘           └──────────────────┘
```

### Additional Relational Entities:
- **`documents`**: Stores uploaded PDF/image metadata, OCR extraction JSON, and validation confidence.
- **`fraud_signals`**: Stores behavioral anomaly flags, severity levels, and detection timestamps.
- **`policy_documents` & `policy_chunks`**: Stores raw underwriting text and dense vector embeddings (`embedding: list[float]`).
- **`audit_events`**: Immutable append-only log recording actor, action, timestamp, and payload metadata.
- **`copilot_interactions`**: Stores user queries, grounded prompts, retrieved citations, and tool call logs.

---

## 8. MACHINE LEARNING DECISION ENGINE

```
Raw Transactions / Verified Document Entities
                     │
                     ▼
       ┌───────────────────────────┐
       │   feature_engineering.py  │ ──► Generates 12-Dimensional Vector X
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │   XGBoost Base Ensemble   │ ──► Computes Raw Margin Scores
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │   Isotonic Calibration    │ ──► Maps Scores to Calibrated Default Probability P
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │    shap.TreeExplainer     │ ──► Generates Exact Shapley Attributions (phi_i)
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │   pathway_engine.py       │ ──► Evaluates Deterministic Policy Rules
       └─────────────┬─────────────┘
                     │
                     ▼
        Final Credit Pathway & Exposure Limit
```

### The 12 Mathematically Defined Features:
1. `income_consistency`: Monthly income stability ($1 - \text{CV}_{\text{income}}$).
2. `expense_ratio`: Operating leverage ($\sum \text{Debits} / \sum \text{Credits}$).
3. `cashflow_stability`: Minimum monthly net balance normalized by average.
4. `payment_regularity`: Proportion of active months with regular recurring payments.
5. `balance_volatility`: Rolling standard deviation of daily balance.
6. `recurring_payment_count`: Normalized count of recurring merchant commitments.
7. `days_since_last_payment`: Recency of outflow activity.
8. `liquidity_ratio`: Months of average balance reserve over monthly expenses.
9. `debt_to_income`: Recurring debt/EMI obligations over verified income.
10. `transaction_velocity`: Normalized 30-day transaction frequency.
11. `account_age_months`: Normalized banking relationship duration.
12. `income_sources_count`: Inflow revenue stream diversification.

### Deterministic Pathway Rules:
- **Rule 1 (Fraud Override)**: High-severity anomaly signal $\rightarrow$ **`HUMAN_REVIEW`**.
- **Rule 2 (Thin-File Gate)**: Confidence $< 60\%$ or completeness $< 50\%$ $\rightarrow$ **`REQUEST_EVIDENCE`**.
- **Rule 3 (High Default Risk)**: Calibrated risk $> 68\%$ $\rightarrow$ **`TRANSPARENT_DECLINE`**.
- **Rule 4 (Ambiguous Risk)**: Risk $48\%\text{–}68\%$ with medium confidence $\rightarrow$ **`HUMAN_REVIEW`**.
- **Rule 5 (Verified Low Risk)**: Risk $< 40\%$ with confidence $\ge 60\%$ $\rightarrow$ **`CONDITIONAL_APPROVAL`** (₹50,000 limit, 60-day monitoring).
- **Rule 6 (Prime Profile)**: Risk $< 22\%$ with high confidence $\rightarrow$ **`FULL_APPROVAL`** (₹100,000 limit, 90-day monitoring).

---

## 9. MULTIMODAL EVIDENCE INGESTION ARCHITECTURE

```
[PDF Bank Statement / PNG Receipt / CSV]
                     │
                     ▼
        ┌───────────────────────────┐
        │   Step 1: Ingestion       │ ──► MIME Type & SHA-256 Checksum Verification
        └────────────┬──────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │   Step 2: Classification  │ ──► Layout Heuristic: Type = bank_statement (95% Conf)
        └────────────┬──────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │   Step 3: Layout OCR      │ ──► pdfplumber / pytesseract Table Text Parsing
        └────────────┬──────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │   Step 4: Entity Parser   │ ──► Regex Extractors: Salary ₹64,820, 24 Txns, EMI
        └────────────┬──────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │   Step 5: Validation      │ ──► Balance Reconciler: Inflows - Outflows = Net (94% Conf)
        └────────────┬──────────────┘
                     │
                     ▼
         Twin State Incorporation & Rescoring
```

*Note: All document parsing runs completely locally in Python using `pdfplumber` and `pytesseract`. No cloud OCR APIs are required for the prototype.*

---

## 10. REAL-TIME EVENT STREAMING ARCHITECTURE

```
[Simulated Event: POST /events/simulate]
                     │
                     ▼
        ┌───────────────────────────┐
        │   Transaction Ingestion   │ ──► Inserts Record into transactions Table
        └────────────┬──────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │   Feature Recalculation   │ ──► compute_features() on Enriched History (<10ms)
        └────────────┬──────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │   XGBoost + SHAP Rescore  │ ──► Calibrated Probability & Shapley Deltas (<20ms)
        └────────────┬──────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │   Credit Pathway Update   │ ──► Deterministic Rule Evaluation (<1ms)
        └────────────┬──────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │   ConnectionManager       │ ──► Broadcasts twin_updated Payload over WebSockets
        └────────────┬──────────────┘
                     │
                     ▼
       [React UI: Live Twin State Update & 7-Stage Causal Animation]
```

---

## 11. RAG & AI COPILOT ARCHITECTURE

```
Underwriting Policy Manuals (Policy P-15)
                     │
                     ▼
        ┌───────────────────────────┐
        │   Sentence Transformers   │ ──► all-MiniLM-L6-v2 Dense Embeddings
        └────────────┬──────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │   Vector Retrieval        │ ──► Cosine Similarity Search (Top-K Policy Chunks)
        └────────────┬──────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │   Bounded Read-Only Tools │ ──► get_customer_profile(), get_model_explanation()
        └────────────┬──────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │   Grounded Prompt Builder │ ──► Injects Model Values & Retrieved Policy Text
        └────────────┬──────────────┘
                     │
                     ▼
        ┌───────────────────────────┐
        │   Local LLM / MockProvider│ ──► Generates Natural Language Decision Explanation
        └───────────────────────────┘
```

### Bounded Read-Only Tools (Tools Cannot Mutate State):
- `get_customer_profile(application_id)`: Fetches verified demographics and persona tags.
- `get_financial_evidence(application_id)`: Fetches extracted document entities and cashflows.
- `get_model_explanation(application_id)`: Fetches exact SHAP contributions and rank order.
- `get_credit_pathway(application_id)`: Fetches current deterministic pathway and limits.
- `get_uncertainty(application_id)`: Fetches confidence score and missing data flags.
- `get_next_best_evidence(application_id)`: Fetches ranked uncertainty reduction estimates.
- `get_recent_events(application_id)`: Fetches transaction timeline and anomaly signals.

---

## 12. RESPONSIBLE AI & DECISION BOUNDARY

```
┌─────────────────────────────────────────┬─────────────────────────────────────────┐
│     AUTHORITATIVE DECISION ENGINE       │          AI EXPLANATION COPILOT         │
│          (100% DETERMINISTIC)           │           (READ-ONLY / BOUNDED)         │
├─────────────────────────────────────────┼─────────────────────────────────────────┤
│ • 12-Feature Cashflow Engine            │ • Sentence-Transformers Policy Search   │
│ • Calibrated XGBoost Probability Model  │ • Underwriting Manual (Policy P-15)     │
│ • Mathematical SHAP TreeExplainer       │ • Read-Only Model & Evidence Tools      │
│ • Deterministic Pathway Policy Rules    │ • Natural Language Explanation & Chat   │
│                                         │                                         │
│   ► DETERMINES RISK & CREDIT LIMIT ◄    │       ► EXPLAINS — NEVER DECIDES ◄      │
└─────────────────────────────────────────┴─────────────────────────────────────────┘
```

---

## 13. SECURITY ARCHITECTURE

```
User (Browser Client)
        │
        ▼
[HTTP Request with Bearer JWT (HS256)]
        │
        ▼
[FastAPI Security Dependency: get_current_user]
        │
        ├──► Validates Signature & Expiration
        ├──► Checks Revocation & User Identity
        │
        ▼
[RBAC Authorization Guards]
        │
        ├──► require_underwriter: Case Triage, Twin Inspection, Evidence Upload
        └──► require_demo_admin: Scenario Reset, Bulk Seeding, Demo Panel
        │
        ▼
[Executed Authorized Controller] ──► [Records Immutable Entry in audit_events]
```

---

## 14. AUDIT & GOVERNANCE ARCHITECTURE

The `audit_events` table maintains an immutable, append-only chronological log of all underwriting and system actions:

| Logged Field | Description / Audit Purpose | Example Value |
|---|---|---|
| `id` | Unique UUID primary key | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `application_id`| Referenced applicant case | `ba8cbaeb-d0d7-469c-8d4a-45acaa33cabc` |
| `actor` | Email / Identity of user initiating action | `sarah.chen@ledger.demo` |
| `action` | Standardized audit action verb | `document_incorporated` |
| `payload` | Full JSON state snapshot & feature deltas | `{"doc_id": "...", "pathway_promoted": true}` |
| `model_version` | Model version at execution time | `xgb-credit-v1.0` |
| `created_at` | UTC ISO-8601 timestamp | `2026-08-21T10:02:35.123Z` |

---

## 15. PROTOTYPE VS. PRODUCTION EVOLUTION ARCHITECTURE

| Architecture Layer | Current Hackathon Prototype (Verified) | Future Production Evolution (Conceptual AWS) |
|---|---|---|
| **Frontend Delivery** | Local Vite Dev Server (`localhost:5173`) | Next.js on AWS CloudFront Edge + S3 |
| **API Layer** | Local FastAPI on Uvicorn (`localhost:8000`) | AWS ECS / EKS Microservices with ALB |
| **Relational Database** | Local SQLite / PostgreSQL via SQLAlchemy Async | AWS Aurora PostgreSQL Multi-AZ Cluster |
| **Vector Database** | `sentence-transformers` + In-Memory / pgvector | AWS Bedrock Knowledge Bases / OpenSearch |
| **ML Inference** | In-Process Python XGBoost + Scikit-Learn | AWS SageMaker Real-Time Endpoint / Triton Server |
| **Explainability (XAI)**| In-Process `shap.TreeExplainer` | AWS SageMaker Clarify Real-Time XAI |
| **Document OCR** | Local `pdfplumber` + `pytesseract` | AWS Textract Multimodal Document Intelligence |
| **LLM Copilot** | Local Ollama / Local `MockProvider` Fallback | AWS Bedrock (Claude 3.5 Sonnet / Llama 3) |
| **Event Streaming** | Python Async WebSockets (`events/ws`) | AWS API Gateway WebSockets + Amazon MSK (Kafka) |
| **Audit Storage** | Append-Only SQL `audit_events` Table | AWS QLDB / CloudTrail Immutable Ledger |

---

## 16. EXACT TECHNOLOGY-TO-COMPONENT MAPPING

| Technology | Implemented In Layer | Exact Role in LEDGER | Status |
|---|---|---|:---:|
| **React 19.2** | Presentation | Reactive component state & UI hierarchy | **IMPLEMENTED** |
| **TypeScript 6.0** | Presentation | Strict end-to-end type safety | **IMPLEMENTED** |
| **Vite 8.2** | Build Tool | ESM module bundling & rapid development | **IMPLEMENTED** |
| **TailwindCSS 4.3** | UI Styling | FinTech dark glassmorphism design system | **IMPLEMENTED** |
| **Framer Motion 13.1**| UI Animation | Fluid 7-step causal chain state machine | **IMPLEMENTED** |
| **Recharts 3.10** | UI Charts | Multi-point trajectory & financial twin radar | **IMPLEMENTED** |
| **FastAPI 0.110+** | API Layer | Asynchronous REST endpoints & WebSockets | **IMPLEMENTED** |
| **SQLAlchemy 2.0** | Persistence | Async ORM database abstraction | **IMPLEMENTED** |
| **XGBoost** | ML Engine | Gradient-boosted decision tree classifier | **IMPLEMENTED** |
| **Scikit-Learn** | ML Calibration | Isotonic regression default calibration | **IMPLEMENTED** |
| **SHAP** | Explainability | Exact TreeExplainer Shapley value computation | **IMPLEMENTED** |
| **sentence-transformers**| RAG Layer | Dense semantic embeddings (`all-MiniLM-L6-v2`) | **IMPLEMENTED** |
| **pdfplumber / Pillow**| Multimodal | Local PDF layout & text extraction | **IMPLEMENTED** |
| **pytesseract** | Multimodal | Image OCR entity parsing fallback | **IMPLEMENTED** |
| **python-jose / passlib**| Security | JWT encoding & salted bcrypt password hashing | **IMPLEMENTED** |
| **Ollama / MockProvider**| Copilot | Local LLM / deterministic fallback generation | **IMPLEMENTED** |
| **AWS Bedrock / MSK** | Cloud Evolution | Enterprise cloud scale architecture | **CONCEPTUAL** |

---

## 17. CODE SOURCE DIRECTORY MAPPING

| System Component | Exact Source File | Key Classes / Functions |
|---|---|---|
| **Underwriter Workbench** | `frontend/src/pages/ApplicationsPage.tsx` | `ApplicationsPage()` |
| **Executive Command Center** | `frontend/src/pages/DashboardPage.tsx` | `DashboardPage()` |
| **Financial Twin Console** | `frontend/src/pages/FinancialTwinPage.tsx` | `OverviewPanel()`, `WhatChangedPanel()`, `NBEPanel()`, `runCounterfactual()` |
| **API Application Routes** | `backend/app/api/applications.py` | `get_application()`, `analyze_application()`, `upload_document()`, `incorporate_document()` |
| **Event Simulation & WS** | `backend/app/api/events.py` | `simulate_event()`, `websocket_endpoint()` |
| **RAG Copilot Routes** | `backend/app/api/copilot.py` | `copilot_query()`, `execute_read_only_tools()` |
| **Feature Engineering** | `backend/app/ml/feature_engineering.py` | `compute_features()`, `FeatureVector` (12 features) |
| **Credit Pathway Engine** | `backend/app/ml/pathway_engine.py` | `determine_pathway()`, `CreditPathway`, `PathwayDecision` |
| **SHAP Explainability** | `backend/app/ml/shap_utils.py` | `compute_shap_values()`, `compute_shap_delta()` |
| **Dense Vector Retriever**| `backend/app/rag/retriever.py` | `retrieve_relevant_chunks()`, `build_grounded_prompt()` |
| **Security & RBAC** | `backend/app/core/security.py` | `create_access_token()`, `require_underwriter()`, `require_demo_admin()` |
| **Demo Administration** | `backend/app/api/demo.py` | `reset_scenario_a()`, `seed_all_scenarios()`, `demo_status()` |

---

## 18. VERIFICATION & FACT-CHECK STATUS

- **Decision Engine Separation**: Verified 100% deterministic (LLM has 0 authority).
- **Multimodal Pipeline**: Verified local parsing on synthetic 6M HDFC statement.
- **SHAP Attribution**: Verified real `shap.TreeExplainer` non-zero deltas.
- **Zero NaN Hygiene**: Verified clean score rendering across all UI views.
- **Build Status**: Verified `npm run build` exits code 0 with 0 errors.
- **Repeatability**: Verified 100% deterministic reset for demo Scenario A.
