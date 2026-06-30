"""
Embedding model factory.

Returns the correct LangChain embedding model based on the configured
LLM provider (``openai`` or ``google``).
"""

from __future__ import annotations

from langchain_core.embeddings import Embeddings

from app.config.settings import get_settings


def get_embedding_model() -> Embeddings:
    """Instantiate and return the embedding model for the active provider."""
    settings = get_settings()

    if settings.llm_provider == "google":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        return GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.google_api_key,
        )

    # Default → OpenAI
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )
