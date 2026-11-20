import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
root_dir = backend_dir.parent
for p in [str(backend_dir), str(root_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    role = Column(String(50), default="customer", nullable=False)  # "customer" | "admin"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    disputes = relationship("Dispute", back_populates="user")


class Dispute(Base):
    __tablename__ = "disputes"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(String(50), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=True)
    bank_name = Column(String(255), default="State Bank of India")
    transaction_id = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(50), nullable=False)  # "UPI", "Card", "Internet Banking"
    transaction_date = Column(String(50), nullable=False)
    reported_date = Column(String(50), nullable=False)
    fraud_type_claimed = Column(String(100), nullable=True)
    fraud_description = Column(Text, nullable=False)
    otp_shared = Column(Boolean, default=False)

    # AI CLASSIFICATION & AGENT WORKFLOW FIELDS
    fraud_type = Column(String(100), default="Unclassified")  # 5 canonical categories
    risk_score = Column(Integer, default=0)
    risk_level = Column(String(50), default="Medium")  # Low, Medium, High, Critical
    priority = Column(String(50), default="Medium")
    classification_explanation = Column(Text, default="")
    escalated = Column(Boolean, default=False)
    recommendation = Column(Text, default="")
    liability_verdict = Column(String(100), default="PENDING_ASSESSMENT")
    status = Column(String(50), default="Pending")  # "Pending", "In Investigation", "Under Review", "Escalated", "Resolved - Refund Approved", "Resolved - Dispute Rejected"

    admin_remarks = Column(Text, default="")
    final_resolution = Column(Text, default="")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="disputes")
    evidence_files = relationship("EvidenceFile", back_populates="dispute", cascade="all, delete-orphan")
    dossiers = relationship("InvestigationDossier", back_populates="dispute", cascade="all, delete-orphan")
    history = relationship("ComplaintHistory", back_populates="dispute", cascade="all, delete-orphan")


class EvidenceFile(Base):
    __tablename__ = "evidence_files"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(String(50), ForeignKey("disputes.dispute_id"), index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, default=0)
    verified_status = Column(String(50), default="Verified (Local Integrity Checked)")
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    dispute = relationship("Dispute", back_populates="evidence_files")


class InvestigationDossier(Base):
    __tablename__ = "investigation_dossiers"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(String(50), ForeignKey("disputes.dispute_id"), index=True, nullable=False)
    fraud_category = Column(String(100), default="Unclassified")
    agent_findings = Column(Text, default="")
    rbi_citations_json = Column(Text, default="[]")
    verification_summary = Column(Text, default="")
    liability_status = Column(String(100), default="INSUFFICIENT_EVIDENCE")
    liability_reasoning = Column(Text, default="")
    recommendation = Column(Text, default="")
    human_escalation = Column(Boolean, default=False)
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dispute = relationship("Dispute", back_populates="dossiers")


class ComplaintHistory(Base):
    __tablename__ = "complaint_history"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(String(50), ForeignKey("disputes.dispute_id"), index=True, nullable=False)
    action = Column(String(100), nullable=False)
    status_from = Column(String(50), default="")
    status_to = Column(String(50), default="")
    changed_by = Column(String(100), default="System")
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dispute = relationship("Dispute", back_populates="history")
