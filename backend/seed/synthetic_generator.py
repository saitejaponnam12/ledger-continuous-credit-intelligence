"""
LEDGER — Synthetic Dataset Generator
Creates realistic, deterministic training data for XGBoost.

CRITICAL: Features and labels have LOGICAL relationships.
No random assignment. Each feature genuinely predicts the outcome.

5 Persona archetypes + random variations.
Deterministic: same seed → same dataset every run.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RANDOM_SEED = 42
N_CUSTOMERS = 800
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "synthetic"


@dataclass
class PersonaConfig:
    """Configuration for each synthetic persona type."""
    name: str
    tag: str
    # Feature ranges (min, max)
    income_consistency: tuple[float, float]
    expense_ratio: tuple[float, float]
    cashflow_stability: tuple[float, float]
    payment_regularity: tuple[float, float]
    balance_volatility: tuple[float, float]
    recurring_payment_count: tuple[float, float]
    days_since_last_payment: tuple[float, float]
    liquidity_ratio: tuple[float, float]
    debt_to_income: tuple[float, float]
    transaction_velocity: tuple[float, float]
    account_age_months: tuple[float, float]
    income_sources_count: tuple[float, float]
    # Outcome probability (P(default) — used to generate label)
    default_probability_base: float
    count: int


# ─── 5 Canonical Personas ───────────────────────────────────────────────────

PERSONAS: list[PersonaConfig] = [
    PersonaConfig(
        name="Strong Thin-File (NTC)",
        tag="thin_file_ntc",
        income_consistency=(0.70, 0.92),      # Stable income but new
        expense_ratio=(0.45, 0.65),            # Spends moderately
        cashflow_stability=(0.55, 0.80),       # Decent cushion
        payment_regularity=(0.30, 0.60),       # Some history
        balance_volatility=(0.15, 0.40),       # Low volatility
        recurring_payment_count=(0.20, 0.50),  # Few recurring
        days_since_last_payment=(0.70, 1.00),  # Recent activity
        liquidity_ratio=(0.55, 0.80),          # Reasonable liquidity
        debt_to_income=(0.05, 0.20),           # Low debt
        transaction_velocity=(0.25, 0.55),     # Moderate activity
        account_age_months=(0.05, 0.25),       # NEW — thin file
        income_sources_count=(0.33, 0.67),     # 1-2 sources
        default_probability_base=0.20,          # Actually low risk
        count=160,
    ),
    PersonaConfig(
        name="High Income, Unstable Cashflow",
        tag="high_income_unstable",
        income_consistency=(0.20, 0.50),       # Highly variable income
        expense_ratio=(0.65, 0.95),            # High spender
        cashflow_stability=(0.15, 0.45),       # Volatile balance
        payment_regularity=(0.50, 0.80),       # Pays regularly
        balance_volatility=(0.60, 1.00),       # High volatility
        recurring_payment_count=(0.40, 0.80),  # Many commitments
        days_since_last_payment=(0.60, 0.90),  # Mostly recent
        liquidity_ratio=(0.30, 0.65),          # Mediocre liquidity
        debt_to_income=(0.20, 0.45),           # Moderate debt
        transaction_velocity=(0.60, 0.90),     # High activity
        account_age_months=(0.40, 0.80),       # Established
        income_sources_count=(0.67, 1.00),     # Multiple (gig)
        default_probability_base=0.42,          # Medium risk
        count=160,
    ),
    PersonaConfig(
        name="Moderate Income, Exceptional Discipline",
        tag="moderate_disciplined",
        income_consistency=(0.80, 0.96),       # Very consistent
        expense_ratio=(0.35, 0.55),            # Low spending ratio
        cashflow_stability=(0.70, 0.95),       # Very stable
        payment_regularity=(0.85, 1.00),       # Always pays
        balance_volatility=(0.05, 0.25),       # Very low volatility
        recurring_payment_count=(0.50, 0.80),  # Regular commitments
        days_since_last_payment=(0.80, 1.00),  # Always recent
        liquidity_ratio=(0.70, 1.00),          # High liquidity
        debt_to_income=(0.05, 0.15),           # Very low debt
        transaction_velocity=(0.30, 0.60),     # Moderate
        account_age_months=(0.50, 1.00),       # Well-established
        income_sources_count=(0.33, 0.67),     # 1-2 stable sources
        default_probability_base=0.08,          # Very low risk
        count=160,
    ),
    PersonaConfig(
        name="High Volatility / Suspicious Activity",
        tag="high_volatility_suspicious",
        income_consistency=(0.05, 0.35),       # Erratic income
        expense_ratio=(0.85, 1.40),            # Over-spending
        cashflow_stability=(0.05, 0.30),       # Dangerously low
        payment_regularity=(0.10, 0.40),       # Irregular
        balance_volatility=(0.70, 1.50),       # Extreme volatility
        recurring_payment_count=(0.10, 0.35),  # Few recurring
        days_since_last_payment=(0.10, 0.50),  # Stale
        liquidity_ratio=(0.05, 0.30),          # Very low liquidity
        debt_to_income=(0.40, 0.90),           # High debt burden
        transaction_velocity=(0.70, 1.00),     # Unusual velocity
        account_age_months=(0.10, 0.50),       # Mixed
        income_sources_count=(0.10, 0.50),     # Few/unknown sources
        default_probability_base=0.78,          # High risk
        count=160,
    ),
    PersonaConfig(
        name="Ambiguous — Evidence Required",
        tag="ambiguous_ntc",
        income_consistency=(0.40, 0.70),       # Moderate consistency
        expense_ratio=(0.50, 0.75),            # Moderate spending
        cashflow_stability=(0.30, 0.60),       # Uncertain
        payment_regularity=(0.20, 0.55),       # Unclear pattern
        balance_volatility=(0.30, 0.65),       # Moderate volatility
        recurring_payment_count=(0.10, 0.40),  # Limited
        days_since_last_payment=(0.40, 0.80),  # Mixed recency
        liquidity_ratio=(0.30, 0.65),          # Moderate
        debt_to_income=(0.10, 0.35),           # Moderate
        transaction_velocity=(0.15, 0.45),     # Low activity
        account_age_months=(0.02, 0.15),       # Very new account
        income_sources_count=(0.10, 0.45),     # Unclear
        default_probability_base=0.45,          # Genuinely uncertain
        count=160,
    ),
]

# 5 fixed demo personas for deterministic demo scenarios
DEMO_PERSONAS = [
    {
        "id": "demo-001",
        "scenario": "A",
        "display_name": "Ananya Sharma",
        "persona_tag": "thin_file_ntc",
        "age": 26,
        "city": "Bengaluru",
        "features": {
            "income_consistency": 0.78,
            "expense_ratio": 0.58,
            "cashflow_stability": 0.62,
            "payment_regularity": 0.42,
            "balance_volatility": 0.28,
            "recurring_payment_count": 0.30,
            "days_since_last_payment": 0.85,
            "liquidity_ratio": 0.65,
            "debt_to_income": 0.08,
            "transaction_velocity": 0.38,
            "account_age_months": 0.12,
            "income_sources_count": 0.33,
        },
        "description": "Strong thin-file NTC applicant. Stable income but limited credit history.",
    },
    {
        "id": "demo-002",
        "scenario": "B",
        "display_name": "Rajesh Nair",
        "persona_tag": "high_income_unstable",
        "age": 34,
        "city": "Mumbai",
        "features": {
            "income_consistency": 0.32,
            "expense_ratio": 0.88,
            "cashflow_stability": 0.28,
            "payment_regularity": 0.65,
            "balance_volatility": 0.82,
            "recurring_payment_count": 0.60,
            "days_since_last_payment": 0.72,
            "liquidity_ratio": 0.40,
            "debt_to_income": 0.38,
            "transaction_velocity": 0.78,
            "account_age_months": 0.62,
            "income_sources_count": 0.78,
        },
        "description": "High income freelancer with volatile cashflow. Multiple income sources.",
    },
    {
        "id": "demo-003",
        "scenario": "C",
        "display_name": "Priya Menon",
        "persona_tag": "moderate_disciplined",
        "age": 31,
        "city": "Pune",
        "features": {
            "income_consistency": 0.91,
            "expense_ratio": 0.42,
            "cashflow_stability": 0.88,
            "payment_regularity": 0.96,
            "balance_volatility": 0.12,
            "recurring_payment_count": 0.70,
            "days_since_last_payment": 0.95,
            "liquidity_ratio": 0.85,
            "debt_to_income": 0.07,
            "transaction_velocity": 0.45,
            "account_age_months": 0.75,
            "income_sources_count": 0.50,
        },
        "description": "Salaried professional with exceptional financial discipline.",
    },
    {
        "id": "demo-004",
        "scenario": "D",
        "display_name": "Karan Mehta",
        "persona_tag": "high_volatility_suspicious",
        "age": 29,
        "city": "Delhi",
        "features": {
            "income_consistency": 0.15,
            "expense_ratio": 1.18,
            "cashflow_stability": 0.10,
            "payment_regularity": 0.22,
            "balance_volatility": 1.15,
            "recurring_payment_count": 0.18,
            "days_since_last_payment": 0.25,
            "liquidity_ratio": 0.12,
            "debt_to_income": 0.72,
            "transaction_velocity": 0.88,
            "account_age_months": 0.28,
            "income_sources_count": 0.22,
        },
        "description": "High transaction velocity with suspicious activity patterns.",
    },
    {
        "id": "demo-005",
        "scenario": "E",
        "display_name": "Divya Krishnan",
        "persona_tag": "ambiguous_ntc",
        "age": 24,
        "city": "Chennai",
        "features": {
            "income_consistency": 0.52,
            "expense_ratio": 0.62,
            "cashflow_stability": 0.42,
            "payment_regularity": 0.35,
            "balance_volatility": 0.48,
            "recurring_payment_count": 0.20,
            "days_since_last_payment": 0.58,
            "liquidity_ratio": 0.48,
            "debt_to_income": 0.18,
            "transaction_velocity": 0.28,
            "account_age_months": 0.06,
            "income_sources_count": 0.22,
        },
        "description": "Genuinely ambiguous case. System should request additional evidence.",
    },
]


def generate_synthetic_dataset(
    n_customers: int = N_CUSTOMERS,
    seed: int = RANDOM_SEED,
    output_dir: Path = OUTPUT_DIR,
) -> pd.DataFrame:
    """
    Generate a reproducible synthetic training dataset.

    Label generation logic:
    - Base probability comes from persona archetype
    - Adjusted by feature quality (features that are "good" reduce P(default))
    - Small Gaussian noise added for realistic variance
    - Final label: 1 = default (high risk), 0 = no default (low risk)

    This creates a genuine statistical relationship between features and labels
    that XGBoost can learn. NOT random assignment.
    """
    rng = np.random.default_rng(seed)
    random.seed(seed)

    records = []

    for persona in PERSONAS:
        for i in range(persona.count):
            features = _sample_features(persona, rng)
            label = _compute_label(features, persona.default_probability_base, rng)

            record = {
                "persona_tag": persona.tag,
                "label": int(label),
                **features,
            }
            records.append(record)

    df = pd.DataFrame(records)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)  # Shuffle

    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_dir / "training_data.csv", index=False)

    print(f"Generated {len(df)} synthetic customers")
    print(f"Default rate: {df['label'].mean():.2%}")
    print(f"Persona distribution:\n{df['persona_tag'].value_counts()}")

    return df


def _sample_features(persona: PersonaConfig, rng: np.random.Generator) -> dict[str, float]:
    """Sample feature values uniformly from persona's ranges."""
    feature_names = [
        "income_consistency", "expense_ratio", "cashflow_stability",
        "payment_regularity", "balance_volatility", "recurring_payment_count",
        "days_since_last_payment", "liquidity_ratio", "debt_to_income",
        "transaction_velocity", "account_age_months", "income_sources_count",
    ]
    features = {}
    for name in feature_names:
        low, high = getattr(persona, name)
        # Add small jitter (~5% noise)
        value = rng.uniform(low, high)
        value = float(np.clip(value, 0.0, 1.5))  # expense_ratio can exceed 1.0
        features[name] = round(value, 4)
    return features


