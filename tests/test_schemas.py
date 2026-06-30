"""Unit tests for Pydantic schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import (
    Decision,
    EvaluationResponse,
    ExpenseType,
    ReimbursementClaim,
)


class TestExpenseType:
    """Tests for the ExpenseType enum."""

    def test_valid_types(self):
        assert ExpenseType.HOTEL == "hotel"
        assert ExpenseType.MEALS == "meals"
        assert ExpenseType.FLIGHT == "flight"
        assert ExpenseType.TAXI == "taxi"


class TestReimbursementClaim:
    """Tests for claim validation."""

    def test_valid_claim(self, sample_claim):
        claim = ReimbursementClaim(**sample_claim)
        assert claim.claim_id == "CLM-TEST-001"
        assert claim.total_claimed_amount == 900.00
        assert len(claim.expenses) == 3

    def test_end_date_before_start_raises(self, sample_claim):
        sample_claim["travel_start_date"] = "2025-08-05"
        sample_claim["travel_end_date"] = "2025-08-01"
        with pytest.raises(ValidationError, match="travel_end_date"):
            ReimbursementClaim(**sample_claim)

    def test_negative_amount_raises(self, sample_claim):
        sample_claim["total_claimed_amount"] = -100.00
        with pytest.raises(ValidationError):
            ReimbursementClaim(**sample_claim)

    def test_empty_expenses_raises(self, sample_claim):
        sample_claim["expenses"] = []
        with pytest.raises(ValidationError):
            ReimbursementClaim(**sample_claim)

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            ReimbursementClaim()  # type: ignore[call-arg]


class TestEvaluationResponse:
    """Tests for evaluation response schema."""

    def test_valid_response(self):
        resp = EvaluationResponse(
            claim_id="CLM-TEST-001",
            decision=Decision.APPROVED,
            approved_amount=900.00,
            rejected_amount=0.00,
            confidence_score=0.95,
            reasoning="All expenses within limits",
        )
        assert resp.decision == Decision.APPROVED
        assert resp.confidence_score == 0.95

    def test_confidence_score_bounds(self):
        with pytest.raises(ValidationError):
            EvaluationResponse(
                claim_id="CLM-TEST-001",
                decision=Decision.APPROVED,
                approved_amount=900.00,
                rejected_amount=0.00,
                confidence_score=1.5,  # Invalid: > 1.0
            )

    def test_all_decisions_valid(self):
        for decision in Decision:
            resp = EvaluationResponse(
                claim_id="TEST",
                decision=decision,
                approved_amount=0,
                rejected_amount=0,
                confidence_score=0.5,
            )
            assert resp.decision == decision
