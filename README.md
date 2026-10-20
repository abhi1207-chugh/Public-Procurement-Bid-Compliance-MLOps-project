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
