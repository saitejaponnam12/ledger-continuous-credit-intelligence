"""
LEDGER — SQLAlchemy Models
Complete database schema for the credit intelligence platform.
"""
import uuid
from datetime import datetime, timezone

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = lambda dims: JSON
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# USERS (Underwriters / Admins)
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="underwriter")  # underwriter | demo_admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)


# ============================================================
# CUSTOMERS (Applicants)
# ============================================================

class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name = Column(String(255), nullable=False)
    persona_tag = Column(String(100), nullable=True)  # thin_file_ntc | stable_salaried | etc.
    age = Column(Numeric(3, 0), nullable=True)
    city = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    applications = relationship("Application", back_populates="customer", cascade="all, delete-orphan")
    financial_accounts = relationship("FinancialAccount", back_populates="customer", cascade="all, delete-orphan")


# ============================================================
# APPLICATIONS
# ============================================================

class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="intake")  # intake | processing | decisioned | review
    consent_given = Column(Boolean, default=False)
    assigned_underwriter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    customer = relationship("Customer", back_populates="applications")
    documents = relationship("FinancialDocument", back_populates="application", cascade="all, delete-orphan")
    extracted_features = relationship("ExtractedFeatures", back_populates="application", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="application", cascade="all, delete-orphan", order_by="RiskScore.computed_at")
    fraud_signals = relationship("FraudSignal", back_populates="application", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="application", cascade="all, delete-orphan")
    next_best_evidence = relationship("NextBestEvidence", back_populates="application", cascade="all, delete-orphan")
    copilot_interactions = relationship("CopilotInteraction", back_populates="application", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="application", cascade="all, delete-orphan")


# ============================================================
# FINANCIAL ACCOUNTS
# ============================================================

class FinancialAccount(Base):
    __tablename__ = "financial_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    account_type = Column(String(50))  # bank | upi | wallet
    opened_at = Column(Date, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)

    customer = relationship("Customer", back_populates="financial_accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")


# ============================================================
# TRANSACTIONS
# ============================================================

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("financial_accounts.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    direction = Column(String(10), nullable=False)  # credit | debit
    category = Column(String(50))  # income | rent | essential | discretionary | transfer
    merchant = Column(String(255), nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_synthetic_event = Column(Boolean, default=False)
    event_tag = Column(String(100), nullable=True)  # Tags demo-triggered events

    account = relationship("FinancialAccount", back_populates="transactions")


# ============================================================
# FINANCIAL DOCUMENTS
# ============================================================

class FinancialDocument(Base):
    __tablename__ = "financial_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True)
    doc_type = Column(String(50))  # bank_statement | salary_slip | utility_bill
    storage_path = Column(String(500), nullable=True)
    extraction_status = Column(String(50), default="pending")  # pending | extracted | failed | needs_review
    extracted_fields = Column(JSON, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    application = relationship("Application", back_populates="documents")


# ============================================================
# EXTRACTED FEATURES (versioned per computation)
# ============================================================

class ExtractedFeatures(Base):
    __tablename__ = "extracted_features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True)
    feature_version = Column(String(20), nullable=False)
    features = Column(JSON, nullable=False)  # {income_consistency, expense_ratio, ...}
    computed_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    application = relationship("Application", back_populates="extracted_features")


# ============================================================
# RISK SCORES (versioned, append-only trajectory)
# ============================================================

class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True)
    model_version = Column(String(50), nullable=False)
    risk_probability = Column(Numeric(5, 4), nullable=True)       # 0.0 - 1.0
    risk_band = Column(String(20), nullable=True)                  # low | medium | high
    confidence = Column(Numeric(5, 4), nullable=True)             # calibrated confidence
    shap_values = Column(JSON, nullable=True)                     # {feature: contribution}
    triggered_by = Column(String(100), nullable=True)             # initial | event_simulation | counterfactual
    computed_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    # Financial twin dimensions (stored alongside risk score)
    financial_stability = Column(Numeric(5, 4), nullable=True)
    income_reliability = Column(Numeric(5, 4), nullable=True)
    payment_discipline = Column(Numeric(5, 4), nullable=True)
    liquidity = Column(Numeric(5, 4), nullable=True)
    volatility = Column(Numeric(5, 4), nullable=True)
    exposure_capacity = Column(Numeric(12, 2), nullable=True)

    application = relationship("Application", back_populates="risk_scores")


# ============================================================
# FRAUD SIGNALS
# ============================================================

class FraudSignal(Base):
    __tablename__ = "fraud_signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True)
    signal_type = Column(String(100))  # velocity | device_mismatch | timing_anomaly | amount_spike
    severity = Column(String(20))      # low | medium | high
    confidence = Column(Numeric(5, 4), nullable=True)
    description = Column(Text, nullable=True)
    detected_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    application = relationship("Application", back_populates="fraud_signals")


# ============================================================
# DECISIONS (Credit Pathways — append-only)
# ============================================================

class Decision(Base):
    __tablename__ = "decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True)
    pathway = Column(String(50), nullable=False)  # full_approval | conditional_approval | request_evidence | human_review | decline
    exposure_limit = Column(Numeric(12, 2), nullable=True)        # In INR
    monitoring_period_days = Column(Numeric(5, 0), nullable=True)
    rationale_summary = Column(Text, nullable=True)
    uncertainty_note = Column(Text, nullable=True)
    evidence_required = Column(Text, nullable=True)
    human_review_required = Column(Boolean, default=False)
    policy_version = Column(String(50), nullable=True)
    model_version = Column(String(50), nullable=True)
    decided_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    application = relationship("Application", back_populates="decisions")


# ============================================================
# NEXT BEST EVIDENCE (Active Underwriting)
# ============================================================

class NextBestEvidence(Base):
    __tablename__ = "next_best_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True)
    recommended_evidence = Column(Text)
    expected_uncertainty_reduction = Column(Numeric(5, 4), nullable=True)  # Heuristic estimate
    reasoning = Column(Text, nullable=True)
    rank = Column(Numeric(3, 0), nullable=True)  # Priority rank
    computed_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    application = relationship("Application", back_populates="next_best_evidence")


# ============================================================
# POLICY DOCUMENTS (RAG source)
# ============================================================

class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    policy_version = Column(String(50), nullable=True)
    doc_category = Column(String(100), nullable=True)  # underwriting | responsible_ai | eligibility | evidence
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    chunks = relationship("PolicyChunk", back_populates="document", cascade="all, delete-orphan")


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_document_id = Column(UUID(as_uuid=True), ForeignKey("policy_documents.id"), nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Numeric(5, 0), nullable=True)
    embedding = Column(JSON, nullable=True)  # all-MiniLM-L6-v2 → 384 dims (JSON or vector)

    document = relationship("PolicyDocument", back_populates="chunks")


# ============================================================
# COPILOT INTERACTIONS (logged for governance)
# ============================================================

class CopilotInteraction(Base):
    __tablename__ = "copilot_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    query = Column(Text, nullable=False)
    retrieved_chunks = Column(JSON, nullable=True)   # Which policy chunks were used
    tool_calls = Column(JSON, nullable=True)          # Which bounded tools were invoked
    response = Column(Text, nullable=True)
    llm_provider = Column(String(50), nullable=True)  # ollama | mock
    latency_ms = Column(Numeric(10, 0), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    application = relationship("Application", back_populates="copilot_interactions")


# ============================================================
# AUDIT EVENTS (append-only governance log)
# ============================================================

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    actor = Column(String(100), nullable=False)           # system | underwriter:{email} | copilot
    actor_user_id = Column(UUID(as_uuid=True), nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    application = relationship("Application", back_populates="audit_events")
