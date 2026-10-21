from procurement_screening.requirements import Category, Requirement
from procurement_screening.retrieval import build_query, retrieve_evidence


def req(**kw):
    base = {
        "quote": "The bidder must hold a valid ISO 9001 certification.",
        "category": Category.certification,
        "summary": "Valid ISO 9001 certificate",
        "id": "R3",
        "source_locator": "page 1",
        "mandatory": True,
    }
    return Requirement(**{**base, **kw})


class FakeIndex:
    def __init__(self):
        self.calls = []

    def search(self, collection, query, k=5, page=None):
        self.calls.append((collection, query, k))
        return ["hit"]


def test_query_uses_summary_and_quote():
    q = build_query(req())
    assert "Valid ISO 9001 certificate" in q and "must hold a valid ISO 9001" in q


def test_retrieve_passes_collection_and_k():
    idx = FakeIndex()
    assert retrieve_evidence(idx, "bid1", req(), k=3) == ["hit"]
    assert idx.calls[0][0] == "bid1" and idx.calls[0][2] == 3

