"""
LEDGER — SHAP Explainability Utilities
Wraps SHAP TreeExplainer for the XGBoost model.
All values shown in the UI come from this module — never fabricated.
"""
from __future__ import annotations

import numpy as np
import shap

from app.ml.feature_engineering import FEATURE_NAMES


def compute_shap_values(
    model,
    feature_array: np.ndarray,
) -> dict[str, float]:
    """
    Compute per-feature SHAP contributions for a single prediction.

    Args:
        model: Trained XGBoost classifier (Booster or XGBClassifier)
        feature_array: (1, n_features) numpy array

    Returns:
        Dict mapping feature_name → SHAP contribution (float)
        Positive = increases risk probability
        Negative = decreases risk probability
    """
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(feature_array)

    # For binary classification, shap_values shape: (1, n_features) or (n_classes, 1, n_features)
    if isinstance(shap_values, list):
        # Multi-output: take class 1 (risk class)
        values = shap_values[1][0]
    else:
        values = shap_values[0]

    return {
        feature: float(value)
        for feature, value in zip(FEATURE_NAMES, values, strict=True)
    }


def compute_shap_delta(
    old_shap: dict[str, float],
    new_shap: dict[str, float],
) -> dict[str, float]:
    """
    Compute the change in SHAP values between two scoring events.
    Used by the "What Changed?" interaction.

    Returns:
        Dict of feature → delta (positive = increased risk contribution)
    """
    all_features = set(old_shap) | set(new_shap)
    return {
        feature: new_shap.get(feature, 0.0) - old_shap.get(feature, 0.0)
        for feature in all_features
    }


def rank_shap_for_display(
    shap_values: dict[str, float],
    top_n: int = 6,
) -> dict:
    """
    Rank SHAP values for the Financial Twin explanation panel.

    Returns:
        {
            "positive": [{"feature": str, "label": str, "contribution": float}, ...],
            "negative": [{"feature": str, "label": str, "contribution": float}, ...]
        }
    """
    from app.ml.pathway_engine import _FEATURE_LABELS

    sorted_items = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)
    top_items = sorted_items[:top_n]

    positive = []
    negative = []

    for feature, contribution in top_items:
        entry = {
            "feature": feature,
            "label": _FEATURE_LABELS.get(feature, feature.replace("_", " ").title()),
            "contribution": round(contribution, 4),
        }
        if contribution >= 0:
            negative.append(entry)  # Positive SHAP = increases risk = bad
        else:
            positive.append(entry)  # Negative SHAP = decreases risk = good

    return {"positive": positive, "negative": negative}


def compute_next_best_evidence(
    shap_values: dict[str, float],
    completeness_score: float,
    feature_warnings: list[str],
) -> list[dict]:
    """
    Active Underwriting: rank evidence types by expected uncertainty reduction.

    This is an HONEST HEURISTIC — not mathematically rigorous active learning.
    The label "heuristic estimate" is displayed in the UI.

    Logic: Evidence that would most improve the most impactful missing/uncertain features
    is ranked highest. Expected reduction is estimated as:
        expected_reduction = |shap_contribution| * (1 - data_completeness_for_feature)

    Returns:
        List of dicts sorted by expected_uncertainty_reduction (descending)
    """
    # Feature → evidence type mapping
    evidence_map = {
        "income_consistency": {
            "evidence": "3 months verified salary slips or bank credit statements",
            "rationale": "Income consistency is a primary determinant but current history is limited.",
        },
        "payment_regularity": {
            "evidence": "3 months of recurring payment records (rent, EMI, utilities)",
            "rationale": "Payment regularity cannot be confirmed from available transactions.",
        },
        "account_age_months": {
            "evidence": "Bank account statement showing account opening date",
            "rationale": "Account age is unknown, significantly limiting trajectory assessment.",
        },
        "debt_to_income": {
            "evidence": "Loan statements or EMI payment records",
            "rationale": "Debt obligations cannot be estimated without explicit records.",
        },
        "cashflow_stability": {
            "evidence": "6-month bank statement showing monthly balance patterns",
            "rationale": "Cashflow stability requires longer transaction history.",
        },
        "liquidity_ratio": {
            "evidence": "Recent bank statements showing average balance levels",
            "rationale": "Liquidity assessment needs balance visibility over time.",
        },
    }

    recommendations = []

    for feature, info in evidence_map.items():
        shap_magnitude = abs(shap_values.get(feature, 0.0))
        has_warning = any(feature.split("_")[0] in w.lower() for w in feature_warnings)
        data_gap = 1.0 - completeness_score if has_warning else (0.5 if shap_magnitude > 0.05 else 0.2)
        expected_reduction = round(shap_magnitude * data_gap, 4)

        if expected_reduction > 0.01 or has_warning:
            recommendations.append({
                "evidence": info["evidence"],
                "rationale": info["rationale"],
                "expected_uncertainty_reduction": expected_reduction,
                "feature_affected": feature,
                "estimation_method": "heuristic",  # Honest labeling
            })

    # Sort by expected value
    recommendations.sort(key=lambda x: x["expected_uncertainty_reduction"], reverse=True)
    return recommendations[:5]
