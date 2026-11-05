from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text
)

from sqlalchemy.sql import func

from database import Base


class Dispute(Base):

    __tablename__ = "disputes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    dispute_id = Column(
        String,
        unique=True,
        index=True
    )

    customer_name = Column(
        String,
        nullable=False
    )

    transaction_id = Column(
        String,
        nullable=False
    )

    amount = Column(
        Float,
        nullable=False
    )

    transaction_type = Column(
        String,
        nullable=False
    )

    transaction_date = Column(
        String,
        nullable=False
    )

    reported_date = Column(
        String,
        nullable=False
    )

    fraud_description = Column(
        Text,
        nullable=False
    )

    otp_shared = Column(
        Boolean,
        default=False
    )

    # AI CLASSIFICATION FIELDS

    fraud_type = Column(
        String,
        default="Unclassified"
    )

    risk_score = Column(
        Integer,
        default=0
    )

    priority = Column(
        String,
        default="Medium"
    )

    escalated = Column(
        Boolean,
        default=False
    )

    recommendation = Column(
        Text,
        default=""
    )

    status = Column(
        String,
        default="Pending"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )