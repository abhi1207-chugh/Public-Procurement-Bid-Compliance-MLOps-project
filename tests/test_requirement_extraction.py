import json

from procurement_screening.extraction import ExtractedDocument, TextBlock
from procurement_screening.requirement_extraction import extract_requirements


class FakeLLM:
    model = "fake"

    def __init__(self):
        self.calls = []

    def generate(self, prompt, *, system=None, schema=None):
        self.calls.append((prompt, system, schema))
        n = len(self.calls)
        return json.dumps(
            {
                "requirements": [
                    {
                        "quote": f"q{n}",
                        "category": "document",
                        "summary": "s",
                        "mandatory": True,
                    }
                ]
            }
        )


def test_ids_and_locators_assigned_by_code():
    doc = ExtractedDocument(
        filename="t.pdf",
        kind="pdf",
        blocks=[
            TextBlock(text="a", page=1, locator="page 1"),
            TextBlock(text="b", page=2, locator="page 2"),
        ],
    )
    llm = FakeLLM()
    reqs = extract_requirements(doc, llm)
    assert [(r.id, r.source_locator) for r in reqs] == [("R1", "page 1"), ("R2", "page 2")]
    assert len(llm.calls) == 2
    assert llm.calls[0][2] is not None  # schema passed
