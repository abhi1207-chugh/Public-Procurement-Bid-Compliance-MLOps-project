"""Embedding client (Ollama nomic-embed-text). Documents and queries use different prefixes."""
from typing import Protocol

import httpx

from .config import Settings, get_settings

DOC_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "
BATCH_SIZE = 16


class EmbeddingError(RuntimeError):
    """Raised when the embedding backend fails or returns an unusable response."""


class Embedder(Protocol):
    model: str

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class OllamaEmbedder:
    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout_s: float = 120.0,
        client: httpx.Client | None = None,
    ):
        self.model = model
        self._client = client or httpx.Client(base_url=base_url, timeout=timeout_s)

    def _embed(self, inputs: list[str]) -> list[list[float]]:
        try:
            r = self._client.post("/api/embed", json={"model": self.model, "input": inputs})
            r.raise_for_status()
            vectors = r.json()["embeddings"]
        except (httpx.HTTPError, KeyError, ValueError) as e:
            raise EmbeddingError(f"Ollama embed request failed: {e}") from e
        if len(vectors) != len(inputs) or not all(vectors):
            raise EmbeddingError("embedding count or content does not match inputs")
        return vectors

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), BATCH_SIZE):
            out.extend(self._embed([DOC_PREFIX + t for t in texts[i : i + BATCH_SIZE]]))
        return out

    def embed_query(self, text: str) -> list[float]:
        return self._embed([QUERY_PREFIX + text])[0]


def get_embedder(settings: Settings | None = None) -> Embedder:
    s = settings or get_settings()
    return OllamaEmbedder(s.embedding_model, s.ollama_base_url, s.llm_timeout_s)
