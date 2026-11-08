# Backend image: FastAPI + ChromaDB RAG API
# Slim Python base image keeps the image smaller
FROM python:3.11-slim

# All following commands run inside /app in the container
WORKDIR /app

# Build-essential provides compilers some ChromaDB dependencies need to install
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements first so Docker can cache the pip install layer;
# Dependencies only reinstall when requirements.txt changes, not on every code edit
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code and docs/ (files in .dockerignore, like .env, are skipped)
COPY . .

# Document that the API listens on port 8000
EXPOSE 8000

# Start the API; 0.0.0.0 makes it reachable from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
