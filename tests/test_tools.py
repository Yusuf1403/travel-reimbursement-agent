"""Unit tests for all agent tools."""

from __future__ import annotations

import json

import pytest


class TestReceiptCompleteness:
    """Tests for the receipt completeness checker."""

    def test_all_receipts_present(self):
        from app.tools.receipt_completeness import receipt_completeness_check

        data = {
            "expenses": [
                {"expense_type": "flight", "amount": 400, "receipt_id": "R1"},
                {"expense_type": "hotel", "amount": 300, "receipt_id": "R2"},
            ],
            "receipts": [
                {"receipt_id": "R1", "is_attached": True, "amount": 400, "date": "2025-08-01"},
                {"receipt_id": "R2", "is_attached": True, "amount": 300, "date": "2025-08-01"},
            ],
        }
        result = json.loads(receipt_completeness_check.invoke(json.dumps(data)))
        assert result["status"] == "success"
        assert result["all_receipts_present"] is True
        assert result["missing_count"] == 0

    def test_missing_receipt_detected(self):
        from app.tools.receipt_completeness import receipt_completeness_check

        data = {
            "expenses": [
                {"expense_type": "flight", "amount": 400, "receipt_id": "R1"},
                {"expense_type": "hotel", "amount": 300, "receipt_id": None},
            ],
            "receipts": [
                {"receipt_id": "R1", "is_attached": True, "amount": 400, "date": "2025-08-01"},
            ],
        }
        result = json.loads(receipt_completeness_check.invoke(json.dumps(data)))
        assert result["status"] == "success"
        assert result["all_receipts_present"] is False
        assert result["missing_count"] == 1

    def test_small_expense_no_receipt_ok(self):
        from app.tools.receipt_completeness import receipt_completeness_check

        data = {
            "expenses": [
                {"expense_type": "incidentals", "amount": 15.00, "receipt_id": None},
            ],
            "receipts": [],
        }
        result = json.loads(receipt_completeness_check.invoke(json.dumps(data)))
        assert result["all_receipts_present"] is True

    def test_receipt_not_attached(self):
        from app.tools.receipt_completeness import receipt_completeness_check

        data = {
            "expenses": [
                {"expense_type": "meals", "amount": 50, "receipt_id": "R1"},
            ],
            "receipts": [
                {"receipt_id": "R1", "is_attached": False, "amount": 50, "date": "2025-08-01"},
            ],
        }
        result = json.loads(receipt_completeness_check.invoke(json.dumps(data)))
        assert result["missing_count"] == 1


class TestExpenseLimit:
    """Tests for the expense limit checker."""

    def test_within_domestic_limits(self):
        from app.tools.expense_limit import expense_limit_check

        data = {
            "expenses": [
                {"expense_type": "hotel", "amount": 180, "number_of_units": 1},
                {"expense_type": "meals", "amount": 60, "number_of_units": 1},
            ],
            "travel_type": "domestic",
        }
        result = json.loads(expense_limit_check.invoke(json.dumps(data)))
        assert result["status"] == "success"
        assert result["total_excess"] == 0

    def test_exceeds_limit(self):
        from app.tools.expense_limit import expense_limit_check

        data = {
            "expenses": [
                {"expense_type": "hotel", "amount": 300, "number_of_units": 1},
            ],
            "travel_type": "domestic",
        }
        result = json.loads(expense_limit_check.invoke(json.dumps(data)))
        assert result["total_excess"] > 0
        assert result["items"][0]["within_limit"] is False

    def test_international_limits_higher(self):
        from app.tools.expense_limit import expense_limit_check

        data = {
            "expenses": [
                {"expense_type": "hotel", "amount": 300, "number_of_units": 1},
            ],
            "travel_type": "international",
        }
        result = json.loads(expense_limit_check.invoke(json.dumps(data)))
        # International limit is $350, so $300 is within limit
        assert result["total_excess"] == 0
        assert result["items"][0]["within_limit"] is True

    def test_multi_unit_limits(self):
        from app.tools.expense_limit import expense_limit_check

        data = {
            "expenses": [
                {"expense_type": "hotel", "amount": 500, "number_of_units": 3},
            ],
            "travel_type": "domestic",
        }
        result = json.loads(expense_limit_check.invoke(json.dumps(data)))
        # 3 nights × $200 = $600 max, $500 is within
        assert result["total_excess"] == 0


class TestApprovalMatrix:
    """Tests for the approval matrix checker."""

    def test_auto_approve(self):
        from app.tools.approval_matrix import approval_matrix_check

        data = {"total_amount": 400, "employee_level": "IC"}
        result = json.loads(approval_matrix_check.invoke(json.dumps(data)))
        assert result["auto_approve"] is True
        assert result["required_approver_level"] == "auto"

    def test_manager_approval(self):
        from app.tools.approval_matrix import approval_matrix_check

        data = {"total_amount": 2500, "employee_level": "IC"}
        result = json.loads(approval_matrix_check.invoke(json.dumps(data)))
        assert result["required_approver_level"] == "manager"
        assert result["auto_approve"] is False

    def test_director_approval(self):
        from app.tools.approval_matrix import approval_matrix_check

        data = {"total_amount": 12000, "employee_level": "IC"}
        result = json.loads(approval_matrix_check.invoke(json.dumps(data)))
        assert result["required_approver_level"] == "director"

    def test_vp_approval(self):
        from app.tools.approval_matrix import approval_matrix_check

        data = {"total_amount": 20000, "employee_level": "IC"}
        result = json.loads(approval_matrix_check.invoke(json.dumps(data)))
        assert result["required_approver_level"] == "vp_finance"

    def test_manager_self_approval_escalation(self):
        from app.tools.approval_matrix import approval_matrix_check

        data = {"total_amount": 2500, "employee_level": "Manager"}
        result = json.loads(approval_matrix_check.invoke(json.dumps(data)))
        # Should be escalated from manager to director
        assert result["required_approver_level"] == "director"


class TestCurrencyConversion:
    """Tests for the currency conversion tool."""

    def test_same_currency(self):
        from app.tools.currency_conversion import currency_conversion

        data = {"amount": 100, "from_currency": "USD", "to_currency": "USD"}
        result = json.loads(currency_conversion.invoke(json.dumps(data)))
        assert result["converted_amount"] == 100
        assert result["exchange_rate"] == 1.0

    def test_eur_to_usd(self):
        from app.tools.currency_conversion import currency_conversion

        data = {"amount": 100, "from_currency": "EUR", "to_currency": "USD"}
        result = json.loads(currency_conversion.invoke(json.dumps(data)))
        assert result["status"] == "success"
        assert result["converted_amount"] > 100  # EUR > USD

    def test_unsupported_currency(self):
        from app.tools.currency_conversion import currency_conversion

        data = {"amount": 100, "from_currency": "XYZ", "to_currency": "USD"}
        result = json.loads(currency_conversion.invoke(json.dumps(data)))
        assert result["status"] == "error"

    def test_gbp_to_usd(self):
        from app.tools.currency_conversion import currency_conversion

        data = {"amount": 200, "from_currency": "GBP", "to_currency": "USD"}
        result = json.loads(currency_conversion.invoke(json.dumps(data)))
        assert result["converted_amount"] > 200  # GBP > USD


class TestDuplicateClaim:
    """Tests for the duplicate claim checker."""

    def test_no_duplicate(self):
        from app.tools.duplicate_claim import duplicate_claim_check

        data = {
            "employee_id": "EMP-9999",
            "travel_start_date": "2025-12-01",
            "travel_end_date": "2025-12-05",
            "total_amount": 999,
            "destination": "Nowhere",
        }
        result = json.loads(duplicate_claim_check.invoke(json.dumps(data)))
        assert result["is_potential_duplicate"] is False

    def test_potential_duplicate(self):
        from app.tools.duplicate_claim import duplicate_claim_check

        data = {
            "employee_id": "EMP-1001",
            "travel_start_date": "2025-06-01",
            "travel_end_date": "2025-06-05",
            "total_amount": 2450,
            "destination": "New York",
        }
        result = json.loads(duplicate_claim_check.invoke(json.dumps(data)))
        assert result["is_potential_duplicate"] is True
        assert len(result["matches"]) > 0


class TestOutputValidator:
    """Tests for the output validation tool."""

    def test_valid_output(self):
        from app.tools.output_validator import validate_output

        data = {
            "claim_id": "CLM-TEST",
            "decision": "approved",
            "approved_amount": 500,
            "rejected_amount": 0,
            "confidence_score": 0.9,
            "reasoning": "All good",
        }
        result = json.loads(validate_output.invoke(json.dumps(data)))
        assert result["status"] == "valid"

    def test_invalid_output(self):
        from app.tools.output_validator import validate_output

        data = {"claim_id": "CLM-TEST"}  # Missing required fields
        result = json.loads(validate_output.invoke(json.dumps(data)))
        assert result["status"] == "invalid"
        assert len(result["errors"]) > 0

    def test_invalid_json(self):
        from app.tools.output_validator import validate_output

        result = json.loads(validate_output.invoke("not valid json {{{"))
        assert result["status"] == "invalid"
