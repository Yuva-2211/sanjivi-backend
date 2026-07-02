"""
Text chunking — token-aware sliding window with semantic boundary
preservation (splits on sentence boundaries where possible).
"""

from __future__ import annotations

import re

# pyrefly: ignore [missing-import]
import tiktoken

from app.config import settings
from app.utils.helpers import clean_text

# Use cl100k_base tokeniser (same as GPT-4 / text-embedding-3) for accurate
# token counting; bge-small tokenises similarly so counts will be approximate.
_ENCODING = tiktoken.get_encoding("cl100k_base")

# Sentence boundary pattern — splits on ., !, ? followed by whitespace.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    sentences = _SENTENCE_RE.split(text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    """
    Split *text* into overlapping token-aware chunks.

    Strategy:
    1. Sentence-split the cleaned text.
    2. Pack sentences into a chunk until the token budget is exhausted.
    3. Back-fill the overlap window from the previous chunk's sentences.

    This avoids cutting sentences in half while staying close to *chunk_size*
    tokens per chunk.
    """
    chunk_size = chunk_size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap

    text = clean_text(text)
    if not text:
        return []

    sentences = _split_sentences(text)
    if not sentences:
        return [text[:4000]]  # Safety: return raw text if no sentences found

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_tokens: int = 0

    for sentence in sentences:
        sent_tokens = len(_ENCODING.encode(sentence))

        # If a single sentence exceeds chunk_size, hard-split it
        if sent_tokens > chunk_size:
            # Flush current buffer first
            if current_sentences:
                chunks.append(" ".join(current_sentences))
                current_sentences = []
                current_tokens = 0
            # Hard-split the large sentence on token boundaries
            tokens = _ENCODING.encode(sentence)
            step = max(1, chunk_size - overlap)
            for i in range(0, len(tokens), step):
                sub_tokens = tokens[i : i + chunk_size]
                chunks.append(_ENCODING.decode(sub_tokens))
            continue

        if current_tokens + sent_tokens > chunk_size:
            # Emit current chunk
            chunks.append(" ".join(current_sentences))

            # Build overlap: keep trailing sentences whose total fits in overlap
            overlap_sentences: list[str] = []
            overlap_tokens = 0
            for s in reversed(current_sentences):
                t = len(_ENCODING.encode(s))
                if overlap_tokens + t > overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_tokens += t

            current_sentences = overlap_sentences
            current_tokens = overlap_tokens

        current_sentences.append(sentence)
        current_tokens += sent_tokens

    # Flush remaining
    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return [c for c in chunks if c.strip()]
