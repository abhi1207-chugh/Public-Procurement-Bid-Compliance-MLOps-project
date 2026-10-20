# Progress Tracker

Target: working end-to-end project in ONE WEEK (Day 1 = first day of Phase 2 work).
Last updated: 2026-10-20

## Next up
- [ ] **Day 1:** PDF/DOCX extraction with page references + upload validation (see Day 1 below).

## Machine constraints (M1, 8 GB RAM) that shape this plan
- One model loaded at a time (`OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NUM_PARALLEL=1`, `num_ctx` 4096).
- Develop Qdrant in embedded/local mode (`QdrantClient(path=...)`) on Days 3-5 to save RAM;
  use the Qdrant container only in the Day 6 Compose stack.
- Docker Desktop memory capped ~3 GB. Compose services: api, postgres (host port 5433), qdrant,
  mlflow (SQLite backend, no extra DB). Prometheus/Grafana are NOT in scope.
- Run evaluations while Docker is stopped; close heavy apps. Cache every LLM call by hash.
- ~11-24 GiB free disk: no large downloads; keep datasets small; never prune other projects' Docker items.
- LLM is `llama3.2` (3B); embeddings `nomic-embed-text` (both already installed).

## One-week plan
### Phase 1: Foundation (DONE)
- [x] Environment checks (Python 3.13, Git, Docker, Ollama; disk freed to 24 GiB)
- [x] Ollama structured-output test (llama3.2): schema-valid; copy-as-written amount pattern works (1 sample, not an accuracy claim)
- [x] Repo, layout, config, `/health`, test, README, CLAUDE.md, PROGRESS.md
- [x] Mac venv + tests pass + server runs locally
- [x] GitHub Actions: pytest + ruff (green on GitHub: Python 3.10 and 3.13)

### Day 1: Document processing
- [ ] PDF/DOCX extraction with page references (PyMuPDF, python-docx)
- [ ] Upload validation (type, size, filename/path safety)
- [ ] Tests on small sample files; README note

### Day 2: LLM extraction
- [ ] LLM provider interface + Ollama client + on-disk cache (model+prompt+input hash)
- [ ] Pydantic `Requirement` schema; prompt with category definitions; amount-as-written field
- [ ] Deterministic amount parser (lakh/crore/crore -> rupees) with unit tests
- [ ] Extract requirements from one synthetic tender; inspect results manually

### Day 3: RAG
- [ ] Chunking with page/source metadata
- [ ] Embeddings (nomic-embed-text) + Qdrant (embedded mode) indexing
- [ ] Retrieval of bid evidence per requirement
- [ ] Evidence assessment prompt + citation validation (quote must exist in source)

### Day 4: Compliance engine, report, dataset
- [ ] Deterministic checks (thresholds, dates, required docs)
- [ ] Statuses: compliant / non-compliant / missing evidence / ambiguous (-> human review)
- [ ] Screening report (JSON + readable) with source refs and review flags
- [ ] Small SYNTHETIC dataset (~3 tenders, ~100 labeled pairs, clearly marked synthetic), split by tender

### Day 5: Evaluation and MLflow
- [ ] Baseline A (rules-only) and Baseline B (basic RAG)
- [ ] Minimal Model C: metadata filtering + abstention/review routing (no reranker)
- [ ] Evaluation script: Recall@k, MRR, macro F1, per-class P/R, citation correctness, latency
- [ ] MLflow logging (SQLite); DVC tracking the dataset only
- [ ] Record ACTUAL results and failure cases

### Day 6: Containers, persistence, CI
- [ ] FastAPI endpoints: upload tender/bid, screen, get report
- [ ] PostgreSQL persistence + audit metadata
- [ ] Dockerfile + Docker Compose (api, postgres:5433, qdrant, mlflow); health checks
- [ ] CI: ruff + pytest (+ simple eval regression gate on a tiny fixed set)

### Day 7: Delivery
- [ ] README: architecture diagram, setup, API examples, demo workflow
- [ ] Results + limitations (small synthetic dataset, simplified rules, 3B model)
- [ ] Clean-clone reproduction check

### Out of scope (documented as future work)
Prometheus/Grafana, Evidently drift monitoring, reviewer feedback loop, reranker, OCR (unless a sample needs it), release rollback automation.

## Log
- 2026-10-20: Environment verified. Foundation committed (1 test passes on a Linux VM, Python 3.10;
  not yet verified on the Mac venv).
- 2026-10-20: Mac venv (Python 3.13.7) created; `pytest` 1 passed, `ruff check .` clean, uvicorn `/health` returned 200 with expected JSON.
- 2026-10-20: Added `.github/workflows/ci.yml` (ruff + pytest, Python 3.10 and 3.13). YAML parses; same commands pass locally. Not yet run on GitHub.
- 2026-10-20: Pushed to GitHub (origin). First CI run green on Python 3.10 and 3.13.
- 2026-10-20: Switched to one-week plan tailored to M1/8GB; monitoring stack moved out of scope.
