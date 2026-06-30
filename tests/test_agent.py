"""Unit tests for the ReimbursementAgent (mocked LLM)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from app.schemas import EvaluationResponse, ReimbursementClaim


class TestAgentParsing:
    """Tests for agent output parsing."""

    def test_fallback_on_invalid_output(self, sample_claim):
        """When LLM returns unparseable output, agent should return manual_review."""
        from app.agents.reimbursement_agent import ReimbursementAgent

        claim = ReimbursementClaim(**sample_claim)
        result_dict = {
            "output": "This is not valid JSON at all",
            "intermediate_steps": [
                (MagicMock(tool="policy_lookup", tool_input="test"), "some result"),
            ],
        }

        agent = object.__new__(ReimbursementAgent)
        response = agent._parse_response(result_dict, claim)

        assert isinstance(response, EvaluationResponse)
        assert response.decision.value == "manual_review"
        assert response.confidence_score == 0.3
        assert "policy_lookup" in response.tools_used

    def test_parse_valid_json_output(self, sample_claim):
        """When LLM returns valid JSON, agent should parse it correctly."""
        from app.agents.reimbursement_agent import ReimbursementAgent

        claim = ReimbursementClaim(**sample_claim)
        valid_output = json.dumps({
            "claim_id": claim.claim_id,
            "decision": "approved",
            "approved_amount": 900.0,
            "rejected_amount": 0.0,
            "confidence_score": 0.95,
            "reasoning": "All expenses within limits",
            "deductions": [],
            "policy_references": ["Section 4"],
            "missing_documents": [],
        })
        result_dict = {
            "output": valid_output,
            "intermediate_steps": [
                (MagicMock(tool="expense_limit_check", tool_input="test"), "ok"),
            ],
        }

        agent = object.__new__(ReimbursementAgent)
        response = agent._parse_response(result_dict, claim)

        assert response.decision.value == "approved"
        assert response.approved_amount == 900.0

    def test_parse_markdown_wrapped_json(self, sample_claim):
        """Agent should handle JSON wrapped in markdown code blocks."""
        from app.agents.reimbursement_agent import ReimbursementAgent

        claim = ReimbursementClaim(**sample_claim)
        json_content = json.dumps({
            "claim_id": claim.claim_id,
            "decision": "partially_approved",
            "approved_amount": 700.0,
            "rejected_amount": 200.0,
            "confidence_score": 0.8,
            "reasoning": "Hotel over limit",
        })
        wrapped = f"Here is the result:\n```json\n{json_content}\n```"
        result_dict = {
            "output": wrapped,
            "intermediate_steps": [],
        }

        agent = object.__new__(ReimbursementAgent)
        response = agent._parse_response(result_dict, claim)

        assert response.decision.value == "partially_approved"
        assert response.rejected_amount == 200.0


class TestAgentToolsList:
    """Tests for agent tool configuration."""

    def test_agent_has_seven_tools(self):
        from app.agents.reimbursement_agent import ReimbursementAgent

        assert len(ReimbursementAgent.TOOLS) == 7

    def test_tool_names(self):
        from app.agents.reimbursement_agent import ReimbursementAgent

        tool_names = {t.name for t in ReimbursementAgent.TOOLS}
        expected = {
            "policy_lookup",
            "receipt_completeness_check",
            "expense_limit_check",
            "duplicate_claim_check",
            "approval_matrix_check",
            "currency_conversion",
            "validate_output",
        }
        assert tool_names == expected
