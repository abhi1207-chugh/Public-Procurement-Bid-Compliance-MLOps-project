# Progress Tracker

Last updated: 2026-10-20

## Next up
- [ ] **Phase 1 / finish:** create the Mac `.venv`, `pip install -e ".[dev]"`, run `pytest` and
      `uvicorn procurement_screening.main:app`, confirm `/health` works.

## Roadmap
### Phase 1: Foundation
- [x] Environment checks (Python 3.13, Git, Docker, Ollama; disk freed to 24 GiB)
- [x] Ollama structured-output test (llama3.2): schema-valid; copy-as-written amount pattern works (1 sample, not an accuracy claim)
- [x] Repo, layout, config, `/health`, test, README, CLAUDE.md, PROGRESS.md
- [ ] Mac venv + tests pass + server runs locally
- [ ] GitHub Actions: pytest + ruff
### Phase 2: Document processing
- [ ] PDF/DOCX extraction with page references (PyMuPDF, python-docx)
- [ ] Upload validation (type, size, path safety)
- [ ] Extraction quality checks
### Phase 3: Requirement extraction and RAG
- [ ] LLM client (Ollama) behind a provider interface + response cache
- [ ] Requirement extraction -> Pydantic `Requirement` (+ amount parser for lakh/crore)
- [ ] Chunking, embeddings (nomic-embed-text), Qdrant indexing
- [ ] Retrieval + source-grounded evidence assessment + citation validation
### Phase 4: Compliance engine and API
- [ ] Deterministic checks (thresholds, dates, required fields)
- [ ] Findings: compliant / non-compliant / missing evidence / ambiguous
- [ ] Reports with source refs + review flags
- [ ] PostgreSQL persistence + audit metadata; API endpoints
### Phase 5: Evaluation
- [ ] Labeled dataset (public + clearly marked synthetic), split by tender
- [ ] Baseline A rules-only, B basic RAG, C improved RAG
- [ ] Metrics: Recall@k, MRR, macro F1, citation correctness, latency
### Phase 6: MLOps
- [ ] MLflow tracking, DVC dataset versioning, versioned prompts/configs
- [ ] CI quality gates on eval metrics
### Phase 7: Containers and CI/CD
- [ ] Dockerfile + Docker Compose (api, postgres, qdrant, mlflow)
- [ ] GitHub Actions: tests, lint, security, eval gate
### Phase 8: Monitoring and delivery
- [ ] Prometheus + Grafana; drift/behavior checks
- [ ] Final docs, architecture diagram, results, demo

## Log
- 2026-10-20: Environment verified. Foundation committed (1 test passes on a Linux VM, Python 3.10;
  not yet verified on the Mac venv).
