"""
LEDGER — Events Router (Real-Time Pipeline + WebSocket)
POST /events/simulate → persist → recompute ML → broadcast via WebSocket
"""
from __future__ import annotations

import pickle
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated
from uuid import UUID

import numpy as np
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.applications import (
    _compute_confidence,
    _compute_twin_dimensions,
    _detect_fraud_signals,
    _get_base_model,
    _load_models,
)
from app.core.config import settings
from app.core.database import AsyncSessionLocal, get_db
from app.core.security import require_underwriter, CurrentUser, decode_token
from app.events.websocket_manager import (
    EVENT_MODEL_UPDATED,
    EVENT_PATHWAY_UPDATED,
    EVENT_TWIN_UPDATED,
    EVENT_EVIDENCE_RECEIVED,
    build_event_message,
    ws_manager,
)
from app.ml.feature_engineering import compute_features
from app.ml.pathway_engine import determine_pathway
from app.ml.shap_utils import compute_shap_values, compute_next_best_evidence, rank_shap_for_display
from app.models.models import (
    AuditEvent,
    Customer,
    Decision,
    ExtractedFeatures,
    FinancialAccount,
    FraudSignal,
    NextBestEvidence,
    RiskScore,
    Transaction,
    Application,
)

router = APIRouter()


class SimulateEventRequest(BaseModel):
    customer_id: UUID
    application_id: UUID
    event_type: str = Field(
        description="Event type",
        examples=["income_verified", "payment_made", "salary_credited", "suspicious_activity"]
    )
    amount: float | None = Field(None, ge=0)
    category: str | None = "income"
    merchant: str | None = None
    direction: str | None = "credit"  # credit | debit
    description: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "uuid-here",
                "application_id": "uuid-here",
                "event_type": "income_verified",
                "amount": 45000.0,
                "category": "income",
                "direction": "credit",
                "merchant": "TechCorp Solutions",
                "description": "Monthly salary credit — verified",
            }
        }


