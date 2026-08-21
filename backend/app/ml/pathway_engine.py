"""
LEDGER — Credit Pathway Engine
Deterministic business-rule layer that transforms ML output → Credit Pathway.

The XGBoost model provides risk_probability + confidence.
This engine applies policy-defined rules to select the pathway.

The LLM never touches this logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.core.config import settings


class CreditPathway(str, Enum):
    FULL_APPROVAL = "full_approval"
    CONDITIONAL_APPROVAL = "conditional_approval"
    REQUEST_EVIDENCE = "request_evidence"
    HUMAN_REVIEW = "human_review"
    TRANSPARENT_DECLINE = "transparent_decline"


# Pathway labels for display
PATHWAY_LABELS = {
    CreditPathway.FULL_APPROVAL: "Full Approval",
    CreditPathway.CONDITIONAL_APPROVAL: "Conditional Approval",
    CreditPathway.REQUEST_EVIDENCE: "Request Additional Evidence",
    CreditPathway.HUMAN_REVIEW: "Human Review Required",
    CreditPathway.TRANSPARENT_DECLINE: "Transparent Decline",
}

PATHWAY_COLORS = {
    CreditPathway.FULL_APPROVAL: "#10b981",          # emerald
    CreditPathway.CONDITIONAL_APPROVAL: "#3b82f6",   # blue
    CreditPathway.REQUEST_EVIDENCE: "#f59e0b",        # amber
    CreditPathway.HUMAN_REVIEW: "#8b5cf6",            # violet
    CreditPathway.TRANSPARENT_DECLINE: "#ef4444",     # red
}

# Exposure limits by risk band (in INR)
EXPOSURE_LIMITS = {
    CreditPathway.FULL_APPROVAL: 100_000,
    CreditPathway.CONDITIONAL_APPROVAL: 50_000,
    CreditPathway.REQUEST_EVIDENCE: None,
    CreditPathway.HUMAN_REVIEW: None,
    CreditPathway.TRANSPARENT_DECLINE: 0,
}

# Monitoring periods (days)
MONITORING_PERIODS = {
    CreditPathway.FULL_APPROVAL: 90,
    CreditPathway.CONDITIONAL_APPROVAL: 60,
    CreditPathway.REQUEST_EVIDENCE: None,
    CreditPathway.HUMAN_REVIEW: None,
    CreditPathway.TRANSPARENT_DECLINE: None,
}


@dataclass
class PathwayDecision:
    """The final Credit Pathway output — the product's decision artifact."""
    pathway: CreditPathway
    label: str
    exposure_limit: Optional[float]       # INR
    monitoring_period_days: Optional[int]
    confidence: float
    rationale_summary: str
    uncertainty_note: str
    evidence_required: Optional[str]
    human_review_required: bool
    policy_version: str
    model_version: str
    decided_at: datetime
    color: str

    # Interpretability
    primary_risk_drivers: list[str]       # Top negative SHAP contributors
    primary_strength_drivers: list[str]   # Top positive SHAP contributors
    risk_probability: float

    def to_dict(self) -> dict:
        return {
            "pathway": self.pathway.value,
            "label": self.label,
            "exposure_limit": self.exposure_limit,
            "monitoring_period_days": self.monitoring_period_days,
            "confidence": round(self.confidence, 4),
            "rationale_summary": self.rationale_summary,
            "uncertainty_note": self.uncertainty_note,
            "evidence_required": self.evidence_required,
            "human_review_required": self.human_review_required,
            "policy_version": self.policy_version,
            "model_version": self.model_version,
            "decided_at": self.decided_at.isoformat(),
            "color": self.color,
            "primary_risk_drivers": self.primary_risk_drivers,
            "primary_strength_drivers": self.primary_strength_drivers,
            "risk_probability": round(self.risk_probability, 4),
        }


