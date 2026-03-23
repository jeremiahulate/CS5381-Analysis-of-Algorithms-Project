# Document Ingestion and Chunking (for Retrieval)

Purpose:
We store project documents in a format that can be embedded and searched (RAG).

Input documents:
- knowledge_docs/raw/ : original PDFs/text
- knowledge_docs/curated/ : cleaned docs (preferred for retrieval)

Ingestion steps:
1) Collect documents in knowledge_docs/raw/ (PDF/TXT/MD).
2) Convert PDFs to text (if needed).
3) Normalize text (remove extra spaces, keep headings).
4) Save cleaned versions in knowledge_docs/curated/.

Chunking steps:
1) Split each curated doc into small chunks (example: 300–800 characters).
2) Keep overlap between chunks (example: 50–100 characters) to avoid losing context.
3) For each chunk, store metadata:
   - source_file
   - chunk_id
   - section/title (if available)

Embedding storage:
- Each chunk is embedded (SentenceTransformers).
- Embeddings + metadata are stored in FAISS for fast retrieval.

Output:
- knowledge_docs/chunks/ : saved chunked text (optional)
- vector index (FAISS) + metadata store used by the retrieval module
