"""
Pydantic schemas for API request / response contracts.

These models are the *public* interface — they define what callers send
and what they receive.  Internal domain objects live in ``app.models``.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class ExpenseType(str, Enum):
    HOTEL = "hotel"
    MEALS = "meals"
    FLIGHT = "flight"
    TAXI = "taxi"
    PARKING = "parking"
    INCIDENTALS = "incidentals"
    CONFERENCE = "conference"
    OTHER = "other"


class TravelType(str, Enum):
    DOMESTIC = "domestic"
    INTERNATIONAL = "international"


class Decision(str, Enum):
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------
class ReceiptItem(BaseModel):
    """Metadata for a single receipt attachment."""

    receipt_id: str = Field(..., description="Unique receipt identifier")
    expense_type: ExpenseType
    vendor: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    date: date
    attachment_url: str | None = Field(default=None, description="URL or file path to the receipt image/PDF")
    is_attached: bool = Field(default=False, description="Whether the actual receipt document is attached")


class ExpenseItem(BaseModel):
    """A single line-item expense within a claim."""

    expense_type: ExpenseType
    description: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    date: date
    receipt_id: str | None = Field(default=None, description="Links to a ReceiptItem")


class ReimbursementClaim(BaseModel):
    """Complete reimbursement claim submitted for evaluation."""

    claim_id: str = Field(..., description="Unique claim identifier")
    employee_id: str = Field(..., description="Employee identifier")
    employee_name: str = Field(..., min_length=1)
    department: str = Field(default="")
    manager_name: str = Field(default="")
    manager_id: str = Field(default="")

    travel_type: TravelType = Field(default=TravelType.DOMESTIC)
    destination: str = Field(default="")
    business_purpose: str = Field(..., min_length=1)

    travel_start_date: date
    travel_end_date: date

    expenses: list[ExpenseItem] = Field(..., min_length=1)
    receipts: list[ReceiptItem] = Field(default_factory=list)

    total_claimed_amount: float = Field(..., gt=0)
    claim_currency: str = Field(default="USD", max_length=3)

    submission_date: date = Field(default_factory=date.today)

    @field_validator("travel_end_date")
    @classmethod
    def end_after_start(cls, v: date, info: Any) -> date:
        start = info.data.get("travel_start_date")
        if start and v < start:
            raise ValueError("travel_end_date must be on or after travel_start_date")
        return v


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------
class Deduction(BaseModel):
    """A single deduction entry explaining why an amount was reduced."""

    expense_type: str
    claimed_amount: float
    approved_amount: float
    deducted_amount: float
    reason: str


class AuditEntry(BaseModel):
    """A single step in the processing audit trail."""

    step: int
    tool: str
    input_summary: str = ""
    output_summary: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class EvaluationResponse(BaseModel):
    """Structured output returned by the agent after evaluating a claim."""

    claim_id: str
    decision: Decision
    approved_amount: float = Field(ge=0)
    rejected_amount: float = Field(ge=0)
    deductions: list[Deduction] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    policy_references: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    reasoning: str = ""
    tools_used: list[str] = Field(default_factory=list)
    audit_trail: list[AuditEntry] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str = "healthy"
    version: str
    environment: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class VersionResponse(BaseModel):
    """Version endpoint response."""

    app_name: str
    version: str
    python_version: str
    llm_provider: str


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    error: str
    detail: str | None = None
    status_code: int


class PolicyUploadResponse(BaseModel):
    """Response after uploading / indexing a policy document."""

    message: str
    filename: str
    chunks_indexed: int
