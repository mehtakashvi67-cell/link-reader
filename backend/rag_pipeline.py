"""
rag_pipeline.py
----------------
The conductor. Doesn't implement any concept itself -- just calls the
other modules in the right order:

  INGEST:  scraper -> chunker -> embeddings -> vector_store
  QUERY:   embeddings -> vector_store -> llm_client
"""

from dataclasses import dataclass

import scraper
import chunker
import embeddings
import vector_store
import llm_client
from config import TOP_K

_store = vector_store.VectorStore()


@dataclass
class IngestResult:
    source_id: str
    url: str
    title: str
    num_chunks: int
    preview: str


@dataclass
class QueryResult:
    answer: str
    retrieved_chunks: list[dict]


def ingest_url(url: str) -> IngestResult:
    """Full ingest pipeline: scrape a URL, chunk it, embed it, store it."""
    page = scraper.scrape_url(url)
    chunks = chunker.chunk_text(page.text)

    if not chunks:
        raise ValueError("Page had no content to chunk.")

    chunk_texts = [c.text for c in chunks]
    vectors = embeddings.embed_texts(chunk_texts)

    source_id = vector_store.new_source_id()
    _store.add_chunks(
        source_id=source_id,
        source_url=page.url,
        source_title=page.title,
        chunk_texts=chunk_texts,
        chunk_embeddings=vectors,
    )

    return IngestResult(
        source_id=source_id,
        url=page.url,
        title=page.title,
        num_chunks=len(chunks),
        preview=chunk_texts[0][:200],
    )


def query(question: str, source_id: str | None = None, top_k: int = TOP_K) -> QueryResult:
    """Full query pipeline: embed the question, retrieve chunks, generate an answer."""
    query_vector = embeddings.embed_query(question)
    hits = _store.search(query_vector, top_k=top_k, source_id=source_id)

    if not hits:
        return QueryResult(answer="No ingested content matches this query yet -- ingest a URL first.", retrieved_chunks=[])

    answer = llm_client.generate_answer(question, hits)
    return QueryResult(answer=answer, retrieved_chunks=hits)


def list_sources() -> list[dict]:
    return _store.list_sources()
# if __name__ == "__main__":
#     print("Ingesting...")
#     result = ingest_url("https://en.wikipedia.org/wiki/Python_(programming_language)")
#     print(f"Ingested '{result.title}' -- {result.num_chunks} chunks. source_id={result.source_id}")

#     print("\nQuerying...")
#     answer = query("Who created Python and when?")
#     print("\nANSWER:\n", answer.answer)
#     print(f"\n(based on {len(answer.retrieved_chunks)} retrieved chunks)")
def summarize(source_id: str) -> str:
    """Summarize an entire ingested page, bypassing retrieval."""
    chunks = _store.get_chunks_by_source(source_id)
    if not chunks:
        raise ValueError("No content found for this source.")

    sources = _store.list_sources()
    title = next((s["title"] for s in sources if s["source_id"] == source_id), "this page")

    full_text = " ".join(chunks)
    return llm_client.summarize_text(title, full_text)