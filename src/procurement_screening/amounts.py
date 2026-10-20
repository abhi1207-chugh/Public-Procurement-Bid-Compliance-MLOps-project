"""Deterministic parsing of Indian-style money amounts into rupees.

The LLM copies amounts as written; this module converts them. It uses Decimal (never
float) and refuses ambiguous input instead of guessing, so callers can route to review.
"""
import re
from decimal import Decimal

UNITS = {
    "": Decimal(1),
    "thousand": Decimal(1_000),
    "k": Decimal(1_000),
    "lakh": Decimal(100_000),
    "lakhs": Decimal(100_000),
    "lac": Decimal(100_000),
    "lacs": Decimal(100_000),
    "crore": Decimal(10_000_000),
    "crores": Decimal(10_000_000),
    "cr": Decimal(10_000_000),
    "million": Decimal(1_000_000),
    "mn": Decimal(1_000_000),
    "billion": Decimal(1_000_000_000),
}

_NUMBER = r"(\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
_PATTERN = re.compile(
    rf"^(?:rs\.?|inr|₹)?\s*{_NUMBER}\s*([a-z]*)\s*(?:/-)?$",
    re.IGNORECASE,
)
_PARENTHETICAL = re.compile(r"\([^)]*\)")


class AmountParseError(ValueError):
    """The text is not a single, unambiguous amount."""


def parse_amount_rupees(text: str) -> Decimal:
    """Convert e.g. 'Rs 50 lakh', '₹ 2,50,000/-', '1.5 crore' to rupees as a Decimal."""
    cleaned = _PARENTHETICAL.sub(" ", text).strip().rstrip(".")
    cleaned = " ".join(cleaned.split())
    cleaned = re.sub(r"\s+only$", "", cleaned, flags=re.IGNORECASE)
    m = _PATTERN.match(cleaned)
    if not m:
        raise AmountParseError(f"cannot parse amount: {text!r}")
    number, unit = m.group(1), m.group(2).lower()
    if unit not in UNITS:
        raise AmountParseError(f"unknown unit {unit!r} in {text!r}")
    return Decimal(number.replace(",", "")) * UNITS[unit]
