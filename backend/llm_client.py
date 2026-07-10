"""
llm_client.py
-------------
Step 5 of the pipeline: the "generation" half of RAG.

Retrieval (vector_store.py) finds relevant chunks. This file takes those
chunks plus the user's question and asks a local LLM (via Ollama) to write
a grounded answer -- one based on the retrieved text, not the model's
general training knowledge.

Runs 100% locally through Ollama -- no API key, no cost.
Make sure Ollama is running in the background (it usually auto-starts)
and you've pulled a model: `ollama pull llama3.2`
"""

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"

SYSTEM_PROMPT = """You are a precise research assistant. You answer questions using ONLY the
provided context chunks, which were retrieved from a webpage via semantic search.

Rules:
- If the answer is in the context, answer clearly and cite which chunk(s) you used, like [chunk 2].
- If the context does not contain the answer, say so plainly. Do not make anything up.
- Keep answers concise and direct.
"""


def build_context_block(retrieved_chunks: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block for the prompt."""
    parts = []
    for i, chunk in enumerate(retrieved_chunks):
        parts.append(f"[chunk {i}] (similarity: {chunk['similarity']})\n{chunk['text']}")
    return "\n\n".join(parts)


def generate_answer(question: str, retrieved_chunks: list[dict]) -> str:
    """Call the local Ollama model with the retrieved context and return a grounded answer."""
    context_block = build_context_block(retrieved_chunks)

    prompt = f"""{SYSTEM_PROMPT}

Context chunks retrieved from the source page:

{context_block}

Question: {question}"""

    response = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    })
    response.raise_for_status()

    return response.json()["response"].strip()
def summarize_text(title: str, full_text: str) -> str:
    """Summarize an entire page -- no retrieval involved, just the whole text."""
    # Local models have a limited context window, so we cap how much text we send.
    capped_text = full_text[:12000]

    prompt = f"""Summarize the following page titled "{title}" in a way that's clear and exam-ready:
- Start with a 2-3 sentence overview
- Then list the key points as short bullet points
- Define any important terms simply

Page content:
{capped_text}"""

    response = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    })
    response.raise_for_status()
    return response.json()["response"].strip()
# if __name__ == "__main__":
#     fake_chunks = [
#         {"text": "The Eiffel Tower was completed in 1889 for the World's Fair in Paris.", "similarity": 0.91},
#         {"text": "It stands 330 meters tall and was the tallest man-made structure until 1930.", "similarity": 0.85},
#     ]

#     answer = generate_answer("How tall is the Eiffel Tower and when was it built?", fake_chunks)
#     print("ANSWER:\n", answer)