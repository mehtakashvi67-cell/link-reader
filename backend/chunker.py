"""
chunker.py
----------
Step 2 of the pipeline: split long text into small overlapping chunks.

Why chunk at all?
- Embedding models work best on short, focused passages, not entire pages.
- Retrieval is more precise when we return "this exact paragraph" instead
  of "somewhere in this 3000-word article".

Why overlap?
- Without overlap, a sentence split across two chunks loses context on
  both sides. A small overlap keeps ideas intact.
"""

from dataclasses import dataclass
from config import CHUNK_SIZE_WORDS, CHUNK_OVERLAP_WORDS


@dataclass
class Chunk:
    index: int
    text: str
    word_count: int


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = CHUNK_OVERLAP_WORDS) -> list[Chunk]:
    """
    Word-based sliding-window chunker.

    Example with chunk_size=5, overlap=2 on "a b c d e f g h":
      chunk 0: a b c d e
      chunk 1: d e f g h   <- starts 2 words back into the previous chunk
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    index = 0
    step = max(chunk_size - overlap, 1)

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunks.append(Chunk(index=index, text=" ".join(chunk_words), word_count=len(chunk_words)))

        index += 1
        if end == len(words):
            break
        start += step

    return chunks
# if __name__ == "__main__":
#     from scraper import scrape_url

#     page = scrape_url("https://en.wikipedia.org/wiki/Artificial_intelligence")
#     chunks = chunk_text(page.text)

#     print(f"Total chunks: {len(chunks)}")
#     print("--- First chunk ---")
#     print(chunks[0].text)
#     print("--- Second chunk (notice the overlap with the end of chunk 0) ---")
#     print(chunks[1].text)