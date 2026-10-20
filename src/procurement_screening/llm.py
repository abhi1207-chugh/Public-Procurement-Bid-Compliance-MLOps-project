"""LLM provider interface, Ollama client, and an on-disk response cache.

Calls are deterministic (temperature 0) and cached by a hash of model + prompts + schema +
options, so repeated evaluation runs are fast and reproducible.
"""
import hashlib
import json
from pathlib import Path
from typing import Protocol

import httpx

from .config import Settings, get_settings


class LLMError(RuntimeError):
    """Raised when the LLM backend fails or returns an unusable response."""


class LLMProvider(Protocol):
    model: str

    def generate(
        self, prompt: str, *, system: str | None = None, schema: dict | None = None
    ) -> str:
        """Return the model's text. If schema is given, the text is JSON matching it."""
        ...


class OllamaProvider:
    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        num_ctx: int = 4096,
        timeout_s: float = 120.0,
        client: httpx.Client | None = None,
    ):
        self.model = model
        self.num_ctx = num_ctx
        self._client = client or httpx.Client(base_url=base_url, timeout=timeout_s)

    @property
    def options(self) -> dict:
        return {"temperature": 0, "seed": 0, "num_ctx": self.num_ctx}

    def generate(
        self, prompt: str, *, system: str | None = None, schema: dict | None = None
    ) -> str:
        body: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": self.options,
        }
        if system:
            body["system"] = system
        if schema:
            body["format"] = schema
        try:
            r = self._client.post("/api/generate", json=body)
            r.raise_for_status()
            text = r.json()["response"]
        except (httpx.HTTPError, KeyError, ValueError) as e:
            raise LLMError(f"Ollama request failed: {e}") from e
        return text


class CachedProvider:
    """Wraps a provider; identical (model, options, system, prompt, schema) hits disk."""

    def __init__(self, inner: LLMProvider, cache_dir: Path | str):
        self.inner = inner
        self.model = inner.model
        self.cache_dir = Path(cache_dir)
        self.hits = 0
        self.misses = 0

    def _key(self, prompt: str, system: str | None, schema: dict | None) -> str:
        payload = {
            "model": self.inner.model,
            "options": getattr(self.inner, "options", {}),
            "system": system,
            "prompt": prompt,
            "schema": schema,
        }
        blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode()).hexdigest()

    def generate(
        self, prompt: str, *, system: str | None = None, schema: dict | None = None
    ) -> str:
        path = self.cache_dir / f"{self._key(prompt, system, schema)}.json"
        if path.exists():
            try:
                cached = json.loads(path.read_text())["response"]
                self.hits += 1
                return cached
            except (OSError, ValueError, KeyError):
                pass  # corrupt entry: fall through and regenerate
        text = self.inner.generate(prompt, system=system, schema=schema)
        self.misses += 1
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"model": self.model, "response": text}))
        tmp.replace(path)
        return text


def get_provider(settings: Settings | None = None) -> LLMProvider:
    s = settings or get_settings()
    if s.llm_provider != "ollama":
        raise LLMError(f"unsupported llm_provider {s.llm_provider!r}")
    inner = OllamaProvider(
        s.llm_model, s.ollama_base_url, s.llm_num_ctx, s.llm_timeout_s
    )
    return CachedProvider(inner, s.llm_cache_dir)
