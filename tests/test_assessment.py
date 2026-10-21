import json

import pytest
from pydantic import ValidationError

from procurement_screening.assessment import (
    EvidenceStatus,
    assess_evidence,
    assessment_schema,
    build_assessment_prompt,
)
from procurement_screening.chunking import Chunk
from procurement_screening.requirements import Category, Requirement
from procurement_screening.vector_store import ScoredChunk

REQ = Requirement(
    quote="The bidder must hold a valid ISO 9001 certification.",
    category=Category.certification,
    summary="Valid ISO 9001 certificate",
    id="R3",
    source_locator="page 1",
    mandatory=True,
)


def hit(n, text, page=3):
    c = Chunk(id=f"bid.pdf#{n}", filename="bid.pdf", text=text, page=page,
              locator=f"page {page}", start=0, end=len(text))
    return ScoredChunk(chunk=c, score=0.5)


HITS = [
    hit(1, "Our factory is certified under ISO 14001\n(environmental management)."),
    hit(2, "Turnover was Rs 38 lakh."),
]


class FakeLLM:
    model = "fake"

    def __init__(self, **out):
        self.out = out
        self.calls = []

    def generate(self, prompt, *, system=None, schema=None):
        self.calls.append((prompt, system, schema))
        base = {"evidence_status": "found", "chunk_id": None, "quote": None,
                "value_as_written": None, "explanation": "e"}
        return json.dumps({**base, **self.out})


def test_valid_citation_is_verified_despite_whitespace_and_case():
    llm = FakeLLM(chunk_id="bid.pdf#1", quote="certified under iso 14001 (environmental")
    a = assess_evidence(REQ, HITS, llm)
    assert a.citation_valid and a.source_chunk.id == "bid.pdf#1"
    assert a.effective_status is EvidenceStatus.found
    assert a.source_chunk.page == 3


def test_fabricated_quote_downgraded_to_unclear():
    llm = FakeLLM(chunk_id="bid.pdf#1", quote="We hold ISO 9001 certification")
    a = assess_evidence(REQ, HITS, llm)
    assert not a.citation_valid and a.source_chunk is None
    assert a.evidence_status is EvidenceStatus.found
    assert a.effective_status is EvidenceStatus.unclear


def test_wrong_chunk_id_is_resolved_to_the_chunk_that_contains_the_quote():
    for bad_id in ("bid.pdf#2", "bid.pdf#9", None):
        a = assess_evidence(REQ, HITS, FakeLLM(chunk_id=bad_id, quote="ISO 14001"))
        assert a.citation_valid and a.source_chunk.id == "bid.pdf#1"


def test_quote_not_in_any_retrieved_chunk_is_invalid():
    a = assess_evidence(REQ, HITS, FakeLLM(chunk_id="bid.pdf#2", quote="ISO 9001"))
    assert not a.citation_valid


def test_found_without_quote_is_invalid():
    a = assess_evidence(REQ, HITS, FakeLLM(evidence_status="found"))
    assert not a.citation_valid and a.effective_status is EvidenceStatus.unclear


def test_not_found_needs_no_citation():
    a = assess_evidence(REQ, HITS, FakeLLM(evidence_status="not_found"))
    assert a.citation_valid and a.effective_status is EvidenceStatus.not_found


def test_no_hits_skips_llm():
    llm = FakeLLM()
    a = assess_evidence(REQ, [], llm)
    assert llm.calls == [] and a.effective_status is EvidenceStatus.not_found


def test_value_kept_as_written():
    llm = FakeLLM(chunk_id="bid.pdf#2", quote="Rs 38 lakh", value_as_written="Rs 38 lakh")
    assert assess_evidence(REQ, HITS, llm).value_as_written == "Rs 38 lakh"


def test_bad_llm_output_raises():
    with pytest.raises(ValidationError):
        assess_evidence(REQ, HITS, FakeLLM(evidence_status="compliant"))


def test_prompt_marks_passages_untrusted_and_includes_ids():
    p = build_assessment_prompt(REQ, HITS)
    assert '<passage id="bid.pdf#1" location="page 3">' in p
    assert "not evidence" in p
    assert "untrusted" in assess_evidence.__globals__["SYSTEM_PROMPT"]
    assert "evidence_status" in assessment_schema()["properties"]
