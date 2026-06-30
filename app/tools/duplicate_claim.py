"""
Duplicate Claim Tool — detects potential duplicate submissions.

Checks an in-memory claim store (simulating a database) for claims
with matching employee, travel dates, and similar expense amounts.
"""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta

from langchain_core.tools import tool

from app.config.settings import get_settings

logger = logging.getLogger("app.tools.duplicate_claim")

# In-memory claim history (simulates a database)
_claim_history: list[dict] = [
    {
        "claim_id": "CLM-2025-001",
        "employee_id": "EMP-1001",
        "travel_start_date": "2025-06-01",
        "travel_end_date": "2025-06-05",
        "total_amount": 2450.00,
        "destination": "New York",
        "status": "approved",
    },
    {
        "claim_id": "CLM-2025-002",
        "employee_id": "EMP-1002",
        "travel_start_date": "2025-06-10",
        "travel_end_date": "2025-06-12",
        "total_amount": 1200.00,
        "destination": "Chicago",
        "status": "approved",
    },
    {
        "claim_id": "CLM-2025-003",
        "employee_id": "EMP-1001",
        "travel_start_date": "2025-07-15",
        "travel_end_date": "2025-07-18",
        "total_amount": 3200.00,
        "destination": "San Francisco",
        "status": "approved",
    },
]


def _calculate_similarity(claim1: dict, claim2: dict) -> float:
    """
    Compute a simple similarity score [0, 1] between two claims.

    Factors: same employee, overlapping dates, similar amounts, same destination.
    """
    score = 0.0

    # Same employee
    if claim1.get("employee_id") == claim2.get("employee_id"):
        score += 0.3

    # Overlapping dates
    try:
        s1 = date.fromisoformat(str(claim1.get("travel_start_date", "")))
        e1 = date.fromisoformat(str(claim1.get("travel_end_date", "")))
        s2 = date.fromisoformat(str(claim2.get("travel_start_date", "")))
        e2 = date.fromisoformat(str(claim2.get("travel_end_date", "")))
        if s1 <= e2 and s2 <= e1:
            score += 0.3
    except (ValueError, TypeError):
        pass

    # Similar amount (within 10%)
    try:
        a1 = float(claim1.get("total_amount", 0))
        a2 = float(claim2.get("total_amount", 0))
        if a1 > 0 and a2 > 0:
            ratio = min(a1, a2) / max(a1, a2)
            if ratio > 0.9:
                score += 0.25
    except (ValueError, TypeError):
        pass

    # Same destination
    d1 = str(claim1.get("destination", "")).strip().lower()
    d2 = str(claim2.get("destination", "")).strip().lower()
    if d1 and d2 and d1 == d2:
        score += 0.15

    return round(min(score, 1.0), 2)


@tool
def duplicate_claim_check(claim_json: str) -> str:
    """
    Check if a claim may duplicate a previously submitted one.

    Args:
        claim_json: JSON string with employee_id, travel_start_date,
                    travel_end_date, total_amount, destination.

    Returns:
        JSON with duplicate risk flag, matching claims, and similarity scores.
    """
    logger.info("Running duplicate claim check")
    try:
        claim = json.loads(claim_json)
        settings = get_settings()
        threshold = settings.duplicate_similarity_threshold

        matches: list[dict] = []
        for historical in _claim_history:
            sim = _calculate_similarity(claim, historical)
            if sim >= threshold:
                matches.append({
                    "matching_claim_id": historical["claim_id"],
                    "similarity_score": sim,
                    "status": historical.get("status", "unknown"),
                    "amount": historical.get("total_amount"),
                    "destination": historical.get("destination"),
                })

        is_duplicate = len(matches) > 0
        result = {
            "status": "success",
            "is_potential_duplicate": is_duplicate,
            "matches": matches,
            "threshold_used": threshold,
            "claims_checked": len(_claim_history),
        }
        logger.info("Duplicate check: duplicate=%s, matches=%d", is_duplicate, len(matches))
        return json.dumps(result)

    except Exception as exc:
        logger.error("Duplicate claim check failed: %s", exc)
        return json.dumps({"status": "error", "message": str(exc)})
