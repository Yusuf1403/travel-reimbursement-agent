"""
Approval Matrix Tool — determines required approval authority.

The matrix is driven by ``config.ini`` thresholds:
    auto_approve_max      ≤ $500    → auto-approved
    manager_approval_max  ≤ $5,000  → manager approval
    director_approval_max ≤ $15,000 → director approval
    above                           → VP / Finance approval
"""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

from app.config.settings import get_settings

logger = logging.getLogger("app.tools.approval_matrix")


@tool
def approval_matrix_check(request_json: str) -> str:
    """
    Determine the required approval level for a given amount.

    Args:
        request_json: JSON string with:
            - total_amount: float
            - employee_level: str (optional, e.g. "IC", "Manager", "Director")

    Returns:
        JSON with required_approver_level, auto_approve flag, and notes.
    """
    logger.info("Running approval matrix check")
    try:
        data = json.loads(request_json)
        amount = float(data.get("total_amount", 0))
        employee_level = data.get("employee_level", "IC")
        settings = get_settings()

        if amount <= settings.auto_approve_max:
            approver = "auto"
            auto_approve = True
            notes = f"Amount ${amount:.2f} is within auto-approval limit (${settings.auto_approve_max:.2f})"
        elif amount <= settings.manager_approval_max:
            approver = "manager"
            auto_approve = False
            notes = f"Amount ${amount:.2f} requires manager approval (limit ${settings.manager_approval_max:.2f})"
        elif amount <= settings.director_approval_max:
            approver = "director"
            auto_approve = False
            notes = f"Amount ${amount:.2f} requires director approval (limit ${settings.director_approval_max:.2f})"
        else:
            approver = "vp_finance"
            auto_approve = False
            notes = (
                f"Amount ${amount:.2f} exceeds ${settings.director_approval_max:.2f} — "
                "VP / Finance approval required"
            )

        # Self-approval guard: managers cannot approve their own high claims
        if employee_level.lower() == "manager" and approver == "manager":
            approver = "director"
            auto_approve = False
            notes += " | Escalated: manager cannot self-approve."

        result = {
            "status": "success",
            "total_amount": amount,
            "required_approver_level": approver,
            "auto_approve": auto_approve,
            "employee_level": employee_level,
            "notes": notes,
            "thresholds": {
                "auto_approve_max": settings.auto_approve_max,
                "manager_approval_max": settings.manager_approval_max,
                "director_approval_max": settings.director_approval_max,
                "vp_approval_required_above": settings.vp_approval_required_above,
            },
        }
        logger.info("Approval matrix: amount=%.2f, approver=%s", amount, approver)
        return json.dumps(result)

    except Exception as exc:
        logger.error("Approval matrix check failed: %s", exc)
        return json.dumps({"status": "error", "message": str(exc)})
