"""SQLAlchemy database models."""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    Text,
    Boolean,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    tenant_id = Column(String(50), index=True, nullable=False, default="default")
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClaimMaster(Base):
    """Master table for all claims with validation results."""

    __tablename__ = "claims_master"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Claim Information
    claim_id = Column(String(50), unique=True, nullable=False, index=True)
    encounter_type = Column(String(20))
    service_date = Column(DateTime)
    national_id = Column(String(20))
    member_id = Column(String(20))
    facility_id = Column(String(20), index=True)
    unique_id = Column(String(50))
    diagnosis_codes = Column(ARRAY(String))
    service_code = Column(String(20), index=True)
    paid_amount_aed = Column(Numeric(10, 2))
    approval_number = Column(String(50), nullable=True)

    # Validation Results
    status = Column(String(20), index=True)
    error_type = Column(String(50), index=True)
    error_explanation = Column(Text)
    recommended_action = Column(Text)

    # Detailed Error Tracking
    technical_errors = Column(JSON)
    medical_errors = Column(JSON)
    data_quality_errors = Column(JSON)

    # LLM Evaluation
    llm_evaluated = Column(Boolean, default=False)
    llm_confidence_score = Column(Numeric(3, 2))
    llm_explanation = Column(Text)
    llm_retrieved_rules = Column(JSON)

    # Multi-tenant & Audit
    tenant_id = Column(String(50), index=True, nullable=False)
    batch_id = Column(String(50), index=True, nullable=True)
    uploaded_by = Column(String(100))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    processing_duration_ms = Column(Integer)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    rule_version = Column(String(20))

    __table_args__ = (
        Index("idx_tenant_status", "tenant_id", "status"),
        Index("idx_tenant_error_type", "tenant_id", "error_type"),
    )


class RuleDocument(Base):
    """Store rule documents for RAG retrieval."""

    __tablename__ = "rule_documents"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), index=True)
    rule_type = Column(String(20))
    content = Column(Text)
    embedding_id = Column(String(100))
    version = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


class ValidationMetrics(Base):
    """Track validation metrics for analytics."""

    __tablename__ = "validation_metrics"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), index=True)
    batch_id = Column(String(50))

    total_claims = Column(Integer)
    validated_claims = Column(Integer)
    not_validated_claims = Column(Integer)

    no_error_count = Column(Integer)
    technical_error_count = Column(Integer)
    medical_error_count = Column(Integer)
    both_errors_count = Column(Integer)

    total_paid_amount = Column(Numeric(12, 2))
    validated_amount = Column(Numeric(12, 2))
    rejected_amount = Column(Numeric(12, 2))

    processing_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