def determine_pathway(
    risk_probability: float,
    confidence: float,
    shap_values: dict[str, float],
    completeness_score: float,
    has_high_fraud_signal: bool = False,
    has_medium_fraud_signal: bool = False,
    feature_warnings: list[str] | None = None,
) -> PathwayDecision:
    """
    Deterministic Credit Pathway Engine.

    Decision rules (applied in priority order):
    1. High fraud signal → Human Review (overrides everything)
    2. Low confidence (< 0.45) OR low completeness → Request Evidence
    3. High risk (> 0.68) → Transparent Decline
    4. Medium-high risk (0.48-0.68) + medium confidence → Human Review
    5. Low-medium risk (< 0.40) + good confidence → Conditional or Full Approval
    6. Very low risk (< 0.22) + high confidence → Full Approval

    These thresholds encode the policy. They are not ML outputs.
    """
    warnings = feature_warnings or []

    # ── Extract interpretability from SHAP ────────────────────────────────
    strength_drivers, risk_drivers = _extract_shap_drivers(shap_values)

    # ── Rule 1: High fraud → Human Review ─────────────────────────────────
    if has_high_fraud_signal:
        return PathwayDecision(
            pathway=CreditPathway.HUMAN_REVIEW,
            label=PATHWAY_LABELS[CreditPathway.HUMAN_REVIEW],
            exposure_limit=None,
            monitoring_period_days=None,
            confidence=confidence,
            rationale_summary="Anomalous behavioral patterns detected requiring manual verification.",
            uncertainty_note="Fraud signals present. Model output cannot be trusted without human review.",
            evidence_required="Identity verification and transaction explanation required.",
            human_review_required=True,
            policy_version="v1.2",
            model_version=settings.model_version,
            decided_at=datetime.now(timezone.utc),
            color=PATHWAY_COLORS[CreditPathway.HUMAN_REVIEW],
            primary_risk_drivers=risk_drivers,
            primary_strength_drivers=strength_drivers,
            risk_probability=risk_probability,
        )

    # ── Rule 2: Insufficient data → Request Evidence ───────────────────────
    if confidence < 0.60 or completeness_score < 0.50 or len(warnings) >= 2 or any("thin-file" in w.lower() or "insufficient" in w.lower() for w in warnings):
        missing = _identify_missing_evidence(shap_values, completeness_score, warnings)
        return PathwayDecision(
            pathway=CreditPathway.REQUEST_EVIDENCE,
            label=PATHWAY_LABELS[CreditPathway.REQUEST_EVIDENCE],
            exposure_limit=None,
            monitoring_period_days=None,
            confidence=confidence,
            rationale_summary="Insufficient evidence to make a reliable credit assessment. Thin-file applicant with limited payment history.",
            uncertainty_note=f"Model confidence is {confidence:.0%}. Additional verified income or bank statement evidence would meaningfully improve accuracy.",
            evidence_required=missing or "3 months verified salary slips or bank credit statements",
            human_review_required=False,
            policy_version="v1.2",
            model_version=settings.model_version,
            decided_at=datetime.now(timezone.utc),
            color=PATHWAY_COLORS[CreditPathway.REQUEST_EVIDENCE],
            primary_risk_drivers=risk_drivers,
            primary_strength_drivers=strength_drivers,
            risk_probability=risk_probability,
        )

    # ── Rule 3: High risk → Transparent Decline ────────────────────────────
    if risk_probability > 0.68:
        return PathwayDecision(
            pathway=CreditPathway.TRANSPARENT_DECLINE,
            label=PATHWAY_LABELS[CreditPathway.TRANSPARENT_DECLINE],
            exposure_limit=0,
            monitoring_period_days=None,
            confidence=confidence,
            rationale_summary=f"Current financial trajectory indicates elevated credit risk ({risk_probability:.0%} probability).",
            uncertainty_note="This assessment is based on available evidence. New evidence may change this pathway.",
            evidence_required=None,
            human_review_required=False,
            policy_version="v1.2",
            model_version=settings.model_version,
            decided_at=datetime.now(timezone.utc),
            color=PATHWAY_COLORS[CreditPathway.TRANSPARENT_DECLINE],
            primary_risk_drivers=risk_drivers,
            primary_strength_drivers=strength_drivers,
            risk_probability=risk_probability,
        )

    # ── Rule 4: Elevated risk + medium confidence → Human Review ───────────
    if 0.48 <= risk_probability <= 0.68 and 0.45 <= confidence < 0.68:
        return PathwayDecision(
            pathway=CreditPathway.HUMAN_REVIEW,
            label=PATHWAY_LABELS[CreditPathway.HUMAN_REVIEW],
            exposure_limit=None,
            monitoring_period_days=None,
            confidence=confidence,
            rationale_summary="Risk profile is ambiguous. Conflicting signals require underwriter judgment.",
            uncertainty_note="Model confidence is moderate. Human review adds important oversight.",
            evidence_required=None,
            human_review_required=True,
            policy_version="v1.2",
            model_version=settings.model_version,
            decided_at=datetime.now(timezone.utc),
            color=PATHWAY_COLORS[CreditPathway.HUMAN_REVIEW],
            primary_risk_drivers=risk_drivers,
            primary_strength_drivers=strength_drivers,
            risk_probability=risk_probability,
        )

    # ── Rule 5: Full Approval — very low risk, high confidence ─────────────
    if risk_probability < 0.22 and confidence >= 0.75:
        return PathwayDecision(
            pathway=CreditPathway.FULL_APPROVAL,
            label=PATHWAY_LABELS[CreditPathway.FULL_APPROVAL],
            exposure_limit=float(EXPOSURE_LIMITS[CreditPathway.FULL_APPROVAL]),
            monitoring_period_days=MONITORING_PERIODS[CreditPathway.FULL_APPROVAL],
            confidence=confidence,
            rationale_summary="Strong financial trajectory with high confidence. All risk indicators within acceptable bounds.",
            uncertainty_note="This assessment reflects current evidence only. Trajectory monitoring continues.",
            evidence_required=None,
            human_review_required=False,
            policy_version="v1.2",
            model_version=settings.model_version,
            decided_at=datetime.now(timezone.utc),
            color=PATHWAY_COLORS[CreditPathway.FULL_APPROVAL],
            primary_risk_drivers=risk_drivers,
            primary_strength_drivers=strength_drivers,
            risk_probability=risk_probability,
        )

    # ── Rule 6 (default): Conditional Approval ─────────────────────────────
    # Covers risk_probability 0.22-0.48, or good confidence but moderate risk
    # Exposure scaled inversely with risk
    exposure = _calculate_conditional_exposure(risk_probability, confidence)
    monitoring = _calculate_monitoring_period(risk_probability)

    return PathwayDecision(
        pathway=CreditPathway.CONDITIONAL_APPROVAL,
        label=PATHWAY_LABELS[CreditPathway.CONDITIONAL_APPROVAL],
        exposure_limit=float(exposure),
        monitoring_period_days=monitoring,
        confidence=confidence,
        rationale_summary=f"Positive financial indicators with some uncertainty. Conditional approval at ₹{exposure:,.0f} exposure.",
        uncertainty_note=_build_uncertainty_note(risk_drivers, completeness_score),
        evidence_required=None,
        human_review_required=False,
        policy_version="v1.2",
        model_version=settings.model_version,
        decided_at=datetime.now(timezone.utc),
        color=PATHWAY_COLORS[CreditPathway.CONDITIONAL_APPROVAL],
        primary_risk_drivers=risk_drivers,
        primary_strength_drivers=strength_drivers,
        risk_probability=risk_probability,
    )


