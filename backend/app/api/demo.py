"""
LEDGER — Demo Control Panel Router
Hidden admin endpoint for deterministic demo scenario management.
Access: JWT with demo_admin role only.
"""
from __future__ import annotations

import json
import pickle
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated
from uuid import UUID

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import CurrentUser, hash_password, require_admin, require_underwriter
from app.ml.feature_engineering import compute_features, FEATURE_NAMES
from app.ml.pathway_engine import determine_pathway
from app.ml.shap_utils import compute_shap_values, compute_next_best_evidence, rank_shap_for_display
from app.models.models import (
    Application,
    AuditEvent,
    Customer,
    Decision,
    ExtractedFeatures,
    FinancialAccount,
    FraudSignal,
    NextBestEvidence,
    RiskScore,
    Transaction,
    User,
)

router = APIRouter()

# Load demo personas
DEMO_PERSONAS_PATH = Path(__file__).parent.parent.parent.parent / "data" / "synthetic" / "demo_personas.json"


def _load_demo_personas() -> list[dict]:
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "synthetic" / "demo_personas.json",
        Path(__file__).resolve().parent.parent.parent / "data" / "synthetic" / "demo_personas.json",
        Path("data/synthetic/demo_personas.json"),
        Path("backend/data/synthetic/demo_personas.json"),
    ]
    for path in candidates:
        if path.exists():
            with open(path) as f:
                return json.load(f)
    return []


@router.get("/scenarios")
async def list_scenarios(
    current_user: Annotated[CurrentUser, Depends(require_admin)],
):
    """List all available demo scenarios."""
    personas = _load_demo_personas()
    return {
        "scenarios": [
            {
                "scenario": p["scenario"],
                "display_name": p["display_name"],
                "persona_tag": p["persona_tag"],
                "description": p["description"],
            }
            for p in personas
        ]
    }


@router.post("/reset/{scenario}")
async def reset_scenario(
    scenario: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_admin)],
):
    """
    Deterministically reset a demo scenario to its initial state.
    Deletes all existing data, anomaly signals, documents, and scores for this persona and re-seeds it fresh.
    """
    from sqlalchemy import delete
    from app.models.models import (
        FraudSignal, RiskScore, Decision, ExtractedFeatures,
        AuditEvent, FinancialDocument, CopilotInteraction,
        NextBestEvidence, Transaction, FinancialAccount,
    )

    personas = _load_demo_personas()
    persona = next((p for p in personas if p["scenario"].upper() == scenario.upper()), None)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario}' not found")

    # Clean up all existing records associated with this persona
    existing_customers = await db.execute(
        select(Customer).where(Customer.persona_tag == persona["persona_tag"])
    )
    for customer in existing_customers.scalars().all():
        apps = await db.execute(select(Application).where(Application.customer_id == customer.id))
        app_ids = [a.id for a in apps.scalars().all()]
        if app_ids:
            await db.execute(delete(FraudSignal).where(FraudSignal.application_id.in_(app_ids)))
            await db.execute(delete(RiskScore).where(RiskScore.application_id.in_(app_ids)))
            await db.execute(delete(Decision).where(Decision.application_id.in_(app_ids)))
            await db.execute(delete(ExtractedFeatures).where(ExtractedFeatures.application_id.in_(app_ids)))
            await db.execute(delete(AuditEvent).where(AuditEvent.application_id.in_(app_ids)))
            await db.execute(delete(FinancialDocument).where(FinancialDocument.application_id.in_(app_ids)))
            await db.execute(delete(CopilotInteraction).where(CopilotInteraction.application_id.in_(app_ids)))
            await db.execute(delete(NextBestEvidence).where(NextBestEvidence.application_id.in_(app_ids)))
            await db.execute(delete(Application).where(Application.id.in_(app_ids)))

        accs = await db.execute(select(FinancialAccount).where(FinancialAccount.customer_id == customer.id))
        acc_ids = [a.id for a in accs.scalars().all()]
        if acc_ids:
            await db.execute(delete(Transaction).where(Transaction.account_id.in_(acc_ids)))
            await db.execute(delete(FinancialAccount).where(FinancialAccount.id.in_(acc_ids)))

        await db.delete(customer)

    await db.flush()

    # Re-seed golden baseline
    application_id = await _seed_demo_persona(db, persona)

    return {
        "status": "reset",
        "scenario": scenario,
        "application_id": str(application_id),
        "persona": persona["display_name"],
        "message": f"Scenario {scenario} ({persona['display_name']}) has been reset to initial state.",
    }


@router.post("/seed-all")
async def seed_all_scenarios(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_admin)],
):
    """Seed all 5 demo scenarios. Called once during setup."""
    personas = _load_demo_personas()
    if not personas:
        raise HTTPException(status_code=503, detail="Run: python backend/seed/synthetic_generator.py first")

    results = []
    for persona in personas:
        app_id = await _seed_demo_persona(db, persona)
        results.append({
            "scenario": persona["scenario"],
            "persona": persona["display_name"],
            "application_id": str(app_id),
        })

    return {"status": "seeded", "scenarios": results}


