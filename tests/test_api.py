"""Unit tests for API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self, test_client: TestClient):
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data
        assert "timestamp" in data


class TestVersionEndpoint:
    """Tests for GET /version."""

    def test_version_returns_200(self, test_client: TestClient):
        response = test_client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
        assert "version" in data
        assert "python_version" in data
        assert "llm_provider" in data


class TestMetricsEndpoint:
    """Tests for GET /metrics."""

    def test_metrics_returns_200(self, test_client: TestClient):
        response = test_client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_evaluations" in data
        assert "started_at" in data


class TestEvaluateEndpoint:
    """Tests for POST /evaluate — validation only (no LLM call)."""

    def test_invalid_claim_returns_422(self, test_client: TestClient):
        response = test_client.post("/evaluate", json={})
        assert response.status_code == 422

    def test_missing_expenses_returns_422(self, test_client: TestClient):
        payload = {
            "claim_id": "CLM-BAD",
            "employee_id": "EMP-1",
            "employee_name": "Test",
            "business_purpose": "Testing",
            "travel_start_date": "2025-08-01",
            "travel_end_date": "2025-08-03",
            "expenses": [],
            "total_claimed_amount": 100,
        }
        response = test_client.post("/evaluate", json=payload)
        assert response.status_code == 422

    def test_negative_amount_returns_422(self, test_client: TestClient):
        payload = {
            "claim_id": "CLM-BAD",
            "employee_id": "EMP-1",
            "employee_name": "Test",
            "business_purpose": "Testing",
            "travel_start_date": "2025-08-01",
            "travel_end_date": "2025-08-03",
            "expenses": [
                {
                    "expense_type": "hotel",
                    "description": "Test hotel",
                    "amount": 100,
                    "date": "2025-08-01",
                }
            ],
            "total_claimed_amount": -500,
        }
        response = test_client.post("/evaluate", json=payload)
        assert response.status_code == 422


class TestSwaggerDocs:
    """Tests for OpenAPI documentation."""

    def test_docs_accessible(self, test_client: TestClient):
        response = test_client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json_accessible(self, test_client: TestClient):
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "/evaluate" in data["paths"]
        assert "/health" in data["paths"]

    def test_redoc_accessible(self, test_client: TestClient):
        response = test_client.get("/redoc")
        assert response.status_code == 200
