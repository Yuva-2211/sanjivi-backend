"""
Custom backend exceptions for production-grade error handling.
"""

from __future__ import annotations


class ConfigValidationError(RuntimeError):
    """Raised when required startup configuration is invalid or missing."""


class JSONParsingError(ValueError):
    """Raised when an LLM response cannot be parsed into valid JSON."""


class LLMResponseError(RuntimeError):
    """Raised when the LLM returns an invalid or unsupported response."""


class NodeExecutionError(RuntimeError):
    """Raised when a LangGraph node fails and the workflow needs a fallback."""
