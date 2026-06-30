"""
Currency Conversion Tool — converts amounts to USD.

Uses a static exchange-rate table as fallback when no live API key is
configured.  The rates are approximate and intended for demo / testing.
"""

from __future__ import annotations

import json
import logging
from datetime import date

from langchain_core.tools import tool

logger = logging.getLogger("app.tools.currency_conversion")

# Static fallback exchange rates (→ USD)
_STATIC_RATES: dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
    "INR": 0.012,
    "JPY": 0.0067,
    "CAD": 0.74,
    "AUD": 0.65,
    "CHF": 1.13,
    "CNY": 0.14,
    "SGD": 0.74,
}


def _get_rate(from_currency: str, to_currency: str) -> float | None:
    """Return the conversion rate *from_currency → to_currency* using static table."""
    from_rate = _STATIC_RATES.get(from_currency.upper())
    to_rate = _STATIC_RATES.get(to_currency.upper())
    if from_rate is None or to_rate is None:
        return None
    return from_rate / to_rate


@tool
def currency_conversion(conversion_json: str) -> str:
    """
    Convert a monetary amount from one currency to another.

    Args:
        conversion_json: JSON string with:
            - amount: float
            - from_currency: str (ISO 4217)
            - to_currency: str (default "USD")

    Returns:
        JSON with converted_amount, exchange_rate, and conversion_date.
    """
    logger.info("Running currency conversion")
    try:
        data = json.loads(conversion_json)
        amount = float(data.get("amount", 0))
        from_cur = data.get("from_currency", "USD").upper()
        to_cur = data.get("to_currency", "USD").upper()

        if from_cur == to_cur:
            return json.dumps({
                "status": "success",
                "original_amount": amount,
                "converted_amount": amount,
                "from_currency": from_cur,
                "to_currency": to_cur,
                "exchange_rate": 1.0,
                "conversion_date": date.today().isoformat(),
                "source": "identity",
            })

        rate = _get_rate(from_cur, to_cur)
        if rate is None:
            return json.dumps({
                "status": "error",
                "message": f"Unsupported currency pair: {from_cur} → {to_cur}",
                "supported_currencies": list(_STATIC_RATES.keys()),
            })

        converted = round(amount * rate, 2)
        result = {
            "status": "success",
            "original_amount": amount,
            "converted_amount": converted,
            "from_currency": from_cur,
            "to_currency": to_cur,
            "exchange_rate": round(rate, 6),
            "conversion_date": date.today().isoformat(),
            "source": "static_rates",
        }
        logger.info("Converted %.2f %s → %.2f %s (rate=%.6f)", amount, from_cur, converted, to_cur, rate)
        return json.dumps(result)

    except Exception as exc:
        logger.error("Currency conversion failed: %s", exc)
        return json.dumps({"status": "error", "message": str(exc)})
