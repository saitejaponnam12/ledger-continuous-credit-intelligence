"""
LEDGER — Bounded Copilot Tools
Read-only tools the copilot agent can call.

ARCHITECTURAL GUARANTEE:
  Tools are READ-ONLY — no writes to decisions or risk_scores.
  The agent cannot override the decision engine.
  Tool list is finite and explicitly permitted.

Available tools:
  1. get_customer_profile(application_id)
  2. get_financial_evidence(application_id)
  3. get_model_explanation(application_id)
  4. get_policy(query) — RAG retrieval
  5. get_recent_events(application_id)
  6. get_credit_pathway(application_id)
  7. get_uncertainty(application_id)
  8. get_counterfactual(application_id, scenario)
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Application,
    AuditEvent,
    CopilotInteraction,
    Customer,
    Decision,
    ExtractedFeatures,
    FraudSignal,
    NextBestEvidence,
    RiskScore,
    Transaction,
    FinancialAccount,
)


async def get_customer_profile(
    db: AsyncSession,
    application_id: UUID,
) -> dict[str, Any]:
    """Tool 1: Get customer profile and application status."""
    result = await db.execute(
        select(Application, Customer)
        .join(Customer, Application.customer_id == Customer.id)
        .where(Application.id == application_id)
    )
    row = result.first()
    if not row:
        return {"error": "Application not found"}

    app, customer = row
    return {
        "customer_id": str(customer.id),
        "display_name": customer.display_name,
        "persona_tag": customer.persona_tag,
        "age": customer.age,
        "city": customer.city,
        "application_id": str(app.id),
        "application_status": app.status,
        "consent_given": app.consent_given,
        "created_at": app.created_at.isoformat(),
    }


async def get_financial_evidence(
    db: AsyncSession,
    application_id: UUID,
) -> dict[str, Any]:
    """Tool 2: Get latest extracted features as structured evidence."""
    result = await db.execute(
        select(ExtractedFeatures)
        .where(ExtractedFeatures.application_id == application_id)
        .order_by(desc(ExtractedFeatures.computed_at))
        .limit(1)
    )
    features = result.scalar_one_or_none()
    if not features:
        return {"error": "No features extracted yet", "application_id": str(application_id)}

    return {
        "feature_version": features.feature_version,
        "computed_at": features.computed_at.isoformat(),
        "features": features.features,
    }


async def get_model_explanation(
    db: AsyncSession,
    application_id: UUID,
) -> dict[str, Any]:
    """Tool 3: Get latest SHAP explanation and risk score."""
    result = await db.execute(
        select(RiskScore)
        .where(RiskScore.application_id == application_id)
        .order_by(desc(RiskScore.computed_at))
        .limit(1)
    )
    score = result.scalar_one_or_none()
    if not score:
        return {"error": "No risk score computed yet"}

    return {
        "risk_probability": float(score.risk_probability) if score.risk_probability else None,
        "risk_band": score.risk_band,
        "confidence": float(score.confidence) if score.confidence else None,
        "shap_values": score.shap_values,
        "model_version": score.model_version,
        "triggered_by": score.triggered_by,
        "computed_at": score.computed_at.isoformat(),
        "financial_twin": {
            "financial_stability": float(score.financial_stability) if score.financial_stability else None,
            "income_reliability": float(score.income_reliability) if score.income_reliability else None,
            "payment_discipline": float(score.payment_discipline) if score.payment_discipline else None,
            "liquidity": float(score.liquidity) if score.liquidity else None,
            "volatility": float(score.volatility) if score.volatility else None,
            "exposure_capacity": float(score.exposure_capacity) if score.exposure_capacity else None,
        },
    }


async def get_recent_events(
    db: AsyncSession,
    application_id: UUID,
    limit: int = 5,
) -> dict[str, Any]:
    """Tool 5: Get recent audit events for this application."""
    result = await db.execute(
        select(AuditEvent)
        .where(AuditEvent.application_id == application_id)
        .order_by(desc(AuditEvent.created_at))
        .limit(limit)
    )
    events = result.scalars().all()
    return {
        "recent_events": [
            {
                "event_type": e.event_type,
                "actor": e.actor,
                "created_at": e.created_at.isoformat(),
                "payload": e.payload,
            }
            for e in events
        ]
    }


async def get_credit_pathway(
    db: AsyncSession,
    application_id: UUID,
) -> dict[str, Any]:
    """Tool 6: Get the current Credit Pathway decision."""
    result = await db.execute(
        select(Decision)
        .where(Decision.application_id == application_id)
        .order_by(desc(Decision.decided_at))
        .limit(1)
    )
    decision = result.scalar_one_or_none()
    if not decision:
        return {"error": "No decision computed yet"}

    return {
        "pathway": decision.pathway,
        "exposure_limit": float(decision.exposure_limit) if decision.exposure_limit else None,
        "monitoring_period_days": int(decision.monitoring_period_days) if decision.monitoring_period_days else None,
        "rationale_summary": decision.rationale_summary,
        "uncertainty_note": decision.uncertainty_note,
        "evidence_required": decision.evidence_required,
        "human_review_required": decision.human_review_required,
        "policy_version": decision.policy_version,
        "model_version": decision.model_version,
        "decided_at": decision.decided_at.isoformat(),
    }


async def get_uncertainty(
    db: AsyncSession,
    application_id: UUID,
) -> dict[str, Any]:
    """Tool 7: Get uncertainty metrics and next-best-evidence recommendations."""
    # Confidence from latest score
    score_result = await db.execute(
        select(RiskScore)
        .where(RiskScore.application_id == application_id)
        .order_by(desc(RiskScore.computed_at))
        .limit(1)
    )
    score = score_result.scalar_one_or_none()

    # Next-best-evidence
    nbe_result = await db.execute(
        select(NextBestEvidence)
        .where(NextBestEvidence.application_id == application_id)
        .order_by(desc(NextBestEvidence.computed_at))
        .limit(5)
    )
    nbe_items = nbe_result.scalars().all()

    # Fraud signals
    fraud_result = await db.execute(
        select(FraudSignal)
        .where(FraudSignal.application_id == application_id)
        .order_by(desc(FraudSignal.detected_at))
    )
    fraud_signals = fraud_result.scalars().all()

    return {
        "confidence": float(score.confidence) if score and score.confidence else None,
        "risk_probability": float(score.risk_probability) if score and score.risk_probability else None,
        "next_best_evidence": [
            {
                "rank": i + 1,
                "recommended_evidence": nbe.recommended_evidence,
                "expected_uncertainty_reduction": float(nbe.expected_uncertainty_reduction) if nbe.expected_uncertainty_reduction else None,
                "estimation_method": "heuristic",
            }
            for i, nbe in enumerate(nbe_items)
        ],
        "fraud_signals": [
            {
                "signal_type": fs.signal_type,
                "severity": fs.severity,
                "detected_at": fs.detected_at.isoformat(),
            }
            for fs in fraud_signals
        ],
    }


# Alias for backward compatibility
get_next_best_evidence = get_uncertainty

