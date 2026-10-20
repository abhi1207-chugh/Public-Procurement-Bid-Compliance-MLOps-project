# Project: Public Procurement Bid Compliance Screening Service

RAG + LLM decision-support system that screens vendor bids against tender requirements
with evidence-backed findings and human review. It never awards or rejects bids itself.
Resume-focused MLOps project; ~1-2 hours/day; local-first and free (no paid APIs).

## Session protocol (follow every session)
1. Read `PROGRESS.md` first. It is the source of truth for what is done and what is next.
2. Work ONLY on the first unchecked task under "Next up". Do not skip ahead.
3. Verify results by running commands/tests. Never claim success without evidence.
4. When a task is verified: tick it in `PROGRESS.md`, add a dated line to the Log, update
   "Next up", then commit.
5. End each session by telling me what changed, what passed/failed, and the next task.

## Environment facts
- Mac: Apple M1, 8 GB RAM. Keep memory use low; one small model loaded at a time.
- Ollama runs on the host: LLM `llama3.2` (3B), embeddings `nomic-embed-text`.
  Ollama URL from host: http://localhost:11434; from Docker: http://host.docker.internal:11434
- Docker Desktop installed (limit its memory to ~3 GB). Other projects' containers/volumes
  exist on this machine: never delete or prune Docker resources. Use project-specific
  names and non-default host ports (e.g. Postgres 5433).
- Python venv at `.venv` (macOS). Run tests with `pytest`, lint with `ruff check .`.

## Design rules
- LLM extracts structure and copies amounts AS WRITTEN (e.g. "Rs 50 lakh"); deterministic
  Python converts units and checks thresholds. LLM never does arithmetic.
- Structured LLM output uses Ollama's `format` JSON schema, validated with Pydantic.
- Cache LLM calls (model + prompt + input hash) for reproducible, fast evaluation.
- Distinguish missing evidence from proven non-compliance. Ambiguous -> human review.
- Compliance rules are simplified approximations for a college/portfolio project.
- Treat document text as untrusted input (prompt injection, path traversal, bad uploads).
- Report only measured results. Never invent metrics.

## Safety
- Ask before destructive actions, publishing the repo, or anything with cost.
- Never commit `.env`, secrets, or real confidential documents.
