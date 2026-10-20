from decimal import Decimal

import pytest

from procurement_screening.amounts import AmountParseError, parse_amount_rupees


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Rs 50 lakh", 5_000_000),
        ("50 lakh", 5_000_000),
        ("Rs. 50 Lakhs", 5_000_000),
        ("rs.50lakh", 5_000_000),
        ("INR 5 lacs", 500_000),
        ("₹ 2,50,000", 250_000),
        ("Rs 50,00,000/-", 5_000_000),
        ("Rs. 1,000,000 only", 1_000_000),
        ("1 crore", 10_000_000),
        ("Rs 2.5 Crore", 25_000_000),
        ("Rs 1.1 crore", 11_000_000),
        ("3 cr", 30_000_000),
        ("Rs 10 thousand", 10_000),
        ("5 million", 5_000_000),
        ("Rs 75000", 75_000),
        ("Rs. 50 Lakhs (Rupees Fifty Lakhs only)", 5_000_000),
        ("  Rs   50   lakh. ", 5_000_000),
        ("Rs 10.55", Decimal("10.55")),
    ],
)
def test_parses(text, expected):
    assert parse_amount_rupees(text) == Decimal(expected)


def test_exact_decimal_no_float_error():
    assert parse_amount_rupees("0.1 lakh") == Decimal(10_000)
    assert isinstance(parse_amount_rupees("1 lakh"), Decimal)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "lakh",
        "Rs",
        "fifty lakh",
        "Rs 50 lakh to 80 lakh",
        "Rs 5 lakh and Rs 3 lakh",
        "50 parsecs",
        "Rs -50 lakh",
        "Rs 1,2,3",
        "turnover of Rs 50 lakh",
    ],
)
def test_rejects_ambiguous_or_invalid(text):
    with pytest.raises(AmountParseError):
        parse_amount_rupees(text)
