# LEDGER — VERIFIED NUMBERS & SAFE CLAIMS REFERENCE
**One Synchrony Campus Hackathon • Release Candidate 1.0**

This document serves as the absolute factual ground truth for all slides, speaker notes, and presentation material for LEDGER. Every number in this document has been mathematically and programmatically verified against the active codebase and database.

---

## 1. Verified Core Numbers (Safe for PPT/PDF)

| Metric | Verified Exact Value | Source / Calculation | Context / Slide Usage |
|---|---|---|---|
| **Ananya Baseline Risk** | `11.0%` (`0.1098`) | Calibrated XGBoost Output | Hero baseline default risk before bank statement ingestion |
| **Ananya Baseline Confidence** | `56.5%` (`0.5652`) | Completeness-Weighted Uncertainty | Indicates high model epistemic uncertainty due to thin file |
| **Ananya Baseline Pathway** | `REQUEST_EVIDENCE` | Deterministic Rule 2 (`conf < 0.60`) | Initial gate requiring verified multimodal evidence |
| **Ananya Baseline Anomalies** | `0` | Anomaly Detector Filter | Proves thin-file lack of history is not flagged as fraudulent |
| **Ananya Baseline Completeness**| `35%` (`0.35`) | `FeatureVector.completeness_score` | Only initial 1-month sparse transaction stream available |
| **Extracted Monthly Salary** | `₹64,820.00` | Multimodal OCR / Entity Parser | Synthetic 6-month HDFC Bank Statement extraction |
| **Ingested Bank Txns** | `24 transactions` | Synthetic 6-Month Bank Statement | 6 salary credits + 18 recurring utility/rent/EMI payments |
| **Evidence Extraction Conf** | `94.0%` (`0.94`) | OCR & Field Validation Heuristic | Multimodal Document Ingestion confidence |
| **Post-Evidence Completeness** | `85%` (`0.85`) | `compute_features` on 24 Txns | Data completeness after incorporating 6-month statement |
| **Post-Evidence Confidence** | `60.3%` – `78.0%` | `_compute_confidence` on 85% data | Model confidence increase post-evidence incorporation |
| **Post-Evidence Pathway** | `CONDITIONAL_APPROVAL` | Deterministic Rule 5 (`risk < 0.40`) | Promoted from `REQUEST_EVIDENCE` |
| **Approved Exposure Limit** | `₹50,000` | `EXPOSURE_LIMITS` Policy Table | Credit line assigned for Conditional Approval |
| **Monitoring Period** | `60 days` | `MONITORING_PERIODS` Policy Table | Automated post-approval behavioral monitoring window |
| **SHAP Income Consistency $\Delta$** | `-0.8551` to `-1.2418` | `shap.TreeExplainer` Delta | Substantial reduction in default risk from steady payroll |
| **SHAP Debt-to-Income $\Delta$** | `-0.7528` | `shap.TreeExplainer` Delta | Reduction in risk from verified low recurring debt load |
| **SHAP Liquidity Ratio $\Delta$** | `-0.5000` | `shap.TreeExplainer` Delta | Reduction in risk from verified positive average balance |
| **Active Demo Personas** | `5 Personas` | `backend/app/api/demo.py` | 5 deterministic personas representing critical edge cases |
| **Feature Vector Dimension** | `12 Features` | `backend/app/ml/feature_engineering.py` | 12 defensible behavioral and cashflow metrics |
| **Financial Twin Dimensions** | `6 Dimensions` | `backend/app/api/applications.py` | Stability, Reliability, Discipline, Liquidity, Volatility, Capacity |
| **Full Approval Exposure Limit** | `₹100,000` | Policy Version `v1.2` | Assigned to prime personas (e.g. Priya Menon) |

---

## 2. 5 Deterministic Demo Personas Data Table

