"""
LEDGER — XGBoost Training Pipeline
Trains the credit risk model on synthetic data with:
- Reproducible seed (deterministic outputs)
- Isotonic calibration (honest confidence scores)
- Model persistence to disk
- Validation metrics report

Run: python -m ml.train
"""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    brier_score_loss,
    classification_report,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from xgboost import XGBClassifier

RANDOM_SEED = 42
DATA_PATH = Path(__file__).parent.parent / "backend" / "data" / "synthetic" / "training_data.csv"
MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "xgb_credit_model.pkl"
CALIBRATOR_PATH = MODEL_DIR / "isotonic_calibrator.pkl"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

FEATURE_NAMES = [
    "income_consistency",
    "expense_ratio",
    "cashflow_stability",
    "payment_regularity",
    "balance_volatility",
    "recurring_payment_count",
    "days_since_last_payment",
    "liquidity_ratio",
    "debt_to_income",
    "transaction_velocity",
    "account_age_months",
    "income_sources_count",
]


def train_model(data_path: Path = DATA_PATH) -> None:
    """
    Full training pipeline:
    1. Load synthetic data
    2. Train/test split (80/20 stratified by label)
    3. Train XGBoost
    4. Isotonic calibration (post-hoc, 5-fold CV)
    5. Validate on held-out test set
    6. Save model + calibrator + metadata
    """
    print("=" * 60)
    print("LEDGER — XGBoost Training Pipeline")
    print("=" * 60)

    # ── 1. Load Data ────────────────────────────────────────────
    if not data_path.exists():
        print(f"Training data not found at {data_path}")
        print("Run: python -m backend.seed.synthetic_generator first")
        # Generate inline if not found
        from backend.seed.synthetic_generator import generate_synthetic_dataset
        df = generate_synthetic_dataset()
    else:
        df = pd.read_csv(data_path)

    print(f"Loaded {len(df)} records | Default rate: {df['label'].mean():.2%}")

    X = df[FEATURE_NAMES].values.astype(np.float32)
    y = df["label"].values.astype(np.int32)

    # ── 2. Train/Test Split ─────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED, stratify=y
    )
    print(f"Train: {len(X_train)} | Test: {len(X_test)}")

    # ── 3. XGBoost Training ─────────────────────────────────────
    # Class weight to handle potential imbalance
    pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)

    model = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=pos_weight,
        random_state=RANDOM_SEED,
        eval_metric="logloss",
        use_label_encoder=False,
        n_jobs=-1,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    print("\nBase model trained.")

    # ── 4. Isotonic Calibration ─────────────────────────────────
    # Isotonic regression makes probability outputs honest
    # "0.75 confidence means we're right ~75% of the time"
    calibrated_model = CalibratedClassifierCV(
        estimator=model,
        method="isotonic",  # Non-parametric, better for XGBoost than sigmoid
        cv=5,
    )
    calibrated_model.fit(X_train, y_train)
    print("Isotonic calibration fitted (5-fold CV).")

    # ── 5. Validation ────────────────────────────────────────────
    y_prob_raw = model.predict_proba(X_test)[:, 1]
    y_prob_cal = calibrated_model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob_cal > 0.5).astype(int)

    auc = roc_auc_score(y_test, y_prob_cal)
    brier_raw = brier_score_loss(y_test, y_prob_raw)
    brier_cal = brier_score_loss(y_test, y_prob_cal)

    print(f"\nTest Set Metrics:")
    print(f"  ROC-AUC:           {auc:.4f}")
    print(f"  Brier Score (raw): {brier_raw:.4f}")
    print(f"  Brier Score (cal): {brier_cal:.4f}  (lower = better calibrated)")
    print(f"\nClassification Report:\n{classification_report(y_test, y_pred)}")

    # Feature importance
    importance = dict(zip(FEATURE_NAMES, model.feature_importances_))
    print("\nFeature Importance (XGBoost):")
    for feat, imp in sorted(importance.items(), key=lambda x: -x[1]):
        bar = "=" * int(imp * 40)
        print(f"  {feat:<30} {imp:.4f} {bar}")

    # ── 6. Persist ───────────────────────────────────────────────
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    with open(CALIBRATOR_PATH, "wb") as f:
        pickle.dump(calibrated_model, f)

    # Save metadata
    import json
    from datetime import datetime, timezone
    metadata = {
        "model_version": "xgb-v1.0",
        "feature_version": "v1.0",
        "feature_names": FEATURE_NAMES,
        "n_estimators": 200,
        "calibration_method": "isotonic",
        "calibration_cv_folds": 5,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "roc_auc": round(auc, 4),
        "brier_score_calibrated": round(brier_cal, 4),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "data_note": "Trained on synthetic demonstration data. NOT real Synchrony data.",
    }
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nModel saved to: {MODEL_PATH}")
    print(f"Calibrator saved to: {CALIBRATOR_PATH}")
    print(f"Metadata saved to: {METADATA_PATH}")
    print("\n[SUCCESS] Training complete.")


if __name__ == "__main__":
    train_model()
