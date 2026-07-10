"""
app.py
------
The "server" half of the client-server architecture.

This is the only file that speaks HTTP. The frontend calls these
endpoints; everything else in backend/ is invisible to it.
Run with:  uvicorn app:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import rag_pipeline
from scraper import ScrapeError

app = FastAPI(title="RAG URL Explorer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class IngestRequest(BaseModel):
    url: str


class QueryRequest(BaseModel):
    question: str
    source_id: str | None = None


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/ingest")
def ingest(req: IngestRequest):
    try:
        result = rag_pipeline.ingest_url(req.url)
    except ScrapeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {exc}")

    return {
        "source_id": result.source_id,
        "url": result.url,
        "title": result.title,
        "num_chunks": result.num_chunks,
        "preview": result.preview,
    }


@app.post("/api/query")
def query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = rag_pipeline.query(req.question, source_id=req.source_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}")

    return {
        "answer": result.answer,
        "retrieved_chunks": result.retrieved_chunks,
    }
class SummarizeRequest(BaseModel):
    source_id: str


@app.post("/api/summarize")
def summarize(req: SummarizeRequest):
    """Summarize a whole ingested page -- doesn't use retrieval."""
    try:
        summary = rag_pipeline.summarize(req.source_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Summarize failed: {exc}")

    return {"summary": summary}


@app.get("/api/sources")
def sources():
    return {"sources": rag_pipeline.list_sources()}