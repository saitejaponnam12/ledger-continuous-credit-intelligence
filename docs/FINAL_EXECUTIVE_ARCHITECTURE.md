# LEDGER — EXECUTIVE ARCHITECTURE SPECIFICATION
**One Synchrony Campus Hackathon • Release Candidate 1.0**

This document provides a concise, high-impact architectural overview tailored for executive presentation slides, pitch decks, and technical summary briefs.

---

## 1. Executive System Architecture (High-Level)

```
                            UNDERWRITER / RISK OFFICER
                                        │
                                        ▼
                  ┌───────────────────────────────────────────┐
                  │      REACT UNDERWRITING CONSOLE           │
                  │   • Command Center  • Case Workbench      │
                  │   • Financial Twin  • What Changed?       │
                  └─────────────────────┬─────────────────────┘
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

## 2. The Core Responsible AI Boundary

A key differentiator of LEDGER is its strict structural separation between **Decision Execution** (which is 100% deterministic) and **Decision Explanation** (which leverages bounded natural language AI):

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

## 3. Technology Mapping (Implemented vs. Future Evolution)

| Component | Implemented Prototype Technology | Future Production Evolution (AWS Cloud) |
|---|---|---|
| **Frontend** | React 19 + TypeScript 6 + Vite 8 + TailwindCSS | Next.js on AWS CloudFront Edge |
| **API Layer** | FastAPI + Uvicorn (Async ASGI) | AWS ECS / EKS Containerized Microservices |
| **Relational DB** | SQLite / PostgreSQL via SQLAlchemy 2.0 Async | AWS Aurora PostgreSQL (Multi-AZ) |
| **Vector Search** | `sentence-transformers` + In-Memory / pgvector | AWS Bedrock Knowledge Bases / OpenSearch |
| **ML Engine** | XGBoost + `CalibratedClassifierCV` (Isotonic) | AWS SageMaker Real-Time Endpoint |
| **Explainability** | `shap.TreeExplainer` (Exact Shapley Values) | AWS SageMaker Clarify Real-Time XAI |
| **Document OCR** | `pdfplumber` + `pytesseract` + Regex Parsers | AWS Textract Multimodal Document Intelligence |
| **LLM Provider** | Local Ollama / Structured `MockProvider` Fallback | AWS Bedrock (Claude 3.5 Sonnet / Llama 3) |
| **Streaming** | Async Python WebSockets (RFC 6455) | AWS API Gateway WebSockets + Amazon MSK |
| **Audit Ledger** | Append-Only `audit_events` SQL Table | AWS QLDB / CloudTrail Immutable Log |

---

## 4. Key Metrics Safe for Executive Slides

- **Hero Applicant Baseline (Ananya Sharma)**: `11.0% Risk` | `56.5% Confidence` | `Pathway: Request Evidence`
- **Extracted 6M Statement Salary**: `₹64,820 / month` across `24 verified transactions`
- **Post-Evidence Promotion**: `Pathway: Conditional Approval` (₹50,000 credit limit, 60-day monitoring)
- **Top SHAP Delta**: `income_consistency: -0.8551` (Verified reduction in default risk)
- **Feature Vector**: `12 mathematically defined cashflow features` (Zero fabricated random variables)
