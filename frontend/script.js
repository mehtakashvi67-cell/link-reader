// script.js
// ---------
// This is the ENTIRE client side of the client-server architecture.
// It talks to the FastAPI server over plain HTTP -- nothing more.

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

const ingestForm = document.getElementById("ingest-form");
const urlInput = document.getElementById("url-input");
const ingestBtn = document.getElementById("ingest-btn");
const ingestStatus = document.getElementById("ingest-status");
const sourcesList = document.getElementById("sources-list");
const sourceSelect = document.getElementById("source-select");

const queryForm = document.getElementById("query-form");
const questionInput = document.getElementById("question-input");
const queryBtn = document.getElementById("query-btn");
const answerBlock = document.getElementById("answer-block");
const answerText = document.getElementById("answer-text");
const retrievalList = document.getElementById("retrieval-list");

let currentSources = [];

function setStatus(el, message, type) {
  el.textContent = message;
  el.className = `status-line ${type || ""}`;
}

function startReadingStatus() {
  const phrases = [
    "Opening the link…",
    "Reading the page…",
    "Making sense of it…",
    "Saving it for you…",
  ];
  let i = 0;
  setStatus(ingestStatus, phrases[0], "loading");
  const timer = setInterval(() => {
    i = (i + 1) % phrases.length;
    setStatus(ingestStatus, phrases[i], "loading");
  }, 1100);
  return () => clearInterval(timer);
}

ingestForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const url = urlInput.value.trim();
  if (!url) return;

  ingestBtn.disabled = true;
  const stopStatus = startReadingStatus();

  try {
    const res = await fetch(`${API_BASE}/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || "We couldn't read that link. Double-check it and try again.");

    stopStatus();
    setStatus(ingestStatus, `Got it — saved "${data.title}"`, "ok");
    urlInput.value = "";
    await refreshSources();
  } catch (err) {
    stopStatus();
    setStatus(ingestStatus, err.message, "error");
  } finally {
    ingestBtn.disabled = false;
  }
});

async function refreshSources() {
  const res = await fetch(`${API_BASE}/sources`);
  const data = await res.json();
  currentSources = data.sources || [];

  sourceSelect.innerHTML = `<option value="">Look through everything I've added</option>`;
  data.sources.forEach(src => {
    const opt = document.createElement("option");
    opt.value = src.source_id;
    opt.textContent = src.title;
    sourceSelect.appendChild(opt);
  });

  renderSourcesList();
}

function renderSourcesList() {
  sourcesList.innerHTML = "";

  if (!currentSources.length) {
    sourcesList.innerHTML = `<li class="empty-hint">Nothing here yet — paste a link above to get started.</li>`;
    return;
  }

  currentSources.forEach(src => {
    const li = document.createElement("li");
    li.dataset.sourceId = src.source_id;
    li.innerHTML = `
      <span class="source-title">${escapeHtml(src.title)}</span>
      <span class="source-url">${escapeHtml(src.url)}</span>
      <div class="source-actions">
        <button type="button" class="ghost-btn summarize-btn">Summarize</button>
      </div>
      ${src.summary ? renderSummaryBox(src.summary) : ""}
    `;
    li.querySelector(".summarize-btn").addEventListener("click", () => summarizeSource(src.source_id, li));
    sourcesList.appendChild(li);
  });
}

function renderSummaryBox(summary) {
  return `
    <div class="summary-box">
      <span class="summary-label">Quick summary</span>
      ${escapeHtml(summary)}
    </div>
  `;
}

async function summarizeSource(sourceId, listItemEl) {
  const btn = listItemEl.querySelector(".summarize-btn");
  const originalLabel = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Summarizing…";

  try {
    const res = await fetch(`${API_BASE}/summarize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source_id: sourceId }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Couldn't summarize this one — try again in a moment.");

    const src = currentSources.find(s => s.source_id === sourceId);
    if (src) src.summary = data.summary;

    const existingBox = listItemEl.querySelector(".summary-box");
    if (existingBox) existingBox.remove();
    listItemEl.insertAdjacentHTML("beforeend", renderSummaryBox(data.summary));
  } catch (err) {
    const existingBox = listItemEl.querySelector(".summary-box");
    if (existingBox) existingBox.remove();
    listItemEl.insertAdjacentHTML(
      "beforeend",
      `<div class="summary-box" style="border-color: var(--danger);">${escapeHtml(err.message)}</div>`
    );
  } finally {
    btn.disabled = false;
    btn.textContent = originalLabel;
  }
}

queryForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  queryBtn.disabled = true;
  answerBlock.classList.add("hidden");
  retrievalList.innerHTML = `<p class="empty-hint">Looking through what you've added…</p>`;

  try {
    const res = await fetch(`${API_BASE}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        source_id: sourceSelect.value || null,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "We couldn't answer that — try rephrasing your question.");

    answerText.textContent = data.answer;
    answerBlock.classList.remove("hidden");

    renderRetrievedChunks(data.retrieved_chunks);
  } catch (err) {
    retrievalList.innerHTML = `<p class="empty-hint" style="color: var(--danger)">${escapeHtml(err.message)}</p>`;
  } finally {
    queryBtn.disabled = false;
  }
});

function confidenceLabel(score) {
  if (score >= 0.75) return { text: "Strong match", cls: "high" };
  if (score >= 0.5) return { text: "Decent match", cls: "medium" };
  return { text: "Loose match", cls: "low" };
}

function renderRetrievedChunks(chunks) {
  if (!chunks.length) {
    retrievalList.innerHTML = `<p class="empty-hint">We couldn't find anything relevant for that question.</p>`;
    return;
  }

  retrievalList.innerHTML = "";
  chunks.forEach((chunk) => {
    const pct = Math.round(chunk.similarity * 100);
    const confidence = confidenceLabel(chunk.similarity);
    const card = document.createElement("div");
    card.className = "chunk-card";
    card.innerHTML = `
      <div class="chunk-header">
        <span class="chunk-confidence ${confidence.cls}">${confidence.text}</span>
        <span>${pct}%</span>
      </div>
      <div class="similarity-meter"><div class="similarity-fill" style="width:${pct}%"></div></div>
      <div class="chunk-text">${escapeHtml(chunk.text)}</div>
      <div class="chunk-source">from ${escapeHtml(chunk.source_title)}</div>
    `;
    retrievalList.appendChild(card);
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

refreshSources();