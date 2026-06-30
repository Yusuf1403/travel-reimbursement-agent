"""
Reimbursement Agent — the central orchestrator.

Binds the LLM to the seven tools, constructs the prompt with RAG context,
invokes the agent, and parses the structured output.  The LLM *never*
answers directly — it must always call tools.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import ClassVar

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agents.llm_factory import create_chat_model
from app.prompts.templates import CLAIM_EVALUATION_PROMPT, SYSTEM_PROMPT
from app.rag.vector_store import get_vector_store
from app.schemas import EvaluationResponse, ReimbursementClaim
from app.tools import (
    approval_matrix_check,
    currency_conversion,
    duplicate_claim_check,
    expense_limit_check,
    policy_lookup,
    receipt_completeness_check,
    validate_output,
)

logger = logging.getLogger("app.agents.reimbursement_agent")


class ReimbursementAgent:
    """Evaluates travel reimbursement claims using tool-calling LLM agent."""

    TOOLS: ClassVar[list] = [
        policy_lookup,
        receipt_completeness_check,
        expense_limit_check,
        duplicate_claim_check,
        approval_matrix_check,
        currency_conversion,
        validate_output,
    ]

    def __init__(self) -> None:
        self._llm = create_chat_model()
        self._prompt = self._build_prompt()
        self._agent = create_tool_calling_agent(self._llm, self.TOOLS, self._prompt)
        self._executor = AgentExecutor(
            agent=self._agent,
            tools=self.TOOLS,
            verbose=True,
            max_iterations=15,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
        )
        logger.info("ReimbursementAgent initialised with %d tools", len(self.TOOLS))

    # ----- Public API ------------------------------------------------------

    async def evaluate(self, claim: ReimbursementClaim) -> EvaluationResponse:
        """
        Evaluate a claim end-to-end and return a structured decision.

        Steps:
        1. Retrieve policy context via RAG.
        2. Invoke the agent with the claim + context.
        3. Parse the LLM output into ``EvaluationResponse``.
        """
        claim_dict = claim.model_dump(mode="json")
        claim_json = json.dumps(claim_dict, indent=2, default=str)

        # --- RAG retrieval ---
        policy_context = self._retrieve_policy_context(claim)

        # --- Build human message ---
        human_message = CLAIM_EVALUATION_PROMPT.format(
            policy_context=policy_context,
            claim_json=claim_json,
        )

        logger.info(
            "Evaluating claim %s (amount=%.2f %s)", claim.claim_id, claim.total_claimed_amount, claim.claim_currency
        )

        # --- Invoke agent ---
        result = await self._executor.ainvoke({"input": human_message})

        # --- Parse output ---
        return self._parse_response(result, claim)

    # ----- Internals -------------------------------------------------------

    @staticmethod
    def _build_prompt() -> ChatPromptTemplate:
        """Construct the agent prompt template."""
        return ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

    @staticmethod
    def _retrieve_policy_context(claim: ReimbursementClaim) -> str:
        """Use RAG to fetch the most relevant policy snippets for this claim."""
        queries = [
            f"{claim.travel_type.value} travel reimbursement policy",
            "expense limits and per-diem rates",
            "receipt and documentation requirements",
            f"{claim.expenses[0].expense_type.value} expense policy" if claim.expenses else "",
        ]
        all_chunks: list[str] = []
        try:
            store = get_vector_store()
            for q in queries:
                if not q:
                    continue
                docs = store.query(q, top_k=3)
                for doc in docs:
                    chunk_text = doc.page_content.strip()
                    if chunk_text not in all_chunks:
                        all_chunks.append(chunk_text)
        except Exception as exc:
            logger.warning("RAG retrieval failed, proceeding without context: %s", exc)
            all_chunks = ["[Policy context unavailable — RAG index not built. Using general policy knowledge.]"]

        return "\n\n---\n\n".join(all_chunks[:10])

    def _parse_response(self, result: dict, claim: ReimbursementClaim) -> EvaluationResponse:
        """Extract and validate structured JSON from the agent's output."""
        raw_output = result.get("output", "")
        intermediate_steps = result.get("intermediate_steps", [])

        # Collect tools used from intermediate steps
        tools_used = []
        audit_trail = []
        for idx, (action, observation) in enumerate(intermediate_steps):
            tool_name = getattr(action, "tool", "unknown")
            tools_used.append(tool_name)
            audit_trail.append(
                {
                    "step": idx + 1,
                    "tool": tool_name,
                    "input_summary": str(getattr(action, "tool_input", ""))[:200],
                    "output_summary": str(observation)[:200],
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        # Try to parse JSON from the output
        try:
            # Handle markdown code blocks
            cleaned = raw_output
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0]
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0]

            data = json.loads(cleaned)
            data["tools_used"] = list(set(tools_used))
            data["audit_trail"] = audit_trail
            data["claim_id"] = claim.claim_id

            return EvaluationResponse(**data)

        except (json.JSONDecodeError, Exception) as exc:
            logger.warning("Failed to parse agent output as JSON: %s — building fallback", exc)
            return self._build_fallback_response(claim, raw_output, tools_used, audit_trail)

    @staticmethod
    def _build_fallback_response(
        claim: ReimbursementClaim,
        raw_output: str,
        tools_used: list[str],
        audit_trail: list[dict],
    ) -> EvaluationResponse:
        """When the LLM output is not parseable, return a manual-review response."""
        return EvaluationResponse(
            claim_id=claim.claim_id,
            decision="manual_review",
            approved_amount=0.0,
            rejected_amount=claim.total_claimed_amount,
            deductions=[],
            confidence_score=0.3,
            policy_references=["Unable to parse agent output — manual review required"],
            missing_documents=[],
            reasoning=f"Agent output could not be parsed into structured format. Raw output: {raw_output[:500]}",
            tools_used=list(set(tools_used)),
            audit_trail=audit_trail,
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_agent_instance: ReimbursementAgent | None = None


def get_agent() -> ReimbursementAgent:
    """Return (and lazily create) the singleton ``ReimbursementAgent``."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ReimbursementAgent()
    return _agent_instance