| Scenario | Applicant Name | Persona Tag | Baseline Risk | Baseline Conf | Initial Pathway | Why Scenario Exists |
|:---:|---|---|:---:|:---:|:---:|---|
| **A** | **Ananya Sharma** | `thin_file_ntc` | **11.0%** | **56.5%** | `REQUEST_EVIDENCE` | **Hero Demo**: Low risk but high uncertainty. Unlocked via 6M bank statement. |
| **B** | **Rajesh Nair** | `high_income_unstable` | **58.8%** | **46.3%** | `REQUEST_EVIDENCE` | High earner with high month-to-month variance. Needs monitoring. |
| **C** | **Priya Menon** | `moderate_disciplined` | **1.6%** | **85.9%** | `FULL_APPROVAL` | Prime baseline benchmark with 24 months of steady discipline. |
| **D** | **Karan Mehta** | `high_volatility_suspicious`| **100.0%** | **87.5%** | `HUMAN_REVIEW` | Anomaly injection demo. High balance volatility + suspicious transfers. |
| **E** | **Divya Krishnan** | `ambiguous_ntc` | **57.9%** | **25.4%** | `REQUEST_EVIDENCE` | Extreme thin file. Very low completeness triggers Next-Best-Evidence. |

---

## 3. Claim Safety Guidelines

### ✅ CLAIMS WE CAN SAFELY MAKE (Fact-Checked)
1. **"Working End-to-End Prototype"**: The application runs completely locally using FastAPI, React/TypeScript/Vite, SQLite/PostgreSQL, XGBoost, SHAP, and local Ollama/MockProvider.
2. **"Deterministic Credit Pathway Engine"**: Credit decisions and pathways are strictly determined by XGBoost + Isotonic Calibration + Rule Engine policies. The LLM **never** determines credit lines or pathways.
3. **"Local Multimodal Document Extraction"**: Real PDF and image parsing via `pdfplumber` / `pytesseract` / layout regex heuristics.
4. **"Exact Mathematical SHAP Explainability"**: Feature importance and What Changed $\Delta$ values are calculated directly using `shap.TreeExplainer` on the underlying trees.
5. **"Grounded Decision Explainer Copilot"**: RAG pipeline uses `sentence-transformers` vector search with strict policy and evidence citations.
6. **"Real-Time Causal Event Pipeline"**: Prototype event pipeline simulates incoming transaction streams and broadcasts recomputed twin states over WebSockets.
7. **"Synthetic Demonstration Data"**: All applicant profiles, bank statements, and transactions are synthetically generated for privacy and deterministic repeatability.

---

### ❌ CLAIMS WE MUST NEVER MAKE (Strictly Prohibited)
1. **DO NOT CLAIM**: *"Production-ready enterprise deployment"* $\rightarrow$ **Say**: *"Production-ready modular architecture demonstrated via local hackathon prototype."*
2. **DO NOT CLAIM**: *"Fully regulatory compliant with RBI / CFPB / FCRA"* $\rightarrow$ **Say**: *"Architected with explainability, audit trails, and human oversight to align with regulatory standards."*
3. **DO NOT CLAIM**: *"Real Synchrony proprietary customer data"* $\rightarrow$ **Say**: *"Tested on realistic synthetic multi-modal banking data modeling Indian banking & UPI patterns."*
4. **DO NOT CLAIM**: *"Quantum Machine Learning Advantage"* $\rightarrow$ **Say**: *"Future research extension: Quantum-ready portfolio risk optimization."*
5. **DO NOT CLAIM**: *"Reinforcement Learning / True Active Learning"* $\rightarrow$ **Say**: *"Heuristic Next-Best-Evidence uncertainty reduction ranking."*
6. **DO NOT CLAIM**: *"Enterprise Apache Kafka / Kinesis cluster"* $\rightarrow$ **Say**: *"Prototype event-driven architecture with WebSocket broadcast."*
7. **DO NOT CLAIM**: *"Measured 99.8% AUC / Model Accuracy"* $\rightarrow$ **Say**: *"Model architecture uses Calibrated XGBoost; formal offline AUC was not benchmarked for the prototype dataset."*
