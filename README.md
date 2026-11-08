# The Complete Docker Compose: RAG Stack

A complete Retrieval-Augmented Generation (RAG) application that runs entirely in Docker with one command. Ask questions about your documents in a Streamlit web interface and get answers from a local LLM, with source citations showing exactly where each answer came from.

## Architecture

```
Browser ──► Streamlit frontend ──► FastAPI backend ──► Ollama (llama3.2:1b)
            localhost:8501         backend:8000   │    ollama:11434
                                                  │
                                                  └──► ChromaDB (chroma_data volume)
```

| Service    | Purpose                                                        | Port  |
|------------|----------------------------------------------------------------|-------|
| `frontend` | Streamlit UI: health status, Re-index button, Q&A with sources | 8501  |
| `backend`  | FastAPI RAG API: indexes docs into ChromaDB, queries Ollama    | 8000  |
| `ollama`   | Local LLM server (prebuilt `ollama/ollama` image)              | 11434 |

All services share a private Docker network created by Compose, where each **service name works as a hostname**. The frontend reaches the backend at `http://backend:8000`, and the backend reaches Ollama at `http://ollama:11434`. Inside a container, `localhost` refers to that container itself, so service names are required.

## Project Structure

```
The_Complete_Docker_Compose/
├── backend/
│   ├── docs/                  # Documents to index (.txt / .md)
│   ├── .dockerignore
│   ├── config.py              # Settings loaded from environment variables
│   ├── Dockerfile
│   ├── main.py                # FastAPI RAG API
│   └── requirements.txt
├── frontend/
│   ├── app.py                 # Streamlit UI
│   ├── Dockerfile
│   └── requirements.txt
├── .env                       # Configuration (not committed)
├── .env.example               # Template with placeholder values
├── .gitignore
├── docker-compose.yml
└── README.md
```

## How It Works

1. **Index:** Clicking **Re-index Documents** calls `POST /reindex`. The backend reads every `.txt` and `.md` file in `docs/`, splits each one into paragraph-sized chunks, and stores them in ChromaDB with the file name as metadata.
2. **Retrieve:** When you ask a question, ChromaDB embeds it and returns the most similar chunks, measured by cosine distance.
3. **Filter:** Chunks with a distance above `CONFIDENCE_THRESHOLD` are discarded as weak matches.
4. **Generate:** The remaining chunks are sent to Ollama as context, with a system prompt instructing the model to answer only from that context.
5. **Cite:** The answer is returned along with its sources (file name, chunk text, and distance), which the frontend displays.

## Setup

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 1. Create a `.env` file
Copy the example file and adjust values if needed (`.env` is excluded from Git):

```bash
cp .env.example .env
```

On Windows PowerShell: `Copy-Item .env.example .env`

### 2. Build and start the stack
```bash
docker compose up --build
```

### 3. Pull the model (first run only)
In a second terminal:
```bash
docker compose exec ollama ollama pull llama3.2:1b
```
The model is saved in the `ollama_data` volume, so it only needs to be pulled once.

### 4. Use the app
1. Open http://localhost:8501
2. Click **Re-index Documents**
3. Ask a question, for example *"What is a Dockerfile?"*
4. Expand the **Sources** to see which document each answer came from

## API Endpoints

| Method | Endpoint     | Description                                                    |
|--------|--------------|----------------------------------------------------------------|
| GET    | `/health`    | API status, Ollama connection, and number of indexed chunks    |
| GET    | `/`          | Confirms the API is running and shows the model name           |
| POST   | `/reindex`   | Clears the collection and re-indexes all files in `docs/`      |
| POST   | `/documents` | Adds a single document: `{"text": "..."}`                      |
| POST   | `/ask`       | Answers a question: `{"question": "..."}`, returns answer + sources |

Interactive API docs: http://localhost:8000/docs

## Configuration

| Variable               | Default            | Description                                         |
|------------------------|--------------------|-----------------------------------------------------|
| `OLLAMA_URL`           | `http://localhost:11434` | Ollama address (use `http://ollama:11434` in Docker) |
| `MODEL_NAME`           | `llama3.2:1b`      | Ollama model used for answers                       |
| `CHROMA_PATH`          | `./chroma_data`    | Where ChromaDB stores data (mounted as a volume)    |
| `COLLECTION_NAME`      | `documents`        | ChromaDB collection name                            |
| `MAX_RESULTS`          | `3`                | Maximum chunks retrieved per question               |
| `CONFIDENCE_THRESHOLD` | `1.2`              | Maximum cosine distance for a chunk to count as a match |
| `DEBUG`                | `false`            | Prints configuration and match distances to the logs |
| `DOCS_DIRECTORY`       | `./docs`           | Folder of documents to index                        |

Changes to `.env` take effect after restarting the backend:
```bash
docker compose up -d --force-recreate backend
```
Changes to files in `docs/` require a rebuild (`docker compose up --build`) because documents are copied into the image at build time.

## Docker Features Used

- **Dockerfiles** for the backend and frontend, with `requirements.txt` copied first so dependency layers are cached between code changes
- **Environment variables** via `env_file` (backend) and `environment` (frontend)
- **Port mappings** to reach each service from the host
- **Named volumes:** `chroma_data` keeps indexed documents and `ollama_data` keeps downloaded models. Both persist after `docker compose down` (only `docker compose down -v` removes them)
- **Healthcheck** on the backend, using Python's `urllib` because the slim base image does not include `curl`
- **Dependencies:** the frontend waits until the backend passes its healthcheck (`condition: service_healthy`), and the backend starts after Ollama

## Observations

- **The first question is slower** because Ollama loads the model into memory. After about 5 minutes of inactivity the model is unloaded and reloaded on the next question.
- **The similarity threshold matters.** With `CONFIDENCE_THRESHOLD=1.0`, weakly related chunks (distances around 0.65–0.75) still reach the model. For example, asking *"What is an API?"* returned one strong match (0.47) and four weak ones, and the model blended them into an answer that reversed which service sends requests to which. Lowering the threshold (e.g. to `0.6`) keeps only strong matches and gives the model cleaner context.
- **Small models trade accuracy for speed.** `llama3.2:1b` runs well on a CPU, but sometimes answers from general knowledge instead of saying "I don't know" when the context does not contain the answer.

## Useful Commands

```bash
docker compose up --build        # build and start (shows live logs)
docker compose up -d             # start in the background
docker compose logs -f           # follow logs
docker compose ps                # list running services and health status
docker compose down              # stop and remove containers (volumes kept)
```
