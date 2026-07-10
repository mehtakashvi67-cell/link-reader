"""
embeddings.py
-------------
Step 3 of the pipeline: turn text into vectors ("embeddings").

An embedding is a list of numbers (here, 384 of them) that represents the
*meaning* of a piece of text. Texts with similar meaning end up close
together in this 384-dimensional space, even if they don't share any exact
words. That's what makes semantic search possible in vector_store.py.

Runs locally via sentence-transformers -- no API key needed. The model
downloads once (~90MB) and is cached afterward.
"""

from functools import lru_cache
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL_NAME


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it (loading is slow-ish)."""
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Turn a list of strings into a list of embedding vectors."""
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()


def embed_query(query: str) -> list[float]:
    """Embed a single search query the same way chunks were embedded."""
    return embed_texts([query])[0]
# if __name__ == "__main__":
#     import numpy as np

#     texts = [
#         "The cat sat on the mat.",
#         "A feline was resting on the rug.",   # similar meaning, different words
#         "Stock markets crashed today.",        # unrelated meaning
#     ]

#     vectors = embed_texts(texts)

#     print("Vector length:", len(vectors[0]))

#     v0, v1, v2 = np.array(vectors[0]), np.array(vectors[1]), np.array(vectors[2])
#     print("Similarity (cat/mat vs feline/rug):", np.dot(v0, v1))   # should be high
#     print("Similarity (cat/mat vs stock market):", np.dot(v0, v2)) # should be low