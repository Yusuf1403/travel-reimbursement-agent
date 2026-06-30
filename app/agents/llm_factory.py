"""
LLM factory — returns the correct chat model based on the configured provider.

Supports:
- **openai**: ``ChatOpenAI`` targeting GPT-4.1 (or any model in OPENAI_MODEL).
- **google**: ``ChatGoogleGenerativeAI`` targeting Gemini 2.5 Flash.
"""

from __future__ import annotations

import logging

from langchain_core.language_models.chat_models import BaseChatModel

from app.config.settings import get_settings

logger = logging.getLogger("app.agents.llm_factory")


def create_chat_model() -> BaseChatModel:
    """Instantiate the LLM chat model for the active provider."""
    settings = get_settings()

    if settings.llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        logger.info("Using Google Gemini model: %s", settings.google_model)
        return ChatGoogleGenerativeAI(
            model=settings.google_model,
            google_api_key=settings.google_api_key,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_tokens,
            convert_system_message_to_human=True,
        )

    # Default → OpenAI
    from langchain_openai import ChatOpenAI

    logger.info("Using OpenAI model: %s", settings.openai_model)
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        request_timeout=settings.llm_request_timeout,
    )
