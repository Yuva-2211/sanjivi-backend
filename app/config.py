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
    groq_api_keys_str: str = Field(default="", description="Comma-separated Groq API keys for rotation")
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
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
    top_k_dense: int = Field(default=8)
    top_k_bm25: int = Field(default=7)
    top_k_rerank: int = Field(default=6)
    top_k_final: int = Field(default=5)
    rrf_k: int = Field(default=60)
    context_max_chars: int = Field(default=4000)

 

    # ── Per-agent LLM routing ───────────────────────────────────────────────────
    # emergency + reviewer stay on fast 8b model for low latency (Groq)
    # Clinical agents + consensus use meta-llama/llama-3.3-70b-instruct via OpenRouter for reasoning
    emergency_model: str = Field(default="llama-3.1-8b-instant")
    ayurveda_model: str = Field(default="openai/gpt-oss-120b")
    siddha_model: str = Field(default="openai/gpt-oss-120b")
    unani_model: str = Field(default="openai/gpt-oss-120b")
    homeopathy_model: str = Field(default="openai/gpt-oss-120b")
    yoga_model: str = Field(default="openai/gpt-oss-120b")
    consensus_model: str = Field(default="openai/gpt-oss-120b")
    reviewer_model: str = Field(default="llama-3.1-8b-instant")

    
    emergency_max_tokens: int = Field(default=150)
    ayurveda_max_tokens: int = Field(default=700)
    siddha_max_tokens: int = Field(default=700)
    unani_max_tokens: int = Field(default=700)
    homeopathy_max_tokens: int = Field(default=700)
    yoga_max_tokens: int = Field(default=700)
    consensus_max_tokens: int = Field(default=800)
    reviewer_max_tokens: int = Field(default=400)

    # ── Concurrency & Rate Control ─────────────────────────────────────────────
    # How many expert LLM calls can run concurrently (2 = balanced, 5 = burst)
    max_concurrent_experts: int = Field(default=1, description="Max concurrent expert agent calls")
    # Hard cap on total simultaneous Groq calls (guards against burst across all lanes)
    max_concurrent_global: int = Field(default=3, description="Global max concurrent Groq API calls")
    # Backoff base (seconds) for 429 retries: base^attempt → 2, 4, 8
    groq_backoff_base: int = Field(default=2, description="Exponential backoff base for 429 retries")
    # Per-expert timeout
    expert_timeout: int = Field(default=28, description="Expert agent LLM call timeout (seconds)")

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
        if not values.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY must be set for Sanjivi AI to function.")
        if not values.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY must be set for Sanjivi AI to function.")

        return values

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()


# Module-level convenience alias
settings: Settings = get_settings()
