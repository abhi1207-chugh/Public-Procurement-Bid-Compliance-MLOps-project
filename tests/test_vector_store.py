import json

import httpx
import pytest
from qdrant_client import QdrantClient

from procurement_screening.chunking import Chunk
from procurement_screening.embeddings import EmbeddingError, OllamaEmbedder
from procurement_screening.vector_store import ChunkIndex

TOPICS = ["turnover", "gst", "warranty"]


class FakeEmbedder:
    """Bag-of-keywords vectors so retrieval is deterministic without Ollama."""

    model = "fake"

    def _vec(self, text: str) -> list[float]:
        t = text.lower()
        return [float(t.count(w)) + 0.01 for w in TOPICS]

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


def chunk(n, text, page):
    return Chunk(id=f"bid.pdf#{n}", filename="bid.pdf", text=text, page=page,
                 locator=f"page {page}", start=0, end=len(text))


@pytest.fixture
def index():
    return ChunkIndex(QdrantClient(":memory:"), FakeEmbedder())


CHUNKS = [
    chunk(1, "Annual turnover was Rs 60 lakh", 1),
    chunk(2, "GST registration certificate attached", 2),
    chunk(3, "Warranty of 12 months offered", 3),
]


def test_search_returns_best_chunk_with_metadata(index):
    assert index.index("bid1", CHUNKS) == 3
    [top, *_] = index.search("bid1", "what is the turnover?", k=2)
    assert top.chunk.id == "bid.pdf#1"
    assert (top.chunk.page, top.chunk.locator) == (1, "page 1")
    assert top.chunk.text == CHUNKS[0].text


def test_page_filter(index):
    index.index("bid1", CHUNKS)
    hits = index.search("bid1", "turnover", k=5, page=3)
    assert [h.chunk.page for h in hits] == [3]


def test_reindex_replaces_and_collections_are_isolated(index):
    index.index("bid1", CHUNKS)
    index.index("bid2", CHUNKS[:1])
    index.index("bid1", CHUNKS[1:])
    assert len(index.search("bid1", "gst", k=10)) == 2
    assert len(index.search("bid2", "gst", k=10)) == 1


def test_missing_or_empty_collection_returns_nothing(index):
    assert index.search("nope", "turnover") == []
    assert index.index("empty", []) == 0
    assert index.search("empty", "turnover") == []


def test_local_path_persists(tmp_path):
    ChunkIndex(QdrantClient(path=str(tmp_path)), FakeEmbedder()).index("bid1", CHUNKS)
    reopened = QdrantClient(path=str(tmp_path))
    assert len(ChunkIndex(reopened, FakeEmbedder()).search("bid1", "gst")) == 3


def make_embedder(handler):
    client = httpx.Client(base_url="http://x", transport=httpx.MockTransport(handler))
    return OllamaEmbedder("m", client=client)


def test_embedder_prefixes_and_batching():
    seen = []

    def handler(req):
        inputs = json.loads(req.content)["input"]
        seen.append(inputs)
        return httpx.Response(200, json={"embeddings": [[1.0, 2.0]] * len(inputs)})

    e = make_embedder(handler)
    assert len(e.embed_documents([f"t{i}" for i in range(20)])) == 20
    assert [len(b) for b in seen] == [16, 4]
    assert seen[0][0] == "search_document: t0"
    e.embed_query("q")
    assert seen[-1] == ["search_query: q"]


def test_embedder_errors_wrapped():
    with pytest.raises(EmbeddingError):
        make_embedder(lambda r: httpx.Response(500)).embed_query("q")
    with pytest.raises(EmbeddingError):
        make_embedder(lambda r: httpx.Response(200, json={"embeddings": []})).embed_query("q")
