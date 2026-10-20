# Public Procurement Bid Compliance Screening Service

RAG + LLM decision-support tool that screens vendor bids against tender requirements,
with evidence-backed findings and human review. **It does not award or reject bids.**

Status: Phase 1 (foundation). No evaluation results exist yet.

## Local setup (macOS)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest
uvicorn procurement_screening.main:app --reload   # http://127.0.0.1:8000/health
```
Local LLM: Ollama (`llama3.2`), embeddings `nomic-embed-text`.

## Design notes
- LLM extracts requirements as structured JSON and copies amounts as written;
  deterministic Python code does unit conversion (lakh/crore) and threshold checks.
- Rules are simplified approximations for demonstration, not legal advice.

## Document processing

`procurement_screening.extraction.extract_document(filename, data)` returns text blocks with
source references: PDFs by 1-based page number, DOCX (no fixed pages) by paragraph/table
index. Scanned PDFs have no text layer and return no blocks (OCR is out of scope).

`procurement_screening.validation` treats uploads as untrusted: extension allowlist
(pdf/docx), 10 MB size limit, magic-byte check that must match the extension, DOCX zip-bomb
check, PDF page limit, encrypted PDFs rejected, and filename sanitization that keeps saved
paths inside the upload directory.
