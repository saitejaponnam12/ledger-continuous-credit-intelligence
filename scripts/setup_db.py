"""
LEDGER — Database Setup & Seed Script
Creates tables, seeds users, demo personas, and policy documents.
Run: python scripts/setup_db.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings
from app.core.database import AsyncSessionLocal, create_all_tables
from app.core.security import hash_password
from app.models.models import PolicyDocument, User


async def seed_users(session) -> None:
    from sqlalchemy import select
    from app.models.models import User

    users = [
        User(
            email=settings.demo_underwriter_email,
            display_name="Sarah Chen",
            hashed_password=hash_password(settings.demo_underwriter_password),
            role="underwriter",
        ),
        User(
            email=settings.demo_admin_email,
            display_name="Demo Admin",
            hashed_password=hash_password(settings.demo_admin_password),
            role="demo_admin",
        ),
    ]

    for user in users:
        existing = await session.execute(select(User).where(User.email == user.email))
        if not existing.scalar_one_or_none():
            session.add(user)
            print(f"  Created user: {user.email} ({user.role})")
        else:
            print(f"  User already exists: {user.email}")


async def seed_policy_documents(session) -> None:
    """Seed synthetic policy documents for RAG retrieval."""
    from sqlalchemy import select

    # Check if already seeded
    existing = await session.execute(select(PolicyDocument).limit(1))
    if existing.scalar_one_or_none():
        print("  Policy documents already seeded — skipping")
        return

    policies = [
        {
            "title": "Underwriting Policy — NTC & Thin-File Applicants (P-12)",
            "category": "underwriting",
            "version": "v1.2",
            "content": """
LEDGER UNDERWRITING POLICY — NEW-TO-CREDIT (NTC) AND THIN-FILE APPLICANTS
Policy Number: P-12 | Version: 1.2 | Effective: 2025-01-01

SECTION 3.1 — ELIGIBILITY CRITERIA
New-to-credit applicants are defined as individuals with fewer than 6 months of formal financial history.
Thin-file applicants have fewer than 3 credit products or 12 months of transaction history.
Both categories are evaluated using alternative data signals including UPI transaction history,
digital payment behavior, and utility payment regularity.

SECTION 3.2 — INCOME VERIFICATION
For NTC applicants, verified income evidence is a primary determinant for credit approval.
Consistent income (income_consistency score ≥ 0.65) with three or more months of documented
salary credits significantly increases eligibility for conditional approval.
Income consistency is measured as the coefficient of variation of monthly credit amounts (inverted).

SECTION 3.3 — EXPOSURE LIMITS FOR NTC APPLICANTS
Full Approval: ₹1,00,000 maximum | Requires risk_probability < 0.22 and confidence ≥ 0.75
Conditional Approval: ₹20,000–₹80,000 | Requires risk_probability < 0.40 and confidence ≥ 0.60
Monitoring Period: 60–90 days mandatory for all NTC approvals.

SECTION 3.4 — EVIDENCE HIERARCHY
Primary evidence: Bank statement (3+ months), verified salary slips
Secondary evidence: UPI transaction history, utility payment records
Tertiary evidence: Rental payment history, insurance payment consistency

SECTION 3.5 — ACTIVE UNDERWRITING PRINCIPLE
When model confidence falls below 0.50, underwriters must request the highest-value missing evidence
rather than defaulting to decline. This principle — Active Underwriting — preserves credit access
for creditworthy applicants with limited formal history.
""",
        },
        {
            "title": "Credit Risk Assessment Framework — Feature Definitions (P-08)",
            "category": "underwriting",
            "version": "v1.2",
            "content": """
LEDGER CREDIT RISK FRAMEWORK — FEATURE DEFINITIONS
Policy Number: P-08 | Version: 1.2

SECTION 1 — INCOME CONSISTENCY
Definition: Measures the stability of monthly income over the assessment window.
Calculation: 1 - (std(monthly_credits) / mean(monthly_credits))
Interpretation: Score of 1.0 = perfectly stable income. Score near 0 = highly erratic income.
Minimum for conditional approval: 0.55
Primary risk signal: scores below 0.30 indicate income uncertainty.

SECTION 2 — PAYMENT DISCIPLINE
Definition: Proportion of months with documented recurring payment obligations met.
Components: Rent, EMI, utilities, insurance premiums.
Interpretation: Score of 1.0 = 100% of months have recurring payments. 
Score below 0.40 triggers evidence request for payment history.

SECTION 3 — CASHFLOW STABILITY
Definition: Ratio of minimum monthly net cashflow to average monthly net cashflow.
Purpose: Identifies applicants who regularly dip to near-zero or negative balances.
Threshold: Scores below 0.30 indicate structural cashflow stress.

SECTION 4 — DEBT-TO-INCOME
Definition: Estimated recurring debt payments (EMI, loan) as a proportion of monthly income.
High-risk threshold: DTI > 0.55 indicates high debt burden.
Moderate-risk threshold: DTI 0.35–0.55 requires closer review.

SECTION 5 — BALANCE VOLATILITY
Definition: Coefficient of variation of monthly net balance (normalized by mean absolute balance).
High volatility (> 0.80) may indicate irregular income, overdependence on credit, or financial distress.
High volatility combined with high transaction velocity is a fraud signal.
""",
        },
        {
            "title": "Credit Pathway Decision Rules — Engine Policy (P-15)",
            "category": "underwriting",
            "version": "v1.2",
            "content": """
LEDGER CREDIT PATHWAY ENGINE — DECISION RULES
Policy Number: P-15 | Version: 1.2

OVERVIEW
The Credit Pathway Engine transforms model output (risk_probability, confidence) into one of five pathways:
Full Approval | Conditional Approval | Request Evidence | Human Review | Transparent Decline

The LLM Copilot does NOT determine the pathway. The pathway is determined by deterministic rules
applied to XGBoost model output. The Copilot only explains the pathway after it is determined.

RULE SET (Applied in Priority Order):

RULE 1 — FRAUD OVERRIDE
If any fraud signal has severity = HIGH: Pathway = Human Review
Rationale: Behavioral anomalies require human judgment before any credit decision.

RULE 2 — EVIDENCE REQUEST
If confidence < 0.45 OR completeness_score < 0.40: Pathway = Request Evidence
Rationale: Model cannot make reliable prediction without sufficient data.

RULE 3 — TRANSPARENT DECLINE
If risk_probability > 0.68: Pathway = Transparent Decline
New evidence may change this pathway. Applicant must be informed of the primary risk factors.

RULE 4 — HUMAN REVIEW
If 0.48 ≤ risk_probability ≤ 0.68 AND confidence < 0.68: Pathway = Human Review
Rationale: Ambiguous cases with moderate confidence require underwriter judgment.

RULE 5 — FULL APPROVAL
If risk_probability < 0.22 AND confidence ≥ 0.75: Pathway = Full Approval
Maximum exposure: ₹1,00,000. 90-day monitoring period.

RULE 6 — CONDITIONAL APPROVAL (DEFAULT)
All remaining cases in the 0.22–0.48 risk range with adequate confidence.
Exposure scaled by: base ₹80,000 - risk_penalty + confidence_bonus.
Monitoring: 30–90 days based on risk level.
""",
        },
        {
            "title": "Responsible AI & Explainability Policy (RA-01)",
            "category": "responsible_ai",
            "version": "v1.0",
            "content": """
LEDGER RESPONSIBLE AI POLICY
Policy Number: RA-01 | Version: 1.0

SECTION 1 — ARCHITECTURAL SEPARATION
The Decision Engine (XGBoost + calibration + business rules) is strictly separated from the
AI Copilot (LLM + RAG). The Copilot explains decisions; it does not make them.
This separation is a regulatory and governance requirement, not merely a design choice.

SECTION 2 — EXPLAINABILITY REQUIREMENTS
Every credit decision must be accompanied by:
- SHAP values from the actual model (not fabricated)
- Identified positive contributors (features reducing risk probability)
- Identified negative contributors (features increasing risk probability)
- Model version and timestamp
- Policy version governing the decision rules

