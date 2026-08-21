# LEDGER — PPT/PDF SCREENSHOT CHECKLIST & ASSET GUIDE
**One Synchrony Campus Hackathon • Release Candidate 1.0**

This checklist details the 17 visual screenshots to capture or embed into the final PPT/PDF submission deck. Each entry lists the exact application route, visual elements, what it proves to the judges, and key callouts.

---

## 1. Primary Slide Deck Screenshot Catalog

| # | Asset File Name | Application Route / State | What the Screenshot Shows | Why It Matters / Technical Proof |
|:---:|---|---|---|---|
| **01** | `01_command_center.png` | `http://localhost:5173/dashboard` | Executive Command Center: Portfolio KPI cards, Credit Pathway allocation progress bars, Risk band distribution, and Anomaly alerts. | Proves high-level portfolio underwriting intelligence; separates portfolio oversight from case investigation. |
| **02** | `02_applications_queue.png` | `http://localhost:5173/applications` | Underwriter Case Workbench: Search bar, multi-dimensional pathway pills, persona tags, calibrated risk gauges, and confidence scores. | Proves underwriter case triage capabilities with zero `NaN` values and rich filtering. |
| **03** | `03_ananya_baseline.png` | `http://localhost:5173/applications/{ananya_id}` (Overview tab) | Ananya Sharma baseline: `Request Evidence` badge, 11.0% Risk, 56.5% Confidence, 6-dimension Financial Twin radar, and single-point baseline card. | Establishes the **"UNKNOWN ≠ UNTRUSTWORTHY"** thesis: low underlying risk + high thin-file uncertainty. |
| **04** | `04_multimodal_upload.png` | Financial Twin $\rightarrow$ `Multimodal Evidence` tab | Multimodal Evidence Ingestion dropzone with synthetic 6M HDFC Bank Statement PDF sample card. | Proves document support (PDF/PNG/JPG/CSV) and alternative data ingestion capability. |
| **05** | `05_ocr_pipeline.png` | Multimodal Evidence $\rightarrow$ Click `Process 6M Statement` | 5-Step Multimodal Extraction Stepper: *1. Ingestion $\rightarrow$ 2. Classification $\rightarrow$ 3. OCR $\rightarrow$ 4. Entity Extraction $\rightarrow$ 5. Validation*. | Proves real document intelligence pipeline running locally without black-box cloud dependencies. |
| **06** | `06_structured_financial_entities.png` | Multimodal Evidence (Post-Processing) | Extracted structured entities: Verified Salary ₹64,820/mo, 24 verified transactions, Employer name, and 94% evidence confidence. | Shows transformation of unstructured PDF text into structured financial feature inputs. |
| **07** | `07_incorporate_result.png` | Multimodal Evidence $\rightarrow$ Click `Incorporate into Financial Twin` | Pathway promotion banner: `Request Evidence` $\rightarrow$ `Conditional Approval` with ₹50,000 credit limit and 78% confidence. | Core hackathon "WOW" moment: proves alternative data directly expands credit access for NTC applicants. |
| **08** | `08_trajectory.png` | Financial Twin $\rightarrow$ Overview (Post-Incorporation) | Multi-point Risk Trajectory chart: Point 1 (11.0% risk, 56.5% conf) $\rightarrow$ Point 2 (11.0% risk, 78% conf) with shaded gradients. | Proves thesis: *"Traditional underwriting sees a snapshot. Ledger understands the trajectory."* |
| **09** | `09_what_changed.png` | Financial Twin $\rightarrow$ `What Changed?` tab | 7-Stage Causal Animation Chain with green checkmarks (✓) and Before $\rightarrow$ After comparison card. | Demonstrates end-to-end causal traceability for every evidence event. |
| **10** | `10_shap_delta.png` | What Changed $\rightarrow$ `SHAP Feature Contributions Δ` | Mathematical SHAP $\Delta$ Waterfall: `income_consistency: -0.855`, `debt_to_income: -0.753`, `liquidity_ratio: -0.500`. | Proves real `shap.TreeExplainer` values — never hardcoded or fabricated. |
| **11** | `11_what_would_change_my_mind.png`| Financial Twin $\rightarrow$ `What Would Change?` tab | Next-Best-Evidence (NBE) ranked recommendations with expected uncertainty reduction percentages (~24% balance statements). | Proves proactive underwriting intelligence guiding applicant to approval. |
| **12** | `12_counterfactual.png` | Financial Twin $\rightarrow$ `Counterfactual` tab | What-if interactive sliders (Income consistency, expense ratio, payment regularity) with real-time trajectory fork. | Proves non-mutating scenario simulation for underwriter stress-testing. |
| **13** | `13_copilot.png` | Financial Twin $\rightarrow$ `AI Copilot` tab | AI Copilot query *"Why did the pathway change?"* showing grounded answer, tool calls, and policy citations (P-15, Sec 3.1). | Proves Responsible AI: LLM explains and cites — XGBoost determines. |
| **14** | `14_evidence_network.png` | Financial Twin $\rightarrow$ `Evidence Network` tab | Entity relationship graph: Customer $\rightarrow$ Employer $\rightarrow$ Accounts $\rightarrow$ Inflow/Outflow streams via relational joins. | Proves multi-source relational integrity without needing graph databases. |
| **15** | `15_why_this_decision.png` | Financial Twin $\rightarrow$ `Responsible AI` tab | Governance & Transparency breakdown: Decision engine vs LLM boundary, policy citations, and synthetic data notices. | Satisfies Responsible AI, fairness, and governance requirements. |
| **16** | `16_audit_trail.png` | Financial Twin $\rightarrow$ `Audit Trail` tab | Append-only immutable audit log recording actor, timestamp, payload hash, and triggered model versions. | Proves enterprise auditability and regulatory traceability. |
| **17** | `17_karan_human_review.png` | Applications Queue $\rightarrow$ Open Scenario D (Karan Mehta) | Karan Mehta case: `Human Review Required`, 100% Risk, and `Extreme Balance Volatility` anomaly badge. | Proves fraud/anomaly mitigation: anomalous behavior triggers strict human oversight. |

---

## 2. Capture & Layout Recommendations for PPT

- **Aspect Ratio**: Capture screenshots in 16:9 widescreen or tight cropped 4:3 cards for side-by-side slide presentation.
- **Dark Mode Styling**: LEDGER's dark glassmorphism theme (`#0a0f1d` with `#00d4e0` cyan and `#10b981` emerald accents) provides high visual contrast on slide backgrounds.
- **Callout Annotations**: Use numbered callout badges (①, ②, ③) on slide images to highlight:
  1. Calibrated Risk Meter
  2. Multi-point Trajectory Line
  3. Real SHAP TreeExplainer Waterfall
  4. RAG Copilot Policy Citations
