"""Qdrant-backed chunk index. One collection per document set (e.g. one per bid).

Uses embedded/local mode (`path=`) in development; pass a URL-based client for the server.
"""
import uuid

from pydantic import BaseModel
from qdrant_client import QdrantClient, models

from .chunking import Chunk
from .embeddings import Embedder


class ScoredChunk(BaseModel):
    chunk: Chunk
    score: float


def _point_id(collection: str, chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{collection}/{chunk_id}"))


class ChunkIndex:
    def __init__(self, client: QdrantClient, embedder: Embedder):
        self.client = client
        self.embedder = embedder

    def index(self, collection: str, chunks: list[Chunk]) -> int:
        """(Re)build a collection from chunks; returns the number indexed."""
        if self.client.collection_exists(collection):
            self.client.delete_collection(collection)
        if not chunks:
            return 0
        vectors = self.embedder.embed_documents([c.text for c in chunks])
        self.client.create_collection(
            collection,
            vectors_config=models.VectorParams(
                size=len(vectors[0]), distance=models.Distance.COSINE
            ),
        )
        self.client.upsert(
            collection,
            points=[
                models.PointStruct(
                    id=_point_id(collection, c.id), vector=v, payload=c.model_dump()
                )
                for c, v in zip(chunks, vectors)
            ],
        )
        return len(chunks)

    def search(
        self, collection: str, query: str, k: int = 5, page: int | None = None
    ) -> list[ScoredChunk]:
        if not self.client.collection_exists(collection):
            return []
        flt = None
        if page is not None:
            flt = models.Filter(
                must=[models.FieldCondition(key="page", match=models.MatchValue(value=page))]
            )
        res = self.client.query_points(
            collection,
            query=self.embedder.embed_query(query),
            query_filter=flt,
            limit=k,
            with_payload=True,
        )
        return [ScoredChunk(chunk=Chunk(**p.payload), score=p.score) for p in res.points]
