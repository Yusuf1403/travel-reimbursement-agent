"""
Receipt Completeness Tool — validates that every claimed expense has a
matching receipt attached.

Business rule: expenses above $25 require an itemised receipt.
Missing receipts flag the expense for deduction or manual review.
"""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

logger = logging.getLogger("app.tools.receipt_completeness")

RECEIPT_REQUIRED_THRESHOLD = 25.0  # USD — expenses above this need a receipt


@tool
def receipt_completeness_check(expenses_json: str) -> str:
    """
    Check that each expense has a matching receipt.

    Args:
        expenses_json: JSON string containing:
            - expenses: list of {expense_type, amount, receipt_id, date}
            - receipts: list of {receipt_id, is_attached, amount, date}

    Returns:
        JSON string with matched/unmatched expenses and missing receipt list.
    """
    logger.info("Running receipt completeness check")
    try:
        data = json.loads(expenses_json)
        expenses = data.get("expenses", [])
        receipts = data.get("receipts", [])

        receipt_map: dict[str, dict] = {r["receipt_id"]: r for r in receipts}
        matched: list[dict] = []
        missing: list[dict] = []

        for exp in expenses:
            rid = exp.get("receipt_id")
            amount = exp.get("amount", 0)

            if rid and rid in receipt_map:
                receipt = receipt_map[rid]
                if receipt.get("is_attached", False):
                    matched.append({
                        "expense_type": exp.get("expense_type"),
                        "amount": amount,
                        "receipt_id": rid,
                        "status": "matched",
                    })
                else:
                    missing.append({
                        "expense_type": exp.get("expense_type"),
                        "amount": amount,
                        "receipt_id": rid,
                        "reason": "Receipt referenced but not attached",
                    })
            elif amount > RECEIPT_REQUIRED_THRESHOLD:
                missing.append({
                    "expense_type": exp.get("expense_type"),
                    "amount": amount,
                    "receipt_id": rid,
                    "reason": f"No receipt for expense above ${RECEIPT_REQUIRED_THRESHOLD}",
                })
            else:
                # Small expense — receipt not strictly required
                matched.append({
                    "expense_type": exp.get("expense_type"),
                    "amount": amount,
                    "receipt_id": rid,
                    "status": "below_threshold",
                })

        result = {
            "status": "success",
            "total_expenses": len(expenses),
            "matched_count": len(matched),
            "missing_count": len(missing),
            "matched": matched,
            "missing": missing,
            "all_receipts_present": len(missing) == 0,
        }
        logger.info("Receipt check: %d matched, %d missing", len(matched), len(missing))
        return json.dumps(result)

    except Exception as exc:
        logger.error("Receipt completeness check failed: %s", exc)
        return json.dumps({"status": "error", "message": str(exc)})
