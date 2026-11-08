An embedding is a list of numbers that represents the meaning of a piece of text. Texts with similar meanings have embeddings that are close together, even if they use different words.

ChromaDB is a vector database. It stores text chunks along with their embeddings and metadata, and it can find the chunks most similar to a question.

Cosine distance measures how different two embeddings are. A distance of 0 means the texts are nearly identical in meaning, while larger distances mean they are less related.

Chunking means splitting documents into smaller pieces before storing them. Smaller chunks make search results more precise, but chunks that are too small can lose important context.

Ollama runs large language models locally on your own computer. Models such as llama3.2:1b are downloaded with "ollama pull" and can be called through a REST API on port 11434.

Running models locally keeps data private and avoids API costs, but small models on a CPU are slower and less capable than large cloud models.
