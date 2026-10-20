import pytest
from pydantic import ValidationError

from procurement_screening.requirements import (
    CATEGORY_DEFINITIONS,
    Category,
    RequirementList,
    build_extraction_prompt,
    extraction_schema,
)


def test_every_category_is_defined():
    assert set(CATEGORY_DEFINITIONS) == set(Category)


def test_valid_payload_keeps_amount_as_written():
    r = RequirementList.model_validate_json(
        '{"requirements":[{"quote":"Turnover of Rs 50 lakh","category":"financial",'
        '"summary":"min turnover","mandatory":true,"amount_as_written":"Rs 50 lakh"}]}'
    )
    assert r.requirements[0].amount_as_written == "Rs 50 lakh"
    assert isinstance(r.requirements[0].amount_as_written, str)


def test_amount_optional():
    r = RequirementList.model_validate_json(
        '{"requirements":[{"quote":"q","category":"document","summary":"s","mandatory":false}]}'
    )
    assert r.requirements[0].amount_as_written is None


@pytest.mark.parametrize(
    "payload",
    [
        '{"requirements":[{"quote":"q","category":"bogus","summary":"s","mandatory":true}]}',
        '{"requirements":[{"quote":"q","category":"other","summary":"s"}]}',
        '{"nope":[]}',
    ],
)
def test_invalid_payload_rejected(payload):
    with pytest.raises(ValidationError):
        RequirementList.model_validate_json(payload)


def test_prompt_contains_categories_and_wraps_text():
    p = build_extraction_prompt("Bidder needs ISO 9001.")
    for c in Category:
        assert f"- {c.value}:" in p
    assert "<tender_text>\nBidder needs ISO 9001.\n</tender_text>" in p


def test_schema_lists_categories_and_required_fields():
    schema = extraction_schema()
    assert "requirements" in schema["properties"]
    assert set(schema["$defs"]["Category"]["enum"]) == {c.value for c in Category}
    assert "amount_as_written" in schema["$defs"]["ExtractedRequirement"]["properties"]
