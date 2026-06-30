"""
API routes for the Travel Reimbursement Approval Agent.

Endpoints:
    POST /evaluate         — evaluate a reimbursement claim
    POST /upload-policy    — upload and index a policy document
    GET  /health           — health check
    GET  /version          — version information
    GET  /metrics          — simple runtime metrics
"""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File
from langchain_core.documents import Document

from app.agents.reimbursement_agent import get_agent
from app.config.settings import get_settings
from app.rag.vector_store import get_vector_store
from app.schemas import (
    EvaluationResponse,
    ErrorResponse,
    HealthResponse,
    PolicyUploadResponse,
    ReimbursementClaim,
    VersionResponse,
)

logger = logging.getLogger("app.api.routes")

router = APIRouter()

# Simple in-memory metrics
_metrics = {
    "total_evaluations": 0,
    "successful_evaluations": 0,
    "failed_evaluations": 0,
    "total_evaluation_time_ms": 0.0,
    "started_at": datetime.utcnow().isoformat(),
}


# ---------------------------------------------------------------------------
# POST /evaluate
# ---------------------------------------------------------------------------
@router.post(
    "/evaluate",
    response_model=EvaluationResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Evaluate a travel reimbursement claim",
    description="Accepts a reimbursement claim, retrieves policy context via RAG, "
    "runs seven agent tools, and returns a structured approval decision.",
    tags=["Claims"],
)
async def evaluate_claim(claim: ReimbursementClaim) -> EvaluationResponse:
    """Evaluate a travel reimbursement claim end-to-end."""
    _metrics["total_evaluations"] += 1
    start = time.perf_counter()
    logger.info("Received claim %s for evaluation", claim.claim_id)

    try:
        agent = get_agent()
        result = await agent.evaluate(claim)
        _metrics["successful_evaluations"] += 1
        return result
    except Exception:
        _metrics["failed_evaluations"] += 1
        raise
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        _metrics["total_evaluation_time_ms"] += elapsed
        logger.info("Claim %s processed in %.1fms", claim.claim_id, elapsed)


# ---------------------------------------------------------------------------
# POST /upload-policy
# ---------------------------------------------------------------------------
@router.post(
    "/upload-policy",
    response_model=PolicyUploadResponse,
    summary="Upload a policy document",
    description="Upload a Markdown (.md) policy file. It will be saved, chunked, embedded, and added to the FAISS index.",
    tags=["Policies"],
)
async def upload_policy(file: UploadFile = File(...)) -> PolicyUploadResponse:
    """Upload and index a policy document."""
    logger.info("Uploading policy: %s", file.filename)
    settings = get_settings()
    policies_dir = settings.policies_path
    policies_dir.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    text = content.decode("utf-8")

    # Persist the file
    dest = policies_dir / (file.filename or "uploaded_policy.md")
    dest.write_text(text, encoding="utf-8")

    # Add to FAISS
    doc = Document(page_content=text, metadata={"source": file.filename or "uploaded"})
    store = get_vector_store()
    try:
        chunks_added = store.add_documents([doc])
    except Exception:
        # If the index doesn't exist yet, build from scratch
        chunks_added = store.build_index()

    logger.info("Indexed %d chunks from %s", chunks_added, file.filename)
    return PolicyUploadResponse(
        message="Policy uploaded and indexed successfully",
        filename=file.filename or "uploaded_policy.md",
        chunks_indexed=chunks_added,
    )


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------
@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"],
)
async def health() -> HealthResponse:
    """Return service health status."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.app_env,
    )


# ---------------------------------------------------------------------------
# GET /version
# ---------------------------------------------------------------------------
@router.get(
    "/version",
    response_model=VersionResponse,
    summary="Version information",
    tags=["System"],
)
async def version() -> VersionResponse:
    """Return application and runtime version details."""
    settings = get_settings()
    return VersionResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        python_version=sys.version.split()[0],
        llm_provider=settings.llm_provider,
    )


# ---------------------------------------------------------------------------
# GET /metrics
# ---------------------------------------------------------------------------
@router.get(
    "/metrics",
    summary="Runtime metrics",
    tags=["System"],
)
async def metrics() -> dict:
    """Return simple runtime metrics."""
    total = _metrics["total_evaluations"]
    avg_ms = (_metrics["total_evaluation_time_ms"] / total) if total > 0 else 0
    return {
        **_metrics,
        "average_evaluation_time_ms": round(avg_ms, 1),
    }
