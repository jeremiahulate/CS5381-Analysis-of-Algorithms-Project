# Document Ingestion and Chunking (for Retrieval)

## Purpose

Store project docs in embeddable format for RAG (Retrieval-Augmented Generation). Supports LLM-guided mutations by providing relevant context.

## Input Documents

- **knowledge_docs/raw/**: Original PDFs/text (e.g., research papers, code docs).
- **knowledge_docs/curated/**: Cleaned, structured docs (preferred for retrieval).

## Ingestion Steps

1. **Collect**: Gather docs from raw/ (PDF/TXT/MD).
2. **Convert**: PDFs to text (if needed).
3. **Normalize**: Remove extra spaces, standardize headings, keep structure.
4. **Save**: Store cleaned versions in curated/.

## Chunking Steps

1. **Split**: Divide each doc into chunks (300–800 chars).
2. **Overlap**: Add 50–100 char overlap to preserve context.
3. **Metadata**: For each chunk:
   - source_file
   - chunk_id
   - section/title

## Embedding and Storage

- **Embed**: Use SBERT to vectorize chunks.
- **Store**: Vectors + metadata in FAISS for fast search.
- **Query**: Inner-product similarity for retrieval.

## Pseudocode for Chunking

```python
def chunk_document(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks
```

## Output

- **knowledge_docs/chunks/**: Chunked text (optional).
- FAISS index + metadata for retrieval module.

## Example Chunk

Source: 01_Project_Overview.md
Chunk ID: 0
Text: "Goal: Improve a baseline algorithm automatically over multiple generations using evolutionary techniques..."