# ─── Private helpers ────────────────────────────────────────────────────────

def _extract_shap_drivers(shap_values: dict[str, float]) -> tuple[list[str], list[str]]:
    """Split SHAP values into positive (strength) and negative (risk) contributors."""
    if not shap_values:
        return [], []

    sorted_shap = sorted(shap_values.items(), key=lambda x: x[1])
    risk_drivers = [
        _humanize_feature(k) for k, v in sorted_shap if v < -0.02
    ][:3]
    strength_drivers = [
        _humanize_feature(k) for k, v in reversed(sorted_shap) if v > 0.02
    ][:3]
    return strength_drivers, risk_drivers


_FEATURE_LABELS = {
    "income_consistency": "Consistent income",
    "expense_ratio": "Expense ratio",
    "cashflow_stability": "Cashflow stability",
    "payment_regularity": "Payment regularity",
    "balance_volatility": "Balance volatility",
    "recurring_payment_count": "Recurring payments",
    "days_since_last_payment": "Recent payment activity",
    "liquidity_ratio": "Liquidity",
    "debt_to_income": "Debt-to-income ratio",
    "transaction_velocity": "Transaction activity",
    "account_age_months": "Account history length",
    "income_sources_count": "Income sources",
}


def _humanize_feature(feature_name: str) -> str:
    return _FEATURE_LABELS.get(feature_name, feature_name.replace("_", " ").title())


def _identify_missing_evidence(
    shap_values: dict[str, float],
    completeness: float,
    warnings: list[str],
) -> str:
    pieces = []
    if completeness < 0.6:
        pieces.append("3+ months of bank statement history")
    if any("income" in w.lower() for w in warnings):
        pieces.append("verified income documentation (salary slip or Form 16)")
    if any("recurring" in w.lower() for w in warnings):
        pieces.append("evidence of recurring payment obligations")
    if not pieces:
        pieces.append("additional transaction history to improve confidence")
    return "; ".join(pieces)


def _calculate_conditional_exposure(risk_probability: float, confidence: float) -> int:
    """Scale exposure from ₹20,000 to ₹80,000 based on risk + confidence."""
    base_exposure = 80_000
    risk_penalty = risk_probability * 60_000
    confidence_bonus = confidence * 20_000
    exposure = base_exposure - risk_penalty + confidence_bonus - 20_000
    # Round to nearest ₹10,000
    exposure = round(max(20_000, min(80_000, exposure)) / 10_000) * 10_000
    return int(exposure)


def _calculate_monitoring_period(risk_probability: float) -> int:
    """30-90 days monitoring based on risk level."""
    if risk_probability < 0.3:
        return 30
    if risk_probability < 0.45:
        return 60
    return 90


def _build_uncertainty_note(risk_drivers: list[str], completeness: float) -> str:
    parts = []
    if risk_drivers:
        parts.append(f"Key uncertainty factors: {', '.join(risk_drivers[:2])}")
    if completeness < 0.7:
        parts.append("Limited transaction history reduces model confidence")
    if not parts:
        parts.append("Trajectory monitoring will continue through the review period")
    return ". ".join(parts) + "."