def _compute_label(
    features: dict[str, float],
    base_probability: float,
    rng: np.random.Generator,
) -> bool:
    """
    Compute the binary default label from features.

    Feature contributions to default probability:
    + income_consistency: HIGH = reduces default risk
    + expense_ratio: HIGH = increases default risk
    + payment_regularity: HIGH = reduces default risk
    + balance_volatility: HIGH = increases default risk
    + debt_to_income: HIGH = increases default risk
    + liquidity_ratio: HIGH = reduces default risk
    """
    p = base_probability

    # Adjust by key features
    p -= (features["income_consistency"] - 0.5) * 0.25      # Good income = lower risk
    p += (features["expense_ratio"] - 0.6) * 0.20           # High expense = higher risk
    p -= (features["payment_regularity"] - 0.5) * 0.20      # Good payments = lower risk
    p += (features["balance_volatility"] - 0.5) * 0.15      # High volatility = higher risk
    p += (features["debt_to_income"] - 0.3) * 0.20          # High debt = higher risk
    p -= (features["liquidity_ratio"] - 0.5) * 0.15         # Good liquidity = lower risk
    p -= (features["account_age_months"] - 0.3) * 0.10      # Older account = lower risk

    # Add small noise
    p += rng.normal(0, 0.05)
    p = float(np.clip(p, 0.02, 0.98))

    return rng.random() < p


def save_demo_personas(output_dir: Path = OUTPUT_DIR) -> None:
    """Save the 5 fixed demo personas as JSON for deterministic seeding."""
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "demo_personas.json", "w") as f:
        json.dump(DEMO_PERSONAS, f, indent=2)
    print(f"Saved {len(DEMO_PERSONAS)} demo personas")


if __name__ == "__main__":
    generate_synthetic_dataset()
    save_demo_personas()
