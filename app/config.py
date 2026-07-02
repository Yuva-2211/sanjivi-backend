"""
Configuration — loads all environment variables and exposes them as a
typed Settings object.  Import `settings` everywhere instead of os.getenv.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────────────────────────────────
    groq_api_key: str = Field(default="", description="Groq API key")
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model identifier",
    )
    groq_timeout: int = Field(default=60, description="Timeout in seconds for Groq requests")
    groq_max_retries: int = Field(default=2, description="Max retry attempts for Groq requests")

    # ── Vector DB ─────────────────────────────────────────────────────────────
    pinecone_api_key: str = Field(default="", description="Pinecone API key")
    pinecone_index: str = Field(default="sanjivi-ayush")
    pinecone_cloud: Literal["aws", "gcp", "azure"] = Field(default="aws")
    pinecone_region: str = Field(default="us-east-1")

    # ── Embeddings ────────────────────────────────────────────────────────────
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5")
    embedding_dimension: int = Field(default=384)

    # ── Search APIs ───────────────────────────────────────────────────────────
    tavily_api_key: str = Field(default="", description="Tavily Search API key")

    # ── RAG Tuning ────────────────────────────────────────────────────────────
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=64)
    top_k_dense: int = Field(default=6)
    top_k_bm25: int = Field(default=5)
    top_k_rerank: int = Field(default=3)
    top_k_final: int = Field(default=3)
    rrf_k: int = Field(default=60)
    context_max_chars: int = Field(default=3200)

    # ── Per-agent LLM routing ───────────────────────────────────────────────────
    # emergency + reviewer stay on fast 8b model for low latency
    # Clinical agents + consensus use openai/gpt-oss-120b via Groq for best quality
    emergency_model: str = Field(default="llama-3.1-8b-instant")
    ayurveda_model: str = Field(default="openai/gpt-oss-120b")
    siddha_model: str = Field(default="openai/gpt-oss-120b")
    unani_model: str = Field(default="openai/gpt-oss-120b")
    homeopathy_model: str = Field(default="openai/gpt-oss-120b")
    yoga_model: str = Field(default="openai/gpt-oss-120b")
    consensus_model: str = Field(default="openai/gpt-oss-120b")
    reviewer_model: str = Field(default="llama-3.1-8b-instant")

    emergency_max_tokens: int = Field(default=500)
    ayurveda_max_tokens: int = Field(default=900)
    siddha_max_tokens: int = Field(default=900)
    unani_max_tokens: int = Field(default=900)
    homeopathy_max_tokens: int = Field(default=900)
    yoga_max_tokens: int = Field(default=900)
    consensus_max_tokens: int = Field(default=1000)
    reviewer_max_tokens: int = Field(default=700)

    # ── Paths ─────────────────────────────────────────────────────────────────
    data_dir: str = Field(default="../data")
    bm25_index_dir: str = Field(default="bm25_indexes")

    # ── Server ────────────────────────────────────────────────────────────────
    frontend_url: str = Field(default="http://localhost:3000")

    @model_validator(mode="after")
    def validate_model_config(cls, values: "Settings") -> "Settings":
        """Validate environment-loaded model strings and required credentials."""
        invalid_markers = [
            "EMERGENCY_MODEL=",
            "REVIEWER_MODEL=",
            "EMBEDDING_MODEL=",
            "CONSENSUS_MODEL=",
        ]
        for field_name in [
            "groq_model",
            "emergency_model",
            "ayurveda_model",
            "siddha_model",
            "unani_model",
            "homeopathy_model",
            "yoga_model",
            "consensus_model",
            "reviewer_model",
        ]:
            value = getattr(values, field_name, None)
            if isinstance(value, str) and any(marker in value for marker in invalid_markers):
                raise ValueError(
                    f"Environment variable parsing error: '{field_name}' contains unexpected marker. "
                    "Please put each variable on its own line in .env."
                )

        if values.top_k_rerank < values.top_k_final:
            raise ValueError("top_k_rerank must be greater than or equal to top_k_final")

        if not values.groq_api_key:
            raise ValueError("GROQ_API_KEY must be set for Sanjivi AI to function.")
        if not values.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY must be set for Sanjivi AI to function.")

        return values

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()


# Module-level convenience alias
settings: Settings = get_settings()
