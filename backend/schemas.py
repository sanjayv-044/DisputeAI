from datetime import date
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict
)


class DisputeCreate(BaseModel):

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )

    customer_name: str = Field(
        min_length=2,
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

    transaction_type: str
    transaction_date: date
    reported_date: date

    fraud_description: str = Field(
        min_length=5,
        max_length=2000
    )

    otp_shared: bool

    @field_validator("customer_name")
    @classmethod
    def validate_customer_name(cls, value):

        if not value.strip():
            raise ValueError("Customer name cannot be empty")

        if not any(char.isalpha() for char in value):
            raise ValueError("Customer name must contain letters")

        if not all(
            char.isalpha() or char.isspace() or char in ".-'"
            for char in value
        ):
            raise ValueError("Customer name contains invalid characters")

        return value

    @field_validator("transaction_id")
    @classmethod
    def validate_transaction_id(cls, value):

        if not value.strip():
            raise ValueError("Transaction ID cannot be empty")

        if not value.isalnum():
            raise ValueError(
                "Transaction ID must contain only letters and numbers"
            )

        return value

    @field_validator("fraud_description")
    @classmethod
    def validate_description(cls, value):

        if not value.strip():
            raise ValueError("Fraud description cannot be empty")

        if len(value.strip()) < 5:
            raise ValueError(
                "Fraud description must contain at least 5 characters"
            )

        return value

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, value):

        value = value.strip()

        if value not in ["UPI", "Card"]:
            raise ValueError(
                "Transaction type must be UPI or Card"
            )

        return value

    @model_validator(mode="after")
    def validate_dates(self):

        today = date.today()

        if self.transaction_date > today:
            raise ValueError(
                "Transaction date cannot be in the future"
            )

        if self.reported_date > today:
            raise ValueError(
                "Reported date cannot be in the future"
            )

        if self.reported_date < self.transaction_date:
            raise ValueError(
                "Reported date cannot precede transaction date"
            )

        return self