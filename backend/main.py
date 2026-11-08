# RAG API backend: indexes documents into ChromaDB and answers
# the questions asked with Ollama, using only the retrieved text as context
from pathlib import Path

import chromadb
import requests

# All settings (Ollama URL, model, paths, threshold) come from config.py,
# which reads them from environment variables loaded from .env by Docker Compose
from config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# CORS allows other origins (like the Streamlit frontend) to call this API
app = FastAPI(title="RAG API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

DOCS_DIR = Path(settings.DOCS_DIRECTORY)  # /app/docs in the container (set in .env)

# PersistentClient saves data to CHROMA_PATH (/app/chroma_data), which is mounted
# as the chroma_data named volume, so embeddings survive container restarts
# Cosine distance is used to measure how similar a question is to each chunk
client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
collection = client.get_or_create_collection(
    settings.COLLECTION_NAME, configuration={"hnsw": {"space": "cosine"}}
)


# Health check: used by the Docker healthcheck and the frontend sidebar
# Also pings Ollama at http://ollama:11434 (service name = hostname on the Docker network)
@app.get("/health")
def health():
    ollama_ok = False
    try:
        r = requests.get(f"{settings.OLLAMA_URL}/api/tags", timeout=3)
        ollama_ok = r.status_code == 200
    except requests.RequestException:
        pass
    return {
        "status": "healthy",
        "ollama": "connected" if ollama_ok else "unavailable",
        "ollama_url": settings.OLLAMA_URL,
        "documents": collection.count(),
    }

# Stats endpoint: reports how many documents are stored
@app.get("/stats")
def stats():
    return {"document_count": collection.count()}


# Root endpoint: quick check that the API is running and which model it uses
@app.get("/")
def root():
    return {"message": "RAG API running in Docker", "model": settings.MODEL_NAME}


# Wipe the collection and reload every .txt/.md file in docs/
# Called by the "Re-index Documents" button in the frontend
# Deleting and recreating the collection avoids duplicate chunks on repeated re-indexes
@app.post("/reindex")
def reindex():
    global collection
    client.delete_collection(settings.COLLECTION_NAME)
    collection = client.get_or_create_collection(
        settings.COLLECTION_NAME, configuration={"hnsw": {"space": "cosine"}}
    )

    files = sorted(list(DOCS_DIR.glob("*.txt")) + list(DOCS_DIR.glob("*.md")))
    ids, texts, metadatas = [], [], []
    for f in files:
        text = f.read_text(encoding="utf-8")
        # Simple chunking: split on blank lines (paragraphs)
        chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
        for i, chunk in enumerate(chunks):
            ids.append(f"{f.stem}_{i}")
            texts.append(chunk)
            # Store the file name as metadata so answers can cite their source
            metadatas.append({"source": f.name})

    if texts:
        collection.add(ids=ids, documents=texts, metadatas=metadatas)

    return {"files": [f.name for f in files], "chunks": len(texts)}


# Pydantic model: validates the request body for POST /documents
class Document(BaseModel):
    text: str


# Add a single document manually (without putting a file in docs/)
@app.post("/documents")
def add_document(doc: Document):
    doc_id = f"doc_{collection.count() + 1}"
    collection.add(documents=[doc.text], ids=[doc_id],
                   metadatas=[{"source": "manual entry"}])  # label manual docs
    return {"added": doc_id, "documents": collection.count()}


# Pydantic model: validates the request body for POST /ask
class Question(BaseModel):
    question: str


# RAG flow: Step 1) search ChromaDB for relevant chunks, Step 2) filter out weak matches,
# Step 3) send the chunks + question to Ollama, Step 4) return the answer with its sources
@app.post("/ask")
def ask(q: Question):
    if collection.count() == 0:
        return {"answer": "No documents yet. Click Re-index Documents first.", "sources": []}

    # Retrieve: ChromaDB embeds the question and returns the closest chunks
    results = collection.query(
        query_texts=[q.question],
        n_results=min(settings.MAX_RESULTS, collection.count()),
    )

    # Keep only close-enough matches (cosine distance: 0 = identical, 2 = opposite)
    sources = []  # keep file name + text for citations
    for doc, meta, dist in zip(results["documents"][0],
                               results["metadatas"][0],
                               results["distances"][0]):
        if settings.DEBUG:
            print(f"[ask] distance={dist:.3f} doc={doc[:60]!r}")
        if dist <= settings.CONFIDENCE_THRESHOLD:
            sources.append({
                "source": (meta or {}).get("source", "unknown"),
                "text": doc,
                "distance": round(dist, 3),
            })

    if not sources:
        return {"answer": "I don't have information about that in my documents.", "sources": []}

    # Augment: combine the matching chunks into one context block for the prompt
    context = "\n\n".join(s["text"] for s in sources)
    # Generate: Ollama answers using only the context (system prompt reduces hallucination)
    # "stream": False returns the whole answer at once instead of word by word
    response = requests.post(
        f"{settings.OLLAMA_URL}/api/chat",
        json={
            "model": settings.MODEL_NAME,
            "messages": [
                {"role": "system", "content": "Answer using ONLY the context provided. "
                 "If the answer isn't in the context, say you don't know."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {q.question}"},
            ],
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()
    return {"answer": response.json()["message"]["content"], "sources": sources}