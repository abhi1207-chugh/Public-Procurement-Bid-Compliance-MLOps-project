"""Split extracted documents into retrievable chunks that keep their source reference.

A chunk never spans two blocks (pages / paragraphs), so its page and locator are exact.
Chunk text is always a verbatim slice of the block text, which lets later citation
validation check that a quoted span really exists in the source.
"""
from pydantic import BaseModel

from .extraction import ExtractedDocument

DEFAULT_MAX_CHARS = 800
DEFAULT_OVERLAP = 100


class Chunk(BaseModel):
    id: str  # "<filename>#<n>", unique within a document
    filename: str
    text: str
    page: int | None = None
    locator: str
    start: int  # character offsets within the source block text
    end: int


def chunk_document(
    doc: ExtractedDocument,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    if max_chars <= 0 or not 0 <= overlap < max_chars:
        raise ValueError("need max_chars > 0 and 0 <= overlap < max_chars")
    chunks: list[Chunk] = []
    for block in doc.blocks:
        for start, end in _spans(block.text, max_chars, overlap):
            chunks.append(
                Chunk(
                    id=f"{doc.filename}#{len(chunks) + 1}",
                    filename=doc.filename,
                    text=block.text[start:end],
                    page=block.page,
                    locator=block.locator,
                    start=start,
                    end=end,
                )
            )
    return chunks


def _spans(text: str, max_chars: int, overlap: int) -> list[tuple[int, int]]:
    """Windows of at most max_chars, ending at whitespace where possible, trimmed."""
    spans = []
    pos = 0
    n = len(text)
    while pos < n:
        end = min(pos + max_chars, n)
        if end < n:
            cut = max(text.rfind("\n", pos, end), text.rfind(" ", pos, end))
            if cut > pos + max_chars // 2:
                end = cut
        start = pos
        while start < end and text[start].isspace():
            start += 1
        stop = end
        while stop > start and text[stop - 1].isspace():
            stop -= 1
        if stop > start:
            spans.append((start, stop))
        if end >= n:
            break
        pos = max(end - overlap, pos + 1)
    return spans
