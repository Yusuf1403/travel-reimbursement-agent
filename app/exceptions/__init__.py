"""Custom exception hierarchy for the Travel Reimbursement Agent."""

from __future__ import annotations


class AgentBaseError(Exception):
    """Root exception for all application errors."""

    def __init__(self, message: str = "An unexpected error occurred", status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ClaimValidationError(AgentBaseError):
    """Raised when a submitted claim fails schema or business validation."""

    def __init__(self, message: str = "Claim validation failed", details: list[str] | None = None) -> None:
        self.details = details or []
        super().__init__(message=message, status_code=422)


class PolicyNotFoundError(AgentBaseError):
    """Raised when no matching policy documents are found in the RAG store."""

    def __init__(self, message: str = "No relevant policy found") -> None:
        super().__init__(message=message, status_code=404)


class LLMProviderError(AgentBaseError):
    """Raised when the LLM provider returns an error or times out."""

    def __init__(self, message: str = "LLM provider error", provider: str = "unknown") -> None:
        self.provider = provider
        super().__init__(message=f"[{provider}] {message}", status_code=502)


class RAGIndexError(AgentBaseError):
    """Raised when the FAISS index cannot be loaded or queried."""

    def __init__(self, message: str = "RAG index error") -> None:
        super().__init__(message=message, status_code=500)


class DuplicateClaimError(AgentBaseError):
    """Raised when a potential duplicate claim is detected."""

    def __init__(self, claim_id: str, original_claim_id: str) -> None:
        super().__init__(
            message=f"Potential duplicate: claim {claim_id} matches existing claim {original_claim_id}",
            status_code=409,
        )


class CurrencyConversionError(AgentBaseError):
    """Raised when currency conversion fails."""

    def __init__(self, from_currency: str, to_currency: str) -> None:
        super().__init__(
            message=f"Cannot convert {from_currency} → {to_currency}",
            status_code=400,
        )


class ToolExecutionError(AgentBaseError):
    """Raised when an agent tool fails during execution."""

    def __init__(self, tool_name: str, reason: str = "") -> None:
        self.tool_name = tool_name
        super().__init__(
            message=f"Tool '{tool_name}' failed: {reason}",
            status_code=500,
        )
