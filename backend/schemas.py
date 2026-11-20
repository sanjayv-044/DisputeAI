from datetime import date, datetime
from typing import Optional, List, Any
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict
)


# =====================================================
# USER & AUTH SCHEMAS
# =====================================================

class UserRegister(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=5, max_length=150)
    password: str = Field(min_length=6, max_length=100)
    full_name: str = Field(min_length=2, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    role: Optional[str] = Field(default="customer")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str):
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v.lower()


class UserLogin(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str
    created_at: Optional[datetime] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# =====================================================
# DISPUTE SCHEMAS
# =====================================================

class DisputeCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="ignore"
    )

    customer_name: str = Field(
        min_length=2,
        max_length=100
    )

    customer_email: Optional[str] = Field(
        default=None,
        max_length=150
    )

    bank_name: Optional[str] = Field(
        default="State Bank of India",
        max_length=100
    )

    transaction_id: str = Field(
        min_length=3,
        max_length=100
    )

    amount: float = Field(
        gt=0,
        le=100000000,
        allow_inf_nan=False
    )

    transaction_type: str = Field(default="UPI")
    transaction_date: date
    reported_date: date

    fraud_type_claimed: Optional[str] = Field(
        default="Unknown",
        max_length=100
    )

    fraud_description: str = Field(
        min_length=5,
        max_length=3000
    )

    otp_shared: bool = False

    @field_validator("customer_name")
    @classmethod
    def validate_customer_name(cls, value):
        if not value.strip():
            raise ValueError("Customer name cannot be empty")
        if not any(char.isalpha() for char in value):
            raise ValueError("Customer name must contain letters")
        return value

    @field_validator("transaction_id")
    @classmethod
    def validate_transaction_id(cls, value):
        if not value.strip():
            raise ValueError("Transaction ID cannot be empty")
        return value.strip()

    @field_validator("fraud_description")
    @classmethod
    def validate_description(cls, value):
        if len(value.strip()) < 5:
            raise ValueError("Fraud description must contain at least 5 characters")
        return value

    @model_validator(mode="after")
    def validate_dates(self):
        today = date.today()
        if self.transaction_date > today:
            raise ValueError("Transaction date cannot be in the future")
        if self.reported_date > today:
            raise ValueError("Reported date cannot be in the future")
        if self.reported_date < self.transaction_date:
            raise ValueError("Reported date cannot precede transaction date")
        return self


class EvidenceFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_type: str
    file_size: int
    verified_status: str
    uploaded_at: Optional[datetime] = None


class InvestigationDossierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fraud_category: str
    agent_findings: str
    rbi_citations_json: str
    verification_summary: str
    liability_status: str
    liability_reasoning: str
    recommendation: str
    human_escalation: bool
    confidence_score: float
    created_at: Optional[datetime] = None


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    status_from: str
    status_to: str
    changed_by: str
    notes: str
    created_at: Optional[datetime] = None


class DisputeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dispute_id: str
    customer_name: str
    customer_email: Optional[str] = None
    bank_name: Optional[str] = "State Bank of India"
    transaction_id: str
    amount: float
    transaction_type: str
    transaction_date: str
    reported_date: str
    fraud_type_claimed: Optional[str] = None
    fraud_description: str
    otp_shared: bool

    fraud_type: str
    risk_score: int
    risk_level: str
    priority: str
    classification_explanation: Optional[str] = ""
    escalated: bool
    recommendation: str
    liability_verdict: Optional[str] = "PENDING_ASSESSMENT"
    status: str
    admin_remarks: Optional[str] = ""
    final_resolution: Optional[str] = ""
    created_at: Optional[datetime] = None

    evidence_files: Optional[List[EvidenceFileOut]] = []
    dossier: Optional[Any] = None
    history: Optional[List[HistoryOut]] = []


class AdminActionRequest(BaseModel):
    action: str = Field(description="approve | reject | escalate")
    remarks: Optional[str] = ""
    final_resolution: Optional[str] = ""


class StatusUpdateRequest(BaseModel):
    status: str
    remarks: Optional[str] = ""