@router.get("/status")
async def demo_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_underwriter)],
):
    """Show current demo state — which scenarios are seeded and scored."""
    result = await db.execute(
        select(Customer, Application)
        .join(Application, Customer.id == Application.customer_id)
        .where(Customer.persona_tag.in_([
            "thin_file_ntc", "high_income_unstable", "moderate_disciplined",
            "high_volatility_suspicious", "ambiguous_ntc"
        ]))
        .order_by(Application.created_at.desc())
    )
    rows = result.all()

    # Deduplicate: keep only the most recent application per persona_tag
    seen_tags: set[str] = set()
    unique_rows = []
    for row in rows:
        customer, application = row[0], row[1]
        if customer.persona_tag not in seen_tags:
            seen_tags.add(customer.persona_tag)
            unique_rows.append((customer, application))

    # Preserve canonical display order
    ORDER = ["thin_file_ntc", "high_income_unstable", "moderate_disciplined",
             "high_volatility_suspicious", "ambiguous_ntc"]
    unique_rows.sort(key=lambda r: ORDER.index(r[0].persona_tag) if r[0].persona_tag in ORDER else 99)

    # Gather latest risk scores and decisions for each application
    status_list = []
    for customer, application in unique_rows:
        # Latest risk score
        score_result = await db.execute(
            select(RiskScore)
            .where(RiskScore.application_id == application.id)
            .order_by(RiskScore.computed_at.desc())
            .limit(1)
        )
        score = score_result.scalar_one_or_none()

        # Latest decision
        decision_result = await db.execute(
            select(Decision)
            .where(Decision.application_id == application.id)
            .order_by(Decision.decided_at.desc())
            .limit(1)
        )
        decision = decision_result.scalar_one_or_none()

        SCENARIO_MAP = {
            "thin_file_ntc": "A",
            "high_income_unstable": "B",
            "moderate_disciplined": "C",
            "high_volatility_suspicious": "D",
            "ambiguous_ntc": "E",
        }
        status_list.append({
            "scenario": SCENARIO_MAP.get(customer.persona_tag, "A"),
            "customer": customer.display_name,
            "customer_id": str(customer.id),
            "persona_tag": customer.persona_tag,
            "application_id": str(application.id),
            "status": application.status,
            "risk_probability": float(score.risk_probability) if score and score.risk_probability is not None else None,
            "risk_band": score.risk_band if score else None,
            "confidence": float(score.confidence) if score and score.confidence is not None else None,
            "pathway": decision.pathway if decision else None,
            "exposure_limit": float(decision.exposure_limit) if decision and decision.exposure_limit else None,
        })

    return {"seeded_scenarios": status_list}



# ─── Private helpers ────────────────────────────────────────────────────────

async def _seed_demo_persona(db: AsyncSession, persona: dict) -> UUID:
    """
    Seed a single demo persona with:
    - Customer record
    - Financial account
    - 6 months of synthetic transactions
    - Initial scoring
    """
    features = persona["features"]

    # Create customer
    customer = Customer(
        display_name=persona["display_name"],
        persona_tag=persona["persona_tag"],
        age=persona.get("age"),
        city=persona.get("city"),
    )
    db.add(customer)
    await db.flush()

    # Create application
    application = Application(
        customer_id=customer.id,
        status="intake",
        consent_given=True,
    )
    db.add(application)
    await db.flush()

    # Create financial account
    opened_at = (datetime.now(timezone.utc) - timedelta(days=int(features["account_age_months"] * 24 * 30))).date()
    account = FinancialAccount(
        customer_id=customer.id,
        account_type="bank",
        opened_at=opened_at,
    )
    db.add(account)
    await db.flush()

    # Generate synthetic transactions from features (thin-file gets ~1 month, established gets 6 months)
    transactions = _generate_transactions_from_features(account.id, features, persona.get("persona_tag", ""))
    for txn in transactions:
        db.add(txn)
    await db.flush()

    # Score the application
    await _score_application(db, application.id, customer, features, persona)

    db.add(AuditEvent(
        application_id=application.id,
        event_type="demo_scenario_seeded",
        actor="system",
        payload={"scenario": persona["scenario"], "persona_tag": persona["persona_tag"]},
    ))

    await db.flush()
    return application.id