@router.post("/simulate")
async def simulate_event(
    body: SimulateEventRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(require_underwriter)],
):
    """
    Inject a new financial event and recompute the Financial Twin in real-time.

    Pipeline:
      1. Persist new transaction
      2. Recompute all features
      3. Recompute risk + SHAP
      4. Recompute Credit Pathway
      5. Broadcast via WebSocket to all subscribers

    This is a prototype event pipeline (not Kafka/Kinesis).
    Production evolution: event → Kinesis → consumer → recompute → WebSocket.
    """
    # Audit: event received
    db.add(AuditEvent(
        application_id=body.application_id,
        event_type=f"event_simulated:{body.event_type}",
        actor=f"underwriter:{current_user.email}",
        payload={"event_type": body.event_type, "amount": body.amount, "category": body.category},
    ))

    # 1. Persist transaction
    acc_result = await db.execute(
        select(FinancialAccount).where(FinancialAccount.customer_id == body.customer_id).limit(1)
    )
    account = acc_result.scalar_one_or_none()

    if not account:
        # Create account on-the-fly for demo
        account = FinancialAccount(
            customer_id=body.customer_id,
            account_type="bank",
        )
        db.add(account)
        await db.flush()

    transaction = Transaction(
        account_id=account.id,
        amount=body.amount or 0,
        direction=body.direction or "credit",
        category=body.category or "income",
        merchant=body.merchant or body.event_type,
        occurred_at=datetime.now(timezone.utc),
        is_synthetic_event=True,
        event_tag=body.event_type,
    )
    db.add(transaction)

    # If verified income/bank statement arrives, enrich with verified monthly payroll history
    if body.event_type in ("income_verified", "bank_statement_verified", "salary_credited"):
        for offset in range(2, 6):
            past_date = datetime.now(timezone.utc) - timedelta(days=offset * 30 + 2)
            db.add(Transaction(
                account_id=account.id,
                amount=body.amount or 48000.0,
                direction="credit",
                category="income",
                merchant=body.merchant or "TechCorp Solutions Payroll",
                occurred_at=past_date,
                is_synthetic_event=True,
                event_tag="verified_payroll_history",
            ))
    await db.flush()

    # 2. Fetch ALL transactions for this customer
    all_accounts_result = await db.execute(
        select(FinancialAccount).where(FinancialAccount.customer_id == body.customer_id)
    )
    all_accounts = all_accounts_result.scalars().all()

    all_transactions = []
    account_opened_at = None
    for acc in all_accounts:
        if acc.opened_at and (account_opened_at is None or acc.opened_at < account_opened_at):
            account_opened_at = datetime.combine(acc.opened_at, datetime.min.time()).replace(tzinfo=timezone.utc)

        txn_result = await db.execute(
            select(Transaction).where(Transaction.account_id == acc.id)
        )
        txns = txn_result.scalars().all()
        all_transactions.extend([
            {
                "amount": float(t.amount),
                "direction": t.direction,
                "category": t.category or "unknown",
                "merchant": t.merchant or "unknown",
                "occurred_at": t.occurred_at.isoformat(),
            }
            for t in txns
        ])

    # 3. Recompute features
    feature_vector = compute_features(all_transactions, account_opened_at)
    features_dict = feature_vector.to_dict()
    completeness = feature_vector.completeness_score
    feature_warnings = feature_vector.warnings

    # 4. Recompute risk
    model, calibrated_model = _load_models()
    feature_array = np.array([list(features_dict.values())], dtype=np.float32)

    risk_prob = float(calibrated_model.predict_proba(feature_array)[0, 1])
    confidence = _compute_confidence(calibrated_model, feature_array, completeness)

    base_model = _get_base_model(model, calibrated_model)
    shap_values = compute_shap_values(base_model, feature_array)

    risk_band = "low" if risk_prob < 0.35 else ("medium" if risk_prob < 0.60 else "high")
    twin_dims = _compute_twin_dimensions(features_dict, risk_prob)

    # Fraud signals
    customer_result = await db.execute(
        select(Customer).where(Customer.id == body.customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    fraud_signals = _detect_fraud_signals(features_dict, customer.persona_tag if customer else None)
    has_high_fraud = any(f["severity"] == "high" for f in fraud_signals)

    # 5. Credit Pathway
    pathway = determine_pathway(
        risk_probability=risk_prob,
        confidence=confidence,
        shap_values=shap_values,
        completeness_score=completeness,
        has_high_fraud_signal=has_high_fraud,
        feature_warnings=feature_warnings,
    )

    # Get previous score for delta
    prev_score_result = await db.execute(
        select(RiskScore)
        .where(RiskScore.application_id == body.application_id)
        .order_by(desc(RiskScore.computed_at))
        .limit(1)
    )
    prev_score = prev_score_result.scalar_one_or_none()
    prev_risk_prob = float(prev_score.risk_probability) if prev_score and prev_score.risk_probability else None

    # Persist new score
    new_score = RiskScore(
        application_id=body.application_id,
        model_version=settings.model_version,
        risk_probability=risk_prob,
        risk_band=risk_band,
        confidence=confidence,
        shap_values=shap_values,
        triggered_by=f"event_simulation:{body.event_type}",
        **twin_dims,
    )
    db.add(new_score)

    new_decision = Decision(
        application_id=body.application_id,
        pathway=pathway.pathway.value,
        exposure_limit=pathway.exposure_limit,
        monitoring_period_days=pathway.monitoring_period_days,
        rationale_summary=pathway.rationale_summary,
        uncertainty_note=pathway.uncertainty_note,
        evidence_required=pathway.evidence_required,
        human_review_required=pathway.human_review_required,
        policy_version=pathway.policy_version,
        model_version=pathway.model_version,
    )
    db.add(new_decision)

    # Update NBE
    nbe_recs = compute_next_best_evidence(shap_values, completeness, feature_warnings)
    for i, nbe in enumerate(nbe_recs):
        db.add(NextBestEvidence(
            application_id=body.application_id,
            recommended_evidence=nbe["evidence"],
            expected_uncertainty_reduction=nbe["expected_uncertainty_reduction"],
            reasoning=nbe["rationale"],
            rank=i + 1,
        ))

    db.add(AuditEvent(
        application_id=body.application_id,
        event_type="risk_recomputed",
        actor="system",
        payload={
            "trigger": body.event_type,
            "risk_probability": risk_prob,
            "pathway": pathway.pathway.value,
            "prev_risk_probability": prev_risk_prob,
        },
    ))

    await db.flush()

    # 6. WebSocket broadcast — the "live update" moment
    ws_payload = {
        "event_type": body.event_type,
        "risk_probability": round(risk_prob, 4),
        "prev_risk_probability": round(prev_risk_prob, 4) if prev_risk_prob else None,
        "risk_delta": round(risk_prob - prev_risk_prob, 4) if prev_risk_prob else None,
        "risk_band": risk_band,
        "confidence": round(confidence, 4),
        "pathway": pathway.to_dict(),
        "financial_twin": twin_dims,
        "shap_ranked": rank_shap_for_display(shap_values),
    }

    await ws_manager.broadcast(
        str(body.application_id),
        build_event_message(EVENT_TWIN_UPDATED, str(body.application_id), ws_payload),
    )

    return {
        "status": "processed",
        "application_id": str(body.application_id),
        "event_type": body.event_type,
        "risk_probability": round(risk_prob, 4),
        "prev_risk_probability": round(prev_risk_prob, 4) if prev_risk_prob else None,
        "risk_delta": round(risk_prob - prev_risk_prob, 4) if prev_risk_prob else None,
        "pathway": pathway.to_dict(),
        "financial_twin": twin_dims,
        "websocket_subscribers": ws_manager.active_connections(str(body.application_id)),
    }


@router.websocket("/ws/{application_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    application_id: str,
    token: str | None = None,
):
    """
    WebSocket endpoint for live Financial Twin updates.
    Subscribe to receive real-time score/pathway updates when events arrive.
    """
    # Token auth for WebSocket (passed as query param)
    if token:
        try:
            decode_token(token)
        except Exception:
            await websocket.close(code=1008)
            return

    await ws_manager.connect(websocket, application_id)
    try:
        while True:
            # Keep connection alive — actual data pushed from simulate_event
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, application_id)
