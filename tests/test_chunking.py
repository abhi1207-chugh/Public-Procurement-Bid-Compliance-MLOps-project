import itertools

import pytest

from procurement_screening.chunking import chunk_document
from procurement_screening.extraction import ExtractedDocument, TextBlock


def _doc(*blocks: TextBlock) -> ExtractedDocument:
    return ExtractedDocument(filename="bid.pdf", kind="pdf", blocks=list(blocks))


def test_short_block_is_one_chunk_with_metadata():
    doc = _doc(TextBlock(text="Turnover is Rs 60 lakh.", page=2, locator="page 2"))
    [c] = chunk_document(doc)
    assert c.text == "Turnover is Rs 60 lakh."
    assert (c.page, c.locator, c.filename, c.id) == (2, "page 2", "bid.pdf", "bid.pdf#1")


def test_long_block_splits_and_chunks_are_verbatim_slices():
    text = " ".join(f"word{i}" for i in range(400))
    doc = _doc(TextBlock(text=text, page=1, locator="page 1"))
    chunks = chunk_document(doc, max_chars=200, overlap=40)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.text) <= 200
        assert text[c.start : c.end] == c.text
        assert c.page == 1
    assert len({c.id for c in chunks}) == len(chunks)


def test_chunks_cover_all_text_with_overlap():
    text = " ".join(f"w{i}" for i in range(300))
    chunks = chunk_document(_doc(TextBlock(text=text, page=1, locator="page 1")), 150, 30)
    assert chunks[0].start == 0
    assert chunks[-1].end == len(text)
    for a, b in itertools.pairwise(chunks):
        assert b.start < a.end  # overlap, no gap


def test_chunks_start_at_word_boundaries():
    text = " ".join(f"longword{i}" for i in range(100))
    words = set(text.split())
    for c in chunk_document(_doc(TextBlock(text=text, page=1, locator="page 1")), 120, 40):
        assert c.text.split()[0] in words and c.text.split()[-1] in words


def test_chunks_do_not_span_blocks():
    doc = _doc(
        TextBlock(text="first page text", page=1, locator="page 1"),
        TextBlock(text="second page text", page=2, locator="page 2"),
    )
    chunks = chunk_document(doc)
    assert [(c.page, c.text) for c in chunks] == [(1, "first page text"), (2, "second page text")]


def test_docx_blocks_keep_locator_without_page():
    doc = ExtractedDocument(
        filename="t.docx", kind="docx", blocks=[TextBlock(text="GST required", locator="paragraph 4")]
    )
    [c] = chunk_document(doc)
    assert c.page is None and c.locator == "paragraph 4"


def test_unbroken_text_still_terminates():
    chunks = chunk_document(_doc(TextBlock(text="x" * 1000, page=1, locator="page 1")), 100, 10)
    assert chunks[-1].end == 1000 and all(len(c.text) <= 100 for c in chunks)


def test_empty_document_and_bad_params():
    assert chunk_document(_doc()) == []
    with pytest.raises(ValueError):
        chunk_document(_doc(), max_chars=10, overlap=10)