def _generate_transactions_from_features(account_id: UUID, features: dict, persona_tag: str = "") -> list[Transaction]:
    """Generate realistic transactions based on persona type (thin-file gets ~1-2 months, established gets 6 months)."""
    transactions = []
    base_income = 45000 * (0.5 + features.get("income_consistency", 0.5))
    expense_ratio = features.get("expense_ratio", 0.6)
    payment_regularity = features.get("payment_regularity", 0.5)

    rng = np.random.default_rng(hash(str(account_id)) % (2**32))

    # Thin-file / NTC starts with only 1-2 months of history (~45 days)
    month_range = range(1, 0, -1) if persona_tag == "thin_file_ntc" else range(6, 0, -1)

    for month_offset in month_range:
        month_date = datetime.now(timezone.utc) - timedelta(days=month_offset * 30)

        # Income credit
        income_noise = rng.uniform(1 - (1 - features.get("income_consistency", 0.7)) * 0.3, 1.1)
        income = base_income * income_noise
        transactions.append(Transaction(
            account_id=account_id,
            amount=round(income, 2),
            direction="credit",
            category="income",
            merchant="Employer / Income Source",
            occurred_at=month_date + timedelta(days=int(rng.integers(1, 5))),
        ))

        # Expenses
        monthly_expense = income * expense_ratio
        categories = [
            ("rent", 0.35, "essential"),
            ("grocery", 0.15, "essential"),
            ("utilities", 0.08, "essential"),
            ("discretionary", 0.25, "discretionary"),
            ("emi", 0.17, "emi"),
        ]
        for cat_name, fraction, cat_type in categories:
            if rng.random() < max(0.5, payment_regularity):
                amount = monthly_expense * fraction * rng.uniform(0.8, 1.2)
                transactions.append(Transaction(
                    account_id=account_id,
                    amount=round(abs(amount), 2),
                    direction="debit",
                    category=cat_type,
                    merchant=f"{cat_name.title()} Payment",
                    occurred_at=month_date + timedelta(days=int(rng.integers(5, 25))),
                ))

    return transactions


async def _score_application(
    db: AsyncSession,
    application_id: UUID,
    customer: Customer,
    features: dict,
    persona: dict,
) -> None:
    """Run initial scoring for a demo persona."""
    from app.api.applications import (
        _compute_confidence,
        _compute_twin_dimensions,
        _detect_fraud_signals,
        _get_base_model,
        _load_models,
    )

    try:
        model, calibrated_model = _load_models()
        feature_array = np.array([list(features.values())], dtype=np.float32)

        persona_tag = persona.get("persona_tag", "")
        completeness = 0.35 if persona_tag in ("thin_file_ntc", "ambiguous_ntc") else 0.75
        warnings = ["Thin-file applicant: limited credit history (< 3 months)"] if persona_tag == "thin_file_ntc" else []

        risk_prob = float(calibrated_model.predict_proba(feature_array)[0, 1])
        confidence = _compute_confidence(calibrated_model, feature_array, completeness)
        base_model = _get_base_model(model, calibrated_model)
        shap_values = compute_shap_values(base_model, feature_array)
        risk_band = "low" if risk_prob < 0.35 else ("medium" if risk_prob < 0.60 else "high")
        twin_dims = _compute_twin_dimensions(features, risk_prob)
        fraud_signals = _detect_fraud_signals(features, persona_tag)
        has_high_fraud = any(f["severity"] == "high" for f in fraud_signals)

        pathway = determine_pathway(
            risk_probability=risk_prob,
            confidence=confidence,
            shap_values=shap_values,
            completeness_score=completeness,
            has_high_fraud_signal=has_high_fraud,
            feature_warnings=warnings,
        )

        # Persist
        db.add(ExtractedFeatures(
            application_id=application_id,
            feature_version=settings.feature_version,
            features=features,
        ))
        db.add(RiskScore(
            application_id=application_id,
            model_version=settings.model_version,
            risk_probability=risk_prob,
            risk_band=risk_band,
            confidence=confidence,
            shap_values=shap_values,
            triggered_by="demo_seed",
            **twin_dims,
        ))
        db.add(Decision(
            application_id=application_id,
            pathway=pathway.pathway.value,
            exposure_limit=pathway.exposure_limit,
            monitoring_period_days=pathway.monitoring_period_days,
            rationale_summary=pathway.rationale_summary,
            uncertainty_note=pathway.uncertainty_note,
            evidence_required=pathway.evidence_required,
            human_review_required=pathway.human_review_required,
            policy_version=pathway.policy_version,
            model_version=pathway.model_version,
        ))

        # Update application status
        from sqlalchemy import update
        await db.execute(
            update(Application)
            .where(Application.id == application_id)
            .values(status="decisioned")
        )

        # NBE
        nbe_recs = compute_next_best_evidence(shap_values, 0.70, [])
        for i, nbe in enumerate(nbe_recs[:3]):
            db.add(NextBestEvidence(
                application_id=application_id,
                recommended_evidence=nbe["evidence"],
                expected_uncertainty_reduction=nbe["expected_uncertainty_reduction"],
                reasoning=nbe["rationale"],
                rank=i + 1,
            ))

        for fs in fraud_signals:
            db.add(FraudSignal(
                application_id=application_id,
                signal_type=fs["signal_type"],
                severity=fs["severity"],
                confidence=fs["confidence"],
                description=fs["description"],
            ))

    except Exception as e:
        # Model not trained yet — seed without scoring
        import structlog
        structlog.get_logger().warning("demo_score_skipped", error=str(e))
