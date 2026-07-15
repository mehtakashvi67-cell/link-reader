"""
config.py
---------
Every tunable setting for the whole system lives here, in one place.
"""

import os
# --- LLM (Claude) ---------------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL = "claude-sonnet-4-6"
LLM_MAX_TOKENS = 800

# --- Embeddings -------------------------------------------------------------
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# --- Chunking ---------------------------------------------------------------
CHUNK_SIZE_WORDS = 180
CHUNK_OVERLAP_WORDS = 30

# --- Vector store (Chroma) ---------------------------------------------------
VECTOR_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma")
COLLECTION_NAME = "url_chunks"

# --- Retrieval ----------------------------------------------------------------
TOP_K = 4

# --- Scraper -------------------------------------------------------------------
REQUEST_TIMEOUT_SECONDS = 10
USER_AGENT = "RAG-URL-Explorer/1.0 (educational project)"