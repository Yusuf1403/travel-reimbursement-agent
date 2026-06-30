"""
Centralised application settings.

Merges values from three sources (highest priority first):
1. Environment variables / .env file
2. config.ini
3. Hard-coded defaults in this module

All downstream code should import ``get_settings()`` instead of reading
env vars directly — this keeps configuration testable and injectable.
"""

from __future__ import annotations

import configparser
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# ---------------------------------------------------------------------------
# Resolve project root (two levels up from this file → travel-reimbursement-agent/)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_INI = _PROJECT_ROOT / "config.ini"

# Load .env eagerly so os.environ is populated before Pydantic reads it.
load_dotenv(_PROJECT_ROOT / ".env")


def _read_ini(section: str, key: str, fallback: Any = None) -> Any:
    """Read a single value from *config.ini*, returning *fallback* on miss."""
    parser = configparser.ConfigParser()
    if _CONFIG_INI.exists():
        parser.read(_CONFIG_INI)
    try:
        return parser.get(section, key)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return fallback


# ---------------------------------------------------------------------------
# Settings Model
# ---------------------------------------------------------------------------
class Settings(BaseSettings):
    """Immutable, validated application configuration."""

    # --- LLM ---
    llm_provider: str = Field(default_factory=lambda: _read_ini("llm", "provider", "openai"))
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4.1")
    google_api_key: str = Field(default="")
    google_model: str = Field(default="gemini-2.5-flash")
    llm_temperature: float = Field(default_factory=lambda: float(_read_ini("llm", "temperature", "0.1")))
    llm_max_tokens: int = Field(default_factory=lambda: int(_read_ini("llm", "max_tokens", "4096")))
    llm_request_timeout: int = Field(default_factory=lambda: int(_read_ini("llm", "request_timeout", "60")))

    # --- RAG ---
    rag_chunk_size: int = Field(default_factory=lambda: int(_read_ini("rag", "chunk_size", "512")))
    rag_chunk_overlap: int = Field(default_factory=lambda: int(_read_ini("rag", "chunk_overlap", "64")))
    rag_top_k: int = Field(default_factory=lambda: int(_read_ini("rag", "top_k", "5")))
    embedding_model: str = Field(
        default_factory=lambda: _read_ini("rag", "embedding_model", "text-embedding-3-small")
    )
    policies_dir: str = Field(default_factory=lambda: _read_ini("rag", "policies_dir", "data/policies"))
    faiss_index_dir: str = Field(default_factory=lambda: _read_ini("rag", "faiss_index_dir", "data/faiss_index"))

    # --- API ---
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_reload: bool = Field(default=True)
    api_workers: int = Field(default=1)

    # --- App Metadata ---
    app_name: str = Field(default="Travel Reimbursement Approval Agent")
    app_version: str = Field(default="1.0.0")
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # --- Expense Limits (USD) ---
    domestic_hotel_per_night: float = Field(
        default_factory=lambda: float(_read_ini("expense_limits", "domestic_hotel_per_night", "200"))
    )
    international_hotel_per_night: float = Field(
        default_factory=lambda: float(_read_ini("expense_limits", "international_hotel_per_night", "350"))
    )
    domestic_meals_per_day: float = Field(
        default_factory=lambda: float(_read_ini("expense_limits", "domestic_meals_per_day", "75"))
    )
    international_meals_per_day: float = Field(
        default_factory=lambda: float(_read_ini("expense_limits", "international_meals_per_day", "100"))
    )
    domestic_flight_economy: float = Field(
        default_factory=lambda: float(_read_ini("expense_limits", "domestic_flight_economy", "1500"))
    )
    international_flight_economy: float = Field(
        default_factory=lambda: float(_read_ini("expense_limits", "international_flight_economy", "5000"))
    )
    international_flight_business: float = Field(
        default_factory=lambda: float(_read_ini("expense_limits", "international_flight_business", "8000"))
    )
    taxi_per_day: float = Field(
        default_factory=lambda: float(_read_ini("expense_limits", "taxi_per_day", "100"))
    )
    incidentals_per_day: float = Field(
        default_factory=lambda: float(_read_ini("expense_limits", "incidentals_per_day", "50"))
    )

    # --- Approval Thresholds ---
    auto_approve_max: float = Field(
        default_factory=lambda: float(_read_ini("approval_thresholds", "auto_approve_max", "500"))
    )
    manager_approval_max: float = Field(
        default_factory=lambda: float(_read_ini("approval_thresholds", "manager_approval_max", "5000"))
    )
    director_approval_max: float = Field(
        default_factory=lambda: float(_read_ini("approval_thresholds", "director_approval_max", "15000"))
    )
    vp_approval_required_above: float = Field(
        default_factory=lambda: float(_read_ini("approval_thresholds", "vp_approval_required_above", "15000"))
    )

    # --- Duplicate Detection ---
    duplicate_time_window_days: int = Field(
        default_factory=lambda: int(_read_ini("duplicate_detection", "time_window_days", "30"))
    )
    duplicate_similarity_threshold: float = Field(
        default_factory=lambda: float(_read_ini("duplicate_detection", "similarity_threshold", "0.85"))
    )

    # --- Currency ---
    base_currency: str = Field(default="USD")
    exchange_rate_api_key: str = Field(default="")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    # ----- Derived helpers -------------------------------------------------
    @property
    def project_root(self) -> Path:
        return _PROJECT_ROOT

    @property
    def policies_path(self) -> Path:
        return _PROJECT_ROOT / self.policies_dir

    @property
    def faiss_index_path(self) -> Path:
        return _PROJECT_ROOT / self.faiss_index_dir


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton ``Settings`` instance (cached)."""
    return Settings()
