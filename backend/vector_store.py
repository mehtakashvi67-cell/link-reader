"""
vector_store.py
----------------
Step 4 of the pipeline: the actual "vector DB".

We use ChromaDB, a lightweight open-source vector database that persists
to disk. Its job: given a query vector, find the stored vectors that are
closest to it ("nearest neighbors") -- this is what "semantic search"
means in practice.

Every chunk we store is tagged with a source_id (one per ingested URL) so
we can search within just one page, or across everything ever ingested.
"""

import uuid
import chromadb

from config import VECTOR_DB_DIR, COLLECTION_NAME


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, source_id: str, source_url: str, source_title: str,
                   chunk_texts: list[str], chunk_embeddings: list[list[float]]) -> None:
        """Store a batch of chunks + their embeddings for one ingested URL."""
        ids = [f"{source_id}-{i}" for i in range(len(chunk_texts))]
        metadatas = [
            {"source_id": source_id, "source_url": source_url, "source_title": source_title, "chunk_index": i}
            for i in range(len(chunk_texts))
        ]
        self.collection.add(
            ids=ids,
            embeddings=chunk_embeddings,
            documents=chunk_texts,
            metadatas=metadatas,
        )

    def search(self, query_embedding: list[float], top_k: int, source_id: str | None = None) -> list[dict]:
        """Find the top_k most semantically similar chunks to a query embedding."""
        where_filter = {"source_id": source_id} if source_id else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
        )

        hits = []
        for doc, meta, distance in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            similarity = 1 - distance
            hits.append({
                "text": doc,
                "similarity": round(similarity, 4),
                "source_url": meta["source_url"],
                "source_title": meta["source_title"],
                "chunk_index": meta["chunk_index"],
            })
        return hits

    def list_sources(self) -> list[dict]:
        """Return every distinct URL that's been ingested so far."""
        all_items = self.collection.get()
        seen = {}
        for meta in all_items["metadatas"]:
            seen[meta["source_id"]] = {"source_id": meta["source_id"], "url": meta["source_url"], "title": meta["source_title"]}
        return list(seen.values())
    def get_chunks_by_source(self, source_id: str) -> list[str]:
        """Return every chunk's text for one source, in original order."""
        results = self.collection.get(where={"source_id": source_id})
        pairs = sorted(zip(results["metadatas"], results["documents"]), key=lambda p: p[0]["chunk_index"])
        return [doc for _, doc in pairs]


def new_source_id() -> str:
    return uuid.uuid4().hex[:10]
# if __name__ == "__main__":
#     from scraper import scrape_url
#     from chunker import chunk_text
#     from embeddings import embed_texts, embed_query

#     # Ingest one page
#     page = scrape_url("https://en.wikipedia.org/wiki/Artificial_intelligence")
#     chunks = chunk_text(page.text)
#     chunk_texts = [c.text for c in chunks]
#     vectors = embed_texts(chunk_texts)

#     store = VectorStore()
#     store.add_chunks(
#         source_id="test123",
#         source_url=page.url,
#         source_title=page.title,
#         chunk_texts=chunk_texts,
#         chunk_embeddings=vectors,
#     )
#     print(f"Stored {len(chunk_texts)} chunks.")

#     # Now search it with a real question
#     question = "What are the main goals of AI research?"
#     q_vector = embed_query(question)
#     results = store.search(q_vector, top_k=3)

#     print(f"\nTop matches for: '{question}'\n")
#     for r in results:
#         print(f"[{r['similarity']}] {r['text'][:150]}...\n")