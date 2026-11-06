"""
Settings for The Unofficial Guide.

Anything set in the .env file overrides the defaults here.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")


# ─── Corpus ──────────────────────────────────────────────────────────────────
# Folder name inside corpora/. Override with AI201_CORPUS or --corpus.

CORPUS = os.getenv("AI201_CORPUS", "city_guides")


# ─── Chunking ────────────────────────────────────────────────────────────────

CHUNK_SIZE = 800        # characters per chunk
CHUNK_OVERLAP = 120     # characters shared between neighbouring chunks


# ─── Retrieval ───────────────────────────────────────────────────────────────

TOP_K = 5               # how many chunks to pull back per question

# The relevance gate. If the best chunk is further away than this, the system
# refuses to answer instead of handing the model thin material.
#
# Lower is better: 0.3 is a close match, 0.9 is unrelated.
THRESHOLD = 0.66


# ─── Models ──────────────────────────────────────────────────────────────────
# Embeddings run locally and use no API quota. Only generation calls a service.
# Chroma's bundled model is the default. Any other name loads from Hugging Face
# and needs `pip install 'sentence-transformers>=3.4,<3.5'`.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MODEL = os.getenv("AI201_MODEL", "gemini-3.5-flash-lite")


# ─── Rate limiting and quota guards ──────────────────────────────────────────
# Guards so a runaway loop triggers a warning instead of draining the daily quota.

REQUESTS_PER_MINUTE = 10       # outgoing calls the limiter will allow per minute
SESSION_REQUEST_BUDGET = 300   # stop and warn rather than draining the daily quota
MAX_RETRIES = 4                # on 429 / resource-exhausted, with backoff

CACHE_ENABLED = os.getenv("AI201_CACHE", "1") != "0"
CACHE_DIR = ROOT / ".cache"


# ─── Paths ───────────────────────────────────────────────────────────────────

CORPORA_DIR = ROOT / "corpora"
CHROMA_DIR = ROOT / "chroma_db"
RESULTS_DIR = ROOT / "results"


def corpus_path(name: str | None = None) -> Path:
    """Folder holding the documents for a corpus."""
    return CORPORA_DIR / (name or CORPUS) / "documents"


def collection_name(name: str | None = None, variant: str = "default") -> str:
    """
    Name of the vector-store collection for a corpus.

    `variant` lets you index the same corpus two ways and query both without
    deleting anything.

    Chroma is fussy about collection names: 3 to 63 characters, starting and
    ending with a letter or digit, and nothing but letters, digits, underscores
    and hyphens in between. If you bring your own corpus and name the folder
    something Chroma won't accept, this cleans it up rather than failing.
    """
    import re

    raw = f"{name or CORPUS}__{variant}"
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "-", raw)
    cleaned = cleaned.strip("_-")          # must start and end alphanumeric
    if not cleaned or not cleaned[0].isalnum():
        cleaned = f"c{cleaned}"
    if not cleaned[-1].isalnum():
        cleaned = f"{cleaned}0"
    return cleaned[:63].rstrip("_-") or "collection"
