"""
LEDGER — Feature Engineering
Transforms raw transaction history into the 12-feature vector
used by the XGBoost risk model.

ALL features have a logical, defensible relationship to credit risk.
No random numbers. No fabricated signals.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)

# Feature version — bump when feature set changes
FEATURE_VERSION = "v1.0"

# Feature names in the exact order expected by the model
FEATURE_NAMES = [
    "income_consistency",       # 1 - Stability of monthly income (lower std/mean = more consistent)
    "expense_ratio",            # 2 - Total debits / total credits (lower = better)
    "cashflow_stability",       # 3 - Min monthly balance / avg balance (higher = more stable)
    "payment_regularity",       # 4 - Proportion of months with regular recurring payments
    "balance_volatility",       # 5 - Rolling std of daily balance normalized by mean
    "recurring_payment_count",  # 6 - Count of distinct recurring merchants (90 days)
    "days_since_last_payment",  # 7 - Recency of most recent outgoing payment (lower = recent)
    "liquidity_ratio",          # 8 - Avg balance / avg monthly expense
    "debt_to_income",           # 9 - Estimated recurring debt payments / income
    "transaction_velocity",     # 10 - Transaction count per 30 days
    "account_age_months",       # 11 - Age of primary account in months
    "income_sources_count",     # 12 - Number of distinct income sources
]


@dataclass
class FeatureVector:
    """Typed container for computed features + metadata."""
    income_consistency: float
    expense_ratio: float
    cashflow_stability: float
    payment_regularity: float
    balance_volatility: float
    recurring_payment_count: float
    days_since_last_payment: float
    liquidity_ratio: float
    debt_to_income: float
    transaction_velocity: float
    account_age_months: float
    income_sources_count: float

    # Metadata (not passed to model)
    feature_version: str = FEATURE_VERSION
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    warnings: list[str] = field(default_factory=list)
    completeness_score: float = 1.0  # 0-1, used by Next-Best-Evidence heuristic

    def to_model_array(self) -> np.ndarray:
        """Return flat array in FEATURE_NAMES order."""
        return np.array([
            self.income_consistency,
            self.expense_ratio,
            self.cashflow_stability,
            self.payment_regularity,
            self.balance_volatility,
            self.recurring_payment_count,
            self.days_since_last_payment,
            self.liquidity_ratio,
            self.debt_to_income,
            self.transaction_velocity,
            self.account_age_months,
            self.income_sources_count,
        ], dtype=np.float32)

    def to_dict(self) -> dict:
        return {
            name: float(getattr(self, name))
            for name in FEATURE_NAMES
        }

    def to_full_dict(self) -> dict:
        return {
            **self.to_dict(),
            "feature_version": self.feature_version,
            "completeness_score": self.completeness_score,
            "warnings": self.warnings,
        }


def compute_features(
    transactions: list[dict],
    account_opened_at: datetime | None = None,
    reference_date: datetime | None = None,
) -> FeatureVector:
    """
    Compute the full 12-feature vector from raw transaction history.

    Args:
        transactions: List of dicts with keys:
            amount, direction (credit|debit), category, merchant, occurred_at
        account_opened_at: When the primary account was opened
        reference_date: Date to compute features relative to (default: now)

    Returns:
        FeatureVector with all 12 features computed
    """
    ref_date = reference_date or datetime.now(timezone.utc)
    warnings_list: list[str] = []

    if not transactions:
        warnings_list.append("No transaction history — all features set to conservative defaults")
        return _empty_features(warnings_list)

    df = _to_dataframe(transactions, ref_date)

    if len(df) < 3:
        warnings_list.append("Very limited transaction history (< 3 transactions)")

    # ── Feature 1: Income Consistency ──────────────────────────────────────
    # Coefficient of variation (std/mean) of monthly credit amounts, inverted
    # Higher score = more consistent income
    income_consistency = _compute_income_consistency(df, warnings_list)

    # ── Feature 2: Expense Ratio ───────────────────────────────────────────
    # Total debits / total credits over the full window
    # Lower = spending less than earning (good)
    expense_ratio = _compute_expense_ratio(df, warnings_list)

    # ── Feature 3: Cashflow Stability ──────────────────────────────────────
    # Min monthly net cash / avg monthly net cash
    # Higher = never dips dangerously low
    cashflow_stability = _compute_cashflow_stability(df, warnings_list)

    # ── Feature 4: Payment Regularity ──────────────────────────────────────
    # Proportion of months with at least one recurring payment event
    payment_regularity = _compute_payment_regularity(df, warnings_list)

    # ── Feature 5: Balance Volatility ──────────────────────────────────────
    # Rolling std of monthly net balance / mean absolute balance
    # Lower = less volatile (good)
    balance_volatility = _compute_balance_volatility(df, warnings_list)

    # ── Feature 6: Recurring Payment Count ────────────────────────────────
    # Distinct recurring merchants in last 90 days (normalized to 0-1)
    recurring_payment_count = _compute_recurring_count(df, ref_date, warnings_list)

    # ── Feature 7: Days Since Last Payment ────────────────────────────────
    # Recency — normalized so 0 days = 1.0, 90+ days = 0.0
    days_since_last_payment = _compute_days_since_payment(df, ref_date, warnings_list)

    # ── Feature 8: Liquidity Ratio ─────────────────────────────────────────
    # Avg monthly credits / avg monthly debits — capped at 3.0, normalized
    liquidity_ratio = _compute_liquidity_ratio(df, warnings_list)

    # ── Feature 9: Debt-to-Income ─────────────────────────────────────────
    # Estimated recurring debt payments / avg monthly income
    # Lower = better
    debt_to_income = _compute_debt_to_income(df, warnings_list)

    # ── Feature 10: Transaction Velocity ──────────────────────────────────
    # Transaction count per 30 days, normalized to 0-1 (50 txn/mo = 1.0)
    transaction_velocity = _compute_transaction_velocity(df, ref_date, warnings_list)

    # ── Feature 11: Account Age ────────────────────────────────────────────
    # Age in months, normalized to 0-1 (24+ months = 1.0)
    account_age_months = _compute_account_age(account_opened_at, ref_date, warnings_list)

    # ── Feature 12: Income Sources ────────────────────────────────────────
    # Distinct income sources (employers/UPI IDs) normalized to 0-1
    income_sources_count = _compute_income_sources(df, warnings_list)

    # Completeness: fraction of features with full data
    completeness = _compute_completeness(
        transactions, account_opened_at, warnings_list
    )

    return FeatureVector(
        income_consistency=income_consistency,
        expense_ratio=expense_ratio,
        cashflow_stability=cashflow_stability,
        payment_regularity=payment_regularity,
        balance_volatility=balance_volatility,
        recurring_payment_count=recurring_payment_count,
        days_since_last_payment=days_since_last_payment,
        liquidity_ratio=liquidity_ratio,
        debt_to_income=debt_to_income,
        transaction_velocity=transaction_velocity,
        account_age_months=account_age_months,
        income_sources_count=income_sources_count,
        warnings=warnings_list,
        completeness_score=completeness,
    )


# ─── Private helpers ────────────────────────────────────────────────────────

def _to_dataframe(transactions: list[dict], ref_date: datetime) -> pd.DataFrame:
    df = pd.DataFrame(transactions)
    df["occurred_at"] = pd.to_datetime(df["occurred_at"], format='mixed', utc=True)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["month"] = df["occurred_at"].dt.to_period("M")
    df["is_credit"] = df["direction"] == "credit"
    df["is_debit"] = df["direction"] == "debit"
    return df


def _safe_cv(series: pd.Series) -> float:
    """Coefficient of variation, safe for zero-mean series."""
    mean = series.mean()
    if mean == 0:
        return 1.0
    return float(series.std() / abs(mean))


def _compute_income_consistency(df: pd.DataFrame, warn: list) -> float:
    credits = df[df["is_credit"]].groupby("month")["amount"].sum()
    if len(credits) < 2:
        warn.append("Insufficient income history for consistency calculation")
        return 0.3
    cv = _safe_cv(credits)
    # cv=0 → 1.0 (perfectly consistent), cv≥1 → 0.0
    return float(np.clip(1.0 - cv, 0.0, 1.0))


def _compute_expense_ratio(df: pd.DataFrame, warn: list) -> float:
    total_credit = df[df["is_credit"]]["amount"].sum()
    total_debit = df[df["is_debit"]]["amount"].sum()
    if total_credit == 0:
        warn.append("No income transactions detected")
        return 0.9  # Worst-case
    ratio = float(total_debit / total_credit)
    return float(np.clip(ratio, 0.0, 1.5))  # Cap at 1.5 (spending 150% of income)


def _compute_cashflow_stability(df: pd.DataFrame, warn: list) -> float:
    monthly = df.groupby("month").apply(
        lambda g: g[g["is_credit"]]["amount"].sum() - g[g["is_debit"]]["amount"].sum()
    )
    if len(monthly) < 2:
        return 0.4
    mean_cash = monthly.mean()
    min_cash = monthly.min()
    if mean_cash <= 0:
        return 0.1
    # min/mean ratio — if min is always positive relative to mean, highly stable
    stability = float(np.clip((min_cash / mean_cash + 1) / 2, 0.0, 1.0))
    return stability


def _compute_payment_regularity(df: pd.DataFrame, warn: list) -> float:
    recurring_cats = {"rent", "essential", "emi", "insurance"}
    recurring = df[df["category"].isin(recurring_cats)]
    if recurring.empty:
        warn.append("No recurring payments detected — payment regularity unknown")
        return 0.3
    months_with_recurring = recurring["month"].nunique()
    total_months = df["month"].nunique()
    if total_months == 0:
        return 0.3
    return float(months_with_recurring / total_months)


def _compute_balance_volatility(df: pd.DataFrame, warn: list) -> float:
    monthly_net = df.groupby("month").apply(
        lambda g: g[g["is_credit"]]["amount"].sum() - g[g["is_debit"]]["amount"].sum()
    )
    if len(monthly_net) < 3:
        warn.append("Balance volatility assessment limited (< 3 months history)")
        return 0.20
    cv = _safe_cv(monthly_net)
    # Higher CV = higher volatility = WORSE
    return float(np.clip(cv, 0.0, 2.0))


def _compute_recurring_count(df: pd.DataFrame, ref_date: datetime, warn: list) -> float:
    cutoff = ref_date - timedelta(days=90)
    recent = df[df["occurred_at"] >= cutoff]
    if recent.empty:
        return 0.0
    recurring_cats = {"rent", "essential", "emi", "insurance", "subscription"}
    recurring_recent = recent[recent["category"].isin(recurring_cats)]
    count = recurring_recent["merchant"].nunique() if "merchant" in recent.columns else 0
    return float(np.clip(count / 10.0, 0.0, 1.0))  # Normalize: 10 recurring = 1.0


def _compute_days_since_payment(df: pd.DataFrame, ref_date: datetime, warn: list) -> float:
    payments = df[df["is_debit"]]
    if payments.empty:
        warn.append("No debit transactions — days_since_last_payment unknown")
        return 0.0
    last_payment = payments["occurred_at"].max()
    days = (ref_date - last_payment).days
    return float(np.clip(1.0 - (days / 90.0), 0.0, 1.0))  # 0 days=1.0, 90+ days=0.0


def _compute_liquidity_ratio(df: pd.DataFrame, warn: list) -> float:
    months = df["month"].nunique()
    if months == 0:
        return 0.5
    avg_income = df[df["is_credit"]]["amount"].sum() / months
    avg_expense = df[df["is_debit"]]["amount"].sum() / months
    if avg_expense == 0:
        return 1.0
    ratio = float(avg_income / avg_expense)
    return float(np.clip(ratio / 3.0, 0.0, 1.0))  # 3x income/expense = 1.0


def _compute_debt_to_income(df: pd.DataFrame, warn: list) -> float:
    debt_cats = {"emi", "loan_payment", "credit_card"}
    debt_payments = df[df["category"].isin(debt_cats)]["amount"].sum()
    total_income = df[df["is_credit"]]["amount"].sum()
    if total_income == 0:
        warn.append("Cannot compute debt-to-income — no income detected")
        return 0.8
    dti = float(debt_payments / total_income)
    return float(np.clip(dti, 0.0, 1.0))


def _compute_transaction_velocity(df: pd.DataFrame, ref_date: datetime, warn: list) -> float:
    cutoff = ref_date - timedelta(days=30)
    recent_count = len(df[df["occurred_at"] >= cutoff])
    return float(np.clip(recent_count / 50.0, 0.0, 1.0))  # 50 txn/mo = 1.0


def _compute_account_age(
    account_opened_at: datetime | None,
    ref_date: datetime,
    warn: list,
) -> float:
    if account_opened_at is None:
        warn.append("Account opening date unknown — age set to conservative default")
        return 0.2
    months = (ref_date - account_opened_at).days / 30.0
    return float(np.clip(months / 24.0, 0.0, 1.0))  # 24 months = 1.0


def _compute_income_sources(df: pd.DataFrame, warn: list) -> float:
    income_df = df[df["is_credit"]]
    if income_df.empty:
        return 0.0
    sources = income_df["merchant"].nunique() if "merchant" in income_df.columns else 1
    return float(np.clip(sources / 3.0, 0.0, 1.0))  # 3 sources = 1.0


def _compute_completeness(
    transactions: list,
    account_opened_at: datetime | None,
    warn: list,
) -> float:
    score = 1.0
    if len(transactions) < 10:
        score -= 0.3
    if account_opened_at is None:
        score -= 0.2
    months_present = len(set(
        pd.to_datetime(t["occurred_at"], format='mixed', utc=True).to_period("M")
        for t in transactions
    )) if transactions else 0
    if months_present < 3:
        score -= 0.3
    return float(max(0.0, score))


def _empty_features(warnings_list: list) -> FeatureVector:
    """Conservative defaults for customers with no history."""
    return FeatureVector(
        income_consistency=0.2,
        expense_ratio=0.7,
        cashflow_stability=0.3,
        payment_regularity=0.2,
        balance_volatility=0.8,
        recurring_payment_count=0.0,
        days_since_last_payment=0.0,
        liquidity_ratio=0.3,
        debt_to_income=0.5,
        transaction_velocity=0.1,
        account_age_months=0.1,
        income_sources_count=0.0,
        warnings=warnings_list,
        completeness_score=0.0,
    )
