"""
Expense Limit Tool — checks each expense against category-specific limits.

Limits are loaded from ``config.ini`` / Settings so they can be tuned
without code changes.  The tool returns approved and excess amounts per item.
"""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

from app.config.settings import get_settings

logger = logging.getLogger("app.tools.expense_limit")


def _get_limit(expense_type: str, travel_type: str) -> float | None:
    """Look up the per-unit limit (per night / per day / total) for an expense category."""
    settings = get_settings()
    is_international = travel_type.lower() == "international"

    limits = {
        "hotel": settings.international_hotel_per_night if is_international else settings.domestic_hotel_per_night,
        "meals": settings.international_meals_per_day if is_international else settings.domestic_meals_per_day,
        "flight": (settings.international_flight_economy if is_international else settings.domestic_flight_economy),
        "taxi": settings.taxi_per_day,
        "incidentals": settings.incidentals_per_day,
    }
    return limits.get(expense_type.lower())


@tool
def expense_limit_check(expenses_json: str) -> str:
    """
    Check each expense line item against company spending limits.

    Args:
        expenses_json: JSON string containing:
            - expenses: list of {expense_type, amount, date, number_of_units}
            - travel_type: "domestic" | "international"

    Returns:
        JSON with per-item approved_amount, excess, and applicable limit.
    """
    logger.info("Running expense limit check")
    try:
        data = json.loads(expenses_json)
        expenses = data.get("expenses", [])
        travel_type = data.get("travel_type", "domestic")

        results: list[dict] = []
        total_approved = 0.0
        total_excess = 0.0

        for exp in expenses:
            etype = exp.get("expense_type", "other")
            amount = float(exp.get("amount", 0))
            units = int(exp.get("number_of_units", 1))

            limit_per_unit = _get_limit(etype, travel_type)
            if limit_per_unit is not None:
                max_allowed = limit_per_unit * units
                approved = min(amount, max_allowed)
                excess = max(0.0, amount - max_allowed)
                within_limit = excess == 0
            else:
                # No specific limit defined — approve as-is (policy may cover it)
                approved = amount
                excess = 0.0
                max_allowed = None
                within_limit = True

            total_approved += approved
            total_excess += excess

            results.append(
                {
                    "expense_type": etype,
                    "claimed_amount": amount,
                    "limit_per_unit": limit_per_unit,
                    "units": units,
                    "max_allowed": max_allowed,
                    "approved_amount": round(approved, 2),
                    "excess_amount": round(excess, 2),
                    "within_limit": within_limit,
                }
            )

        output = {
            "status": "success",
            "travel_type": travel_type,
            "items": results,
            "total_approved": round(total_approved, 2),
            "total_excess": round(total_excess, 2),
        }
        logger.info("Expense limit check: approved=%.2f, excess=%.2f", total_approved, total_excess)
        return json.dumps(output)

    except Exception as exc:
        logger.error("Expense limit check failed: %s", exc)
        return json.dumps({"status": "error", "message": str(exc)})
