"""
Output Validator Tool — validates the agent's draft response against the
required ``EvaluationResponse`` schema.

This is the *last* tool the agent calls before returning — it ensures the
response is structurally sound and contains all required fields.
"""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool
from pydantic import ValidationError

from app.schemas import EvaluationResponse

logger = logging.getLogger("app.tools.output_validator")


@tool
def validate_output(draft_json: str) -> str:
    """
    Validate a draft evaluation response against the output schema.

    Args:
        draft_json: JSON string of the draft EvaluationResponse.

    Returns:
        JSON with validation result — "valid" or list of errors.
    """
    logger.info("Validating agent output")
    try:
        data = json.loads(draft_json)
        EvaluationResponse(**data)
        logger.info("Output validation passed")
        return json.dumps({"status": "valid", "errors": []})
    except ValidationError as ve:
        errors = [{"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]} for e in ve.errors()]
        logger.warning("Output validation failed: %d errors", len(errors))
        return json.dumps({"status": "invalid", "errors": errors})
    except json.JSONDecodeError as je:
        logger.error("Output is not valid JSON: %s", je)
        return json.dumps({"status": "invalid", "errors": [{"field": "root", "message": f"Invalid JSON: {je}"}]})
    except Exception as exc:
        logger.error("Output validation error: %s", exc)
        return json.dumps({"status": "error", "message": str(exc)})
