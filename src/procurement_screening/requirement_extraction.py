"""Extract requirements from a tender document, one page/section at a time."""
from .extraction import ExtractedDocument
from .llm import LLMProvider
from .requirements import (
    SYSTEM_PROMPT,
    Requirement,
    RequirementList,
    build_extraction_prompt,
    extraction_schema,
    is_mandatory,
)


def extract_requirements(doc: ExtractedDocument, provider: LLMProvider) -> list[Requirement]:
    """Run the LLM over each text block; tie every requirement to its source locator.

    Raises pydantic.ValidationError if the model returns output that breaks the schema.
    """
    schema = extraction_schema()
    found: list[Requirement] = []
    for block in doc.blocks:
        raw = provider.generate(
            build_extraction_prompt(block.text), system=SYSTEM_PROMPT, schema=schema
        )
        for item in RequirementList.model_validate_json(raw).requirements:
            found.append(
                Requirement(
                    **item.model_dump(),
                    id=f"R{len(found) + 1}",
                    source_locator=block.locator,
                    mandatory=is_mandatory(item.quote),
                )
            )
    return found
