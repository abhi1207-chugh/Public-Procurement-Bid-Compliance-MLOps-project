"""Guards the planted-gap ground truth against drifting from the generated bid files."""
import json
import re
from pathlib import Path

import pytest

from procurement_screening.extraction import extract_document

DATA = Path(__file__).parent.parent / "data" / "synthetic"
TRUTH = json.loads((DATA / "bid_syn_001_truth.json").read_text())


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def _blocks(name: str):
    return extract_document(name, (DATA / name).read_bytes()).blocks


def test_bid_is_three_to_four_pages_and_docx_matches_pdf_text():
    pdf = _blocks("bid_syn_001.pdf")
    assert 3 <= len(pdf) <= 4
    assert _norm(" ".join(b.text for b in _blocks("bid_syn_001.docx"))).count("Rs 38 lakh") == 1


def test_truth_covers_each_case():
    assert {i["case"] for i in TRUTH["items"]} >= {"met", "missing", "wrong_value", "ambiguous"}


@pytest.mark.parametrize("item", [i for i in TRUTH["items"] if i["bid_evidence"]])
def test_evidence_is_in_pdf_page_and_docx(item):
    pdf = {b.page: _norm(b.text) for b in _blocks("bid_syn_001.pdf")}
    assert _norm(item["bid_evidence"]) in pdf[item["bid_pdf_page"]]
    docx_text = _norm(" ".join(b.text for b in _blocks("bid_syn_001.docx")))
    # table rows are joined with " | " in extraction, same as the truth string
    assert _norm(item["bid_evidence"]) in docx_text


def test_missing_item_has_no_iso_9001_anywhere():
    text = " ".join(b.text for b in _blocks("bid_syn_001.pdf"))
    assert "ISO 9001" not in text
