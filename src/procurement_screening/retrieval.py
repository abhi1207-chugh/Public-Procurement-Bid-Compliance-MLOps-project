"""Retrieve candidate bid evidence for each tender requirement."""
from .requirements import Requirement
from .vector_store import ChunkIndex, ScoredChunk

DEFAULT_K = 4


def build_query(req: Requirement) -> str:
    """Retrieval query for a requirement: the clause text plus the model's summary."""
    return f"{req.summary}. {req.quote}"


def retrieve_evidence(
    index: ChunkIndex, collection: str, req: Requirement, k: int = DEFAULT_K
) -> list[ScoredChunk]:
    return index.search(collection, build_query(req), k=k)