SECTION 3 — PROHIBITED ATTRIBUTES
The following attributes must NEVER be used as model features or indirectly inferred:
- Gender, race, religion, caste, national origin
- Marital status, number of dependents (direct inputs)
- Location as a proxy for demographics
Model inputs are limited to behavioral and financial signals only.

SECTION 4 — HUMAN OVERSIGHT
All decisions flagged for Human Review must be reviewed by a licensed underwriter before execution.
The AI system is a decision-support tool. Final credit authority rests with human underwriters.
Underwriters may override any AI recommendation with documented rationale.

SECTION 5 — HONEST LIMITATIONS
This prototype uses synthetic demonstration data. It has NOT been tested for demographic bias
on real-world data. Production deployment would require:
- Subgroup performance monitoring (by geography, income bracket, age)
- Disparate impact testing
- Model fairness audits (quarterly minimum)
- Ongoing recalibration as data distribution shifts

SECTION 6 — DISCLAIMER
"This prototype uses synthetic data and is intended for decision support, not autonomous lending."
""",
        },
        {
            "title": "Evidence Standards — What Constitutes Valid Financial Evidence (E-03)",
            "category": "evidence",
            "version": "v1.1",
            "content": """
LEDGER EVIDENCE STANDARDS
Policy Number: E-03 | Version: 1.1

TIER 1 — PRIMARY EVIDENCE (Highest information value)
Bank Statement: Must cover minimum 3 consecutive months. Must show account holder name,
account number (last 4 digits), transaction history, and closing balance.
Salary Slip: Issued by employer on company letterhead. Must show gross salary, deductions, and net pay.
Form 16 (India): Annual income tax statement issued by employer.

TIER 2 — SECONDARY EVIDENCE
UPI Transaction History: Downloaded from bank app. Minimum 90 days.
Utility Bill Payment Records: Electricity, gas, water — minimum 6 months showing consistent payment.
Insurance Premium Records: Life, health, or vehicle insurance payment receipts.

TIER 3 — TERTIARY EVIDENCE
Rental Agreement + Receipts: Verifies stable housing and regular payment obligation.
GST Returns (for self-employed): Income proof for gig workers and small business owners.
Investment Statement: Mutual fund or stock holdings showing financial discipline.

ACTIVE UNDERWRITING GUIDANCE
When requesting evidence, underwriters must specify:
1. Which feature(s) have insufficient data
2. Which evidence tier would address the gap
3. Expected impact on model confidence (heuristic estimate)
4. Deadline for evidence submission (maximum 30 days)

Evidence requests should be ranked by: Expected Uncertainty Reduction / Customer Friction
""",
        },
    ]

    for policy in policies:
        doc = PolicyDocument(
            title=policy["title"],
            content=policy["content"],
            policy_version=policy["version"],
            doc_category=policy["category"],
        )
        session.add(doc)
        print(f"  Created policy: {policy['title'][:60]}...")

    await session.flush()
    print(f"  Created {len(policies)} policy documents")


async def main():
    print("\n" + "=" * 60)
    print("LEDGER — Database Setup")
    print("=" * 60)

    # Create tables
    print("\n[1/3] Creating database tables...")
    await create_all_tables()
    print("  Tables created (or already exist)")

    # Seed data
    async with AsyncSessionLocal() as session:
        print("\n[2/3] Seeding users...")
        await seed_users(session)

        print("\n[3/3] Seeding policy documents...")
        await seed_policy_documents(session)

        await session.commit()

    print("\n[SUCCESS] Database setup complete!")
    print("\nNext steps:")
    print("  1. python scripts/generate_data.py  (generate synthetic training data)")
    print("  2. python ml/train.py               (train XGBoost model)")
    print("  3. python scripts/ingest_policies.py (embed policy docs into pgvector)")
    print("  4. uvicorn backend.app.main:app --reload --port 8000")


if __name__ == "__main__":
    asyncio.run(main())
