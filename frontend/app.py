# Streamlit frontend: the user interface for the RAG API
# It never talks to Ollama or ChromaDB directly; everything goes through the backend
import os

import requests
import streamlit as st

# API_URL is set in docker-compose.yml to http://backend:8000
# Inside Docker, the service name "backend" works as a hostname
# The localhost default is only used when running outside Docker
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="RAG Assistant", page_icon="📚")
st.title("📚 RAG Assistant")

# --- Sidebar: health status + re-index button ---
with st.sidebar:
    st.header("System Status")
    # Check /health on every page load to show backend and Ollama status
    # Ollama shows "connected" or "unavailable"; if the backend is down, an error is shown instead
    try:
        health = requests.get(f"{API_URL}/health", timeout=5).json()
        st.success("Backend: connected")
        if health["ollama"] == "connected":
            st.success("Ollama: connected")
        else:
            st.warning("Ollama: unavailable")
        st.metric("Indexed chunks", health["documents"])
    except requests.exceptions.RequestException:
        st.error(f"Can't reach backend at {API_URL}")

    st.divider()
    # Re-index: tells the backend to reload all files in docs/ into ChromaDB
    # Long timeout because the first run downloads the embedding model
    if st.button("🔄 Re-index Documents", use_container_width=True):
        with st.spinner("Indexing documents..."):
            try:
                r = requests.post(f"{API_URL}/reindex", timeout=300)
                r.raise_for_status()
                data = r.json()
                st.success(f"Indexed {data['chunks']} chunks from {len(data['files'])} files")
                for name in data["files"]:
                    st.caption(f"• {name}")
            except requests.exceptions.RequestException as e:
                st.error(f"Re-index failed: {e}")

# --- Main: ask a question (user input) ---
question = st.text_input("Ask a question about your documents:")

# Send the question to the backend; long timeout because the LLM can be slow on CPU
if st.button("Ask", type="primary") and question:
    with st.spinner("Thinking..."):
        try:
            r = requests.post(f"{API_URL}/ask", json={"question": question}, timeout=180)
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
            st.stop()

    st.subheader("Answer")
    st.write(data["answer"])

    # Source citations: show which file each retrieved chunk came from
    # Lower distance = closer match to the question
    if data["sources"]:
        st.subheader("Sources")
        for i, s in enumerate(data["sources"], start=1):
            with st.expander(f"[{i}] {s['source']} (distance: {s['distance']})"):
                st.write(s["text"])