"""Test configuration and fixtures."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Set test environment before importing app code
os.environ["LLM_PROVIDER"] = "openai"
os.environ["OPENAI_API_KEY"] = "sk-test-key-for-testing"
os.environ["APP_ENV"] = "testing"
os.environ["LOG_LEVEL"] = "WARNING"


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_claim() -> dict:
    """Return a valid sample claim dictionary."""
    return {
        "claim_id": "CLM-TEST-001",
        "employee_id": "EMP-9001",
        "employee_name": "Test User",
        "department": "Engineering",
        "manager_name": "Test Manager",
        "manager_id": "EMP-9002",
        "travel_type": "domestic",
        "destination": "Test City",
        "business_purpose": "Quarterly team meeting",
        "travel_start_date": "2025-08-01",
        "travel_end_date": "2025-08-03",
        "expenses": [
            {
                "expense_type": "flight",
                "description": "Economy round-trip",
                "amount": 400.00,
                "currency": "USD",
                "date": "2025-08-01",
                "receipt_id": "REC-T-001",
            },
            {
                "expense_type": "hotel",
                "description": "Hotel 2 nights",
                "amount": 350.00,
                "currency": "USD",
                "date": "2025-08-01",
                "receipt_id": "REC-T-002",
            },
            {
                "expense_type": "meals",
                "description": "Meals 3 days",
                "amount": 150.00,
                "currency": "USD",
                "date": "2025-08-01",
                "receipt_id": "REC-T-003",
            },
        ],
        "receipts": [
            {
                "receipt_id": "REC-T-001",
                "expense_type": "flight",
                "vendor": "Test Airlines",
                "amount": 400.00,
                "currency": "USD",
                "date": "2025-08-01",
                "is_attached": True,
            },
            {
                "receipt_id": "REC-T-002",
                "expense_type": "hotel",
                "vendor": "Test Hotel",
                "amount": 350.00,
                "currency": "USD",
                "date": "2025-08-01",
                "is_attached": True,
            },
            {
                "receipt_id": "REC-T-003",
                "expense_type": "meals",
                "vendor": "Test Restaurant",
                "amount": 150.00,
                "currency": "USD",
                "date": "2025-08-01",
                "is_attached": True,
            },
        ],
        "total_claimed_amount": 900.00,
        "claim_currency": "USD",
        "submission_date": "2025-08-10",
    }


@pytest.fixture
def test_client() -> TestClient:
    """Return a FastAPI test client."""
    from app.core.application import create_app
    app = create_app()
    return TestClient(app)
