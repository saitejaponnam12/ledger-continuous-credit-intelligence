# LEDGER — Continuous Credit Intelligence

<div align="center">

```
   __    ____ ___   ____ ____ ____ 
  / /   / __// _ \ / __// __// _ \
 / /__ / _/ / // // _/ / _/ / , _/
/____//___//____//___//___//_/|_| 
```

### **Real-Time, Multi-Modal Underwriting Engine for Next-Gen Credit Intelligence**
*Built for the One Synchrony Campus Hackathon • Problem Statement 1*

[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-blue?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-19.2-61dafb?logo=react&logoColor=black)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML_Engine-eb5424?logo=python&logoColor=white)](https://xgboost.readthedocs.io/)
[![SHAP](https://img.shields.io/badge/SHAP-TreeExplainer-ff69b4)](https://shap.readthedocs.io/)
[![Vite](https://img.shields.io/badge/Vite-8.2-646cff?logo=vite&logoColor=white)](https://vitejs.dev/)

---

### **"UNKNOWN ≠ UNTRUSTWORTHY"**
*Traditional underwriting sees a snapshot. Ledger understands the trajectory.*

</div>

---

## 📌 Executive Overview

Traditional credit scorecards (FICO, CIBIL) rely strictly on historical credit bureau trades. For **New-to-Credit (NTC)**, **thin-file**, and **gig-economy** applicants, this creates an **information-driven market failure**: creditworthy individuals are rejected simply due to lack of historical data, not proven default risk.

**LEDGER** replaces static bureau scorecards with a **real-time, multi-modal credit intelligence engine**. By ingesting alternative banking streams, multimodal documents (PDF bank statements, salary slips, utility invoices), and real-time behavioral signals, LEDGER constructs an evolving **Financial Twin** for every borrower and routes them across progressive, risk-calibrated **Credit Pathways**.

---

## 🚀 Key Innovations & Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              LEDGER SYSTEM ARCHITECTURE                                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [Multimodal Document Upload] ──► [Local OCR / Entity Parser]                         │
│   (PDF / PNG / JPG Bank Stmts)      (pdfplumber / pytesseract)                         │
│                                                 │                                      │
│                                                 ▼                                      │
│   [Real-Time Transaction Stream] ─► [12-Feature Cashflow Engine]                       │
│   (API / Simulated Events)          (Income consistency, liquidity, leverage)          │
│                                                 │                                      │
│                                                 ▼                                      │
│                                    [Calibrated XGBoost Model]                          │
│                                    (Isotonic Default Probability)                      │
│                                                 │                                      │
│                                                 ▼                                      │
│                                    [SHAP TreeExplainer]                                │
│                                    (Exact Shapley Feature Attribution)                 │
│                                                 │                                      │
│                                                 ▼                                      │
│                                    [Deterministic Pathway Rules]                       │
│                                    (Full / Conditional / Request Evidence)             │
│                                                 │                                      │
│                                                 ▼                                      │
│                                    [WebSocket Broadcast & UI]                          │
│                                    (Financial Twin, Trajectory, Copilot)               │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. 🧬 The Financial Twin Console
A continuous multi-dimensional representation of an applicant's real-time financial health evaluated across 6 pillars: *Financial Stability, Income Reliability, Payment Discipline, Liquidity Reserve, Balance Volatility, and Exposure Capacity*.

### 2. 📈 Multi-Point Risk Trajectory
Replaces static 3-digit scores with an evolving trajectory. When only a single baseline observation exists, LEDGER renders an intentional single-point baseline node; as verified evidence arrives, it renders the multi-point trajectory evolution with calibrated confidence bounds.

### 3. 📄 Multimodal Document Intelligence
Ingests unstructured financial documents (PDFs, images, CSVs) locally. Executes a 5-step extraction pipeline (*Ingestion $\rightarrow$ Classification $\rightarrow$ OCR Layout Parsing $\rightarrow$ Structured Entity Extraction $\rightarrow$ Validation Checksum*), extracting verified payroll credits and recurring debit commitments without cloud API dependencies.

### 4. ⚡ 7-Stage "What Changed?" Causal Chain
Every evidence update executes a deterministic state machine:
1. **Evidence Arrives** (e.g., 6M Bank Statement / Payroll Credit)
2. **Feature Engineering Recalculates** (Completeness jumps 35% $\rightarrow$ 85%)
3. **XGBoost Scores New Vector** (Calibrated default probability computed)
4. **SHAP Explains What Moved** (Mathematical $\Delta \text{SHAP}$ feature deltas)
5. **Confidence Recalibrated** (Epistemic uncertainty reduced)
6. **Credit Pathway Updated** (`Request Evidence` $\rightarrow$ `Conditional Approval`)
7. **Financial Twin Updated** (Exposure limit assigned; WebSocket push)

### 5. 💡 What Would Change My Mind? (Next-Best-Evidence)
Calculates expected uncertainty reduction ($\Delta U$) across missing alternative evidence types, providing underwriters and applicants with a transparent roadmap to credit approval.

### 6. 🎛️ Counterfactual Simulator
Allows underwriters to interactively slide financial parameters (*income consistency, expense ratio, payment regularity, account age*) to stress-test outcomes in real-time with trajectory forks without mutating stored customer records.

### 7. 🤖 Grounded Decision Support Copilot (Responsible AI)
An AI Copilot grounded via dense vector search (`sentence-transformers`) over underwriting policy manuals (e.g., Policy P-15, Section 3.1). **Architectural Rule**: The LLM *explains* decisions — classical calibrated models and deterministic rules *decide*.

---

## 💻 Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, TypeScript 6.0, Vite 8.2, TailwindCSS 4.3, Framer Motion, Recharts |
| **Backend API** | FastAPI, Uvicorn (ASGI), Python 3.11+, WebSockets |
| **Database & ORM**| SQLAlchemy 2.0 (Async), SQLite / PostgreSQL with pgvector |
| **Machine Learning**| XGBoost, Scikit-Learn (`CalibratedClassifierCV`), SHAP (`TreeExplainer`) |
| **Multimodal / OCR**| `pdfplumber`, `pytesseract`, `Pillow`, Layout regex extractors |
| **RAG & Copilot** | `sentence-transformers` (`all-MiniLM-L6-v2`), Ollama / Local MockProvider |
| **Security** | JWT (`python-jose`), `passlib` with `bcrypt`, Strict Role-Based Access Control |

---

## 🏃 Quickstart & Local Setup

### Prerequisites
- **Node.js**: `v20+` & `npm`
- **Python**: `3.11+`
- **Git**

### 1. Clone & Configure
```bash
git clone <your-repo-url>
cd "SYN LEDGER"
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt

# Start backend server (Port 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install

# Start Vite dev server (Port 5173)
npm run dev
```

### 4. Open in Browser
- **Frontend Console**: [http://localhost:5173](http://localhost:5173)
- **API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔐 Demo Credentials & Personas

| Role | Email | Password | Access Level |
|---|---|---|---|
| **Credit Underwriter** | `sarah.chen@ledger.demo` | `LedgerDemo2026!` | Case workbench, twin inspection, multimodal evidence upload, Copilot, counterfactuals |
| **Demo Admin** | `admin@ledger.demo` | `LedgerAdmin2026!` | All underwriter capabilities + scenario reset controls & bulk seeding |

### Demo Personas Matrix
- **Scenario A (Hero)**: **Ananya Sharma** (`thin_file_ntc`) $\rightarrow$ Baseline: `Request Evidence` ($11.0\%$ risk, $56.5\%$ conf). Ingesting 6M bank statement promotes to `Conditional Approval` (₹50,000 limit).
- **Scenario B**: **Rajesh Nair** (`high_income_unstable`) $\rightarrow$ High income with month-to-month volatility requiring ongoing monitoring.
- **Scenario C**: **Priya Menon** (`moderate_disciplined`) $\rightarrow$ Prime baseline benchmark ($1.6\%$ risk) assigned automated `Full Approval` (₹100,000 limit).
- **Scenario D**: **Karan Mehta** (`high_volatility_suspicious`) $\rightarrow$ Anomaly signal trigger ($100\%$ risk) routing directly to `Human Review`.
- **Scenario E**: **Divya Krishnan** (`ambiguous_ntc`) $\rightarrow$ Sparse thin-file demonstrating Next-Best-Evidence uncertainty reduction.

---

## 📁 Repository Structure

```
SYN LEDGER/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI Routers (applications, events, copilot, demo, auth)
│   │   ├── copilot/          # RAG Copilot providers & bounded read-only tools
│   │   ├── core/             # Configuration, async database sessions & JWT security
│   │   ├── events/           # WebSocket manager & real-time broadcast pipelines
│   │   ├── ml/               # 12-feature pipeline, XGBoost calibration, SHAP & pathway engine
│   │   ├── models/           # SQLAlchemy ORM database models
│   │   └── rag/              # Vector embeddings & policy retrieval
│   ├── data/                 # Sample synthetic bank statements & documents
│   └── requirements.txt      # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/       # AppShell, Navigation, ProtectedRoute
│   │   ├── lib/              # Axios API client & typed interfaces
│   │   ├── pages/            # Dashboard (Command Center), Applications, FinancialTwin, Demo
│   │   └── store/            # Zustand authentication store
│   └── package.json          # React, Vite & Tailwind dependencies
└── docs/
    ├── PPT_SOURCE_PACK.md    # Fact-checked master source pack for hackathon presentation
    ├── PPT_VERIFIED_NUMBERS.md # Reference table of verified numbers & claim boundaries
    └── PPT_SCREENSHOT_CHECKLIST.md # Complete catalog of all 17 slide screenshots
```

---

## 🏆 Hackathon Submission Deliverables

- **Source Pack**: [`docs/PPT_SOURCE_PACK.md`](docs/PPT_SOURCE_PACK.md)
- **Verified Numbers Reference**: [`docs/PPT_VERIFIED_NUMBERS.md`](docs/PPT_VERIFIED_NUMBERS.md)
- **Screenshot Catalog**: [`docs/PPT_SCREENSHOT_CHECKLIST.md`](docs/PPT_SCREENSHOT_CHECKLIST.md)

---

<div align="center">

**One Synchrony Campus Hackathon 2026 • Problem Statement 1**  
*Built with precision for explainable, continuous credit intelligence.*

</div>
