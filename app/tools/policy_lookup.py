"""
Policy Lookup Tool — retrieves relevant travel policy context via RAG.

This is the primary grounding mechanism: before the agent makes any
decision, it must fetch the applicable policy sections so that its
reasoning is anchored in company rules rather than generic knowledge.
"""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

from app.rag.vector_store import get_vector_store

logger = logging.getLogger("app.tools.policy_lookup")


@tool
def policy_lookup(query: str) -> str:
    """
    Retrieve relevant travel policy sections for the given query.

    Args:
        query: A natural-language question about travel policy
               (e.g. "What is the hotel limit for domestic travel?").

    Returns:
        JSON string with a list of policy chunks and their source files.
    """
    logger.info("Policy lookup query: %s", query[:120])
    try:
        store = get_vector_store()
        docs = store.query(query)
        results = [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
            }
            for doc in docs
        ]
        logger.info("Retrieved %d policy chunks", len(results))
        return json.dumps({"status": "success", "chunks": results, "count": len(results)})
    except Exception as exc:
        logger.error("Policy lookup failed: %s", exc)
        return json.dumps({"status": "error", "message": str(exc), "chunks": [], "count": 0})
