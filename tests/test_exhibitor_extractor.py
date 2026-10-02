"""
Tests for src/exhibitor_extractor.py
=====================================
Author  : Ashwin
GitHub  : https://github.com/ashwin8332

Unit tests for the universal PDF exhibitor extractor.
Covers both Format-A and Format-B parsing, edge cases,
field normalisation, and integration against the Aahar PDF.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.exhibitor_extractor import (
    _detect_format,
    _parse_format_a,
    _parse_format_b,
    _normalise_label,
    _is_noise_line,
    _clean,
    _has_enough_fields,
    extract_exhibitors,
)

AAHAR_PDF = Path(__file__).parent.parent / "data" / "Aahar 2025 Fair Guide.pdf"


# ══════════════════════════════════════════════════════════════════════════════
# Helper builders
# ══════════════════════════════════════════════════════════════════════════════

def _lines(text: str) -> list[str]:
    return [l.rstrip() for l in text.strip().splitlines()]


# ══════════════════════════════════════════════════════════════════════════════
# _detect_format
# ══════════════════════════════════════════════════════════════════════════════

class TestDetectFormat:
    def test_format_b_detected_on_hall_line(self):
        lines = _lines("""
5 AM FARMS LLP HALL: 2 FF
STALL: H2F-01-L
Address: South Wing, Mumbai
Contact Person : John
Tel./Mobile : 9876543210
E-mail : john@example.com
Products on Display : Organic Food
""")
        assert _detect_format(lines) == "B"

    def test_format_a_detected_on_field_labels_only(self):
        lines = _lines("""
ABC EXPORTS PVT. LTD.
Address : 123 Street, Delhi-110001
Contact Person : Jane Doe
Tel./Mobile : 9123456789
E-mail : jane@abc.com
Products on Display : Rice, Wheat
""")
        assert _detect_format(lines) == "A"

    def test_unknown_returns_empty_string(self):
        lines = _lines("""
This is just some random text
Without any recognisable field labels
""")
        assert _detect_format(lines) == ""

    def test_format_b_takes_priority_over_format_a(self):
        # A page that has both HALL lines and field labels is Format-B
        lines = _lines("""
COMPANY XYZ HALL: 3 GF
STALL: H3G-01
Address: Some place
E-mail : x@y.com
""")
        assert _detect_format(lines) == "B"


# ══════════════════════════════════════════════════════════════════════════════
# _normalise_label
# ══════════════════════════════════════════════════════════════════════════════

class TestNormaliseLabel:
    def test_company_name(self):
        assert _normalise_label("Company Name") == "company_name"

    def test_address(self):
        assert _normalise_label("Address") == "address"

    def test_contact_person(self):
        assert _normalise_label("Contact Person") == "contact_person"

    def test_tel_mobile_variants(self):
        for label in ("Tel./Mobile", "Tel./Mob", "Tel.Mobile", "Mobile"):
            result = _normalise_label(label)
            assert result == "tel_mobile", f"Failed for label: {label!r}"

    def test_email_variants(self):
        for label in ("E-mail", "Email", "E-Mail"):
            assert _normalise_label(label) == "email", f"Failed for {label!r}"

    def test_products_on_display(self):
        assert _normalise_label("Products on Display") == "products_on_display"

    def test_unknown_returns_none(self):
        assert _normalise_label("Random Text") is None


# ══════════════════════════════════════════════════════════════════════════════
# _is_noise_line
# ══════════════════════════════════════════════════════════════════════════════

class TestIsNoiseLine:
    def test_bare_page_number(self):
        assert _is_noise_line("5") is True
        assert _is_noise_line("142") is True

    def test_aahar_header(self):
        assert _is_noise_line("AAHAR 2025") is True

    def test_www_line(self):
        assert _is_noise_line("www.indiatradefair.com") is True

    def test_hall_line(self):
        assert _is_noise_line("HALL: 5 GF") is True

    def test_stall_line(self):
        assert _is_noise_line("STALL: H5G-04-A") is True

    def test_normal_address_not_noise(self):
        assert _is_noise_line("123 Main Street, Delhi 110001") is False

    def test_company_name_not_noise(self):
        assert _is_noise_line("ABC EXPORTS PVT. LTD.") is False


# ══════════════════════════════════════════════════════════════════════════════
# _clean
# ══════════════════════════════════════════════════════════════════════════════

class TestClean:
    def test_collapses_double_spaces(self):
        assert _clean("hello   world") == "hello world"

    def test_strips_trailing_comma(self):
        assert _clean("value, ") == "value"

    def test_strips_trailing_semicolon(self):
        assert _clean("value;") == "value"

    def test_strips_leading_trailing_whitespace(self):
        assert _clean("  hello  ") == "hello"

    def test_empty_string_stays_empty(self):
        assert _clean("") == ""


# ══════════════════════════════════════════════════════════════════════════════
# _has_enough_fields
# ══════════════════════════════════════════════════════════════════════════════

class TestHasEnoughFields:
    def test_qualifies_with_address_and_email(self):
        text = "Address: Mumbai\nE-mail: a@b.com"
        assert _has_enough_fields(text) is True

    def test_does_not_qualify_with_only_one_field(self):
        text = "Some text\nAddress: Only one field here"
        assert _has_enough_fields(text) is False

    def test_qualifies_with_tel_and_contact(self):
        text = "Contact Person: Jane\nTel./Mobile: 9999"
        assert _has_enough_fields(text) is True


# ══════════════════════════════════════════════════════════════════════════════
# _parse_format_a (unit tests with synthetic data)
# ══════════════════════════════════════════════════════════════════════════════

class TestParseFormatA:
    def test_basic_single_exhibitor(self):
        lines = _lines("""
ABC EXPORTS PVT. LTD.
Address : 123 Street, Delhi-110001
Contact Person : Jane Doe
Tel./Mobile : 9123456789
E-mail : jane@abc.com
Products on Display : Rice, Wheat
""")
        result = _parse_format_a(lines, page_num=1)
        assert len(result) == 1
        ex = result[0]
        assert ex["company_name"] == "ABC EXPORTS PVT. LTD."
        assert "Delhi" in ex["address"]
        assert ex["contact_person"] == "Jane Doe"
        assert ex["tel_mobile"] == "9123456789"
        assert ex["email"] == "jane@abc.com"
        assert "Rice" in ex["products_on_display"]

    def test_multiline_products_joined(self):
        lines = _lines("""
XYZ FOODS
Address : Some place
E-mail : x@y.com
Products on Display : Rice, Wheat,
Maize, Barley
""")
        result = _parse_format_a(lines, page_num=1)
        assert len(result) >= 1
        ex = result[0]
        assert "Barley" in ex["products_on_display"]

    def test_empty_input_returns_no_results(self):
        assert _parse_format_a([], page_num=1) == []

    def test_noise_lines_excluded_from_company_name(self):
        lines = _lines("""
AAHAR 2025
ABC COMPANY
Address : Some Address
E-mail : abc@company.com
""")
        result = _parse_format_a(lines, page_num=1)
        if result:
            assert "AAHAR" not in result[0]["company_name"]

    def test_missing_email_field_is_empty_string(self):
        lines = _lines("""
NO EMAIL COMPANY
Address : Some Address
Contact Person : John
Tel./Mobile : 9876543210
Products on Display : Product A
""")
        result = _parse_format_a(lines, page_num=1)
        assert len(result) == 1
        assert result[0]["email"] == ""


# ══════════════════════════════════════════════════════════════════════════════
# _parse_format_b (unit tests with synthetic data)
# ══════════════════════════════════════════════════════════════════════════════

class TestParseFormatB:
    def test_basic_single_exhibitor(self):
        lines = _lines("""
DEMO COMPANY LTD HALL: 5 GF
STALL: H5G-04-A
Address: 123 Street, City 100001
Contact Person : John Smith
Tel./Mobile : 9876543210
E-mail : john@demo.com
Products on Display : Spices, Grains
""")
        result = _parse_format_b(lines, page_num=1)
        assert len(result) >= 1
        ex = result[0]
        assert ex["company_name"] == "DEMO COMPANY LTD"
        assert ex["email"] == "john@demo.com"

    def test_multiple_exhibitors_on_one_page(self):
        lines = _lines("""
ALPHA FOODS HALL: 2 FF
STALL: H2F-01-A
Address: Alpha Street
Contact Person : Alice
Tel./Mobile : 111
E-mail : alice@alpha.com
Products on Display : Product A

BETA CORP HALL: 3 GF
STALL: H3G-02-B
Address: Beta Road
Contact Person : Bob
Tel./Mobile : 222
E-mail : bob@beta.com
Products on Display : Product B
""")
        result = _parse_format_b(lines, page_num=1)
        assert len(result) == 2
        names = {ex["company_name"] for ex in result}
        assert "ALPHA FOODS" in names
        assert "BETA CORP" in names

    def test_company_name_continuation_stall(self):
        # Pattern: "TRADE FAIR AUTHORITY OF HALL: 4 GF" / "HARYANA STALL: 4G-07"
        lines = _lines("""
TRADE FAIR AUTHORITY OF HALL: 4 GF
HARYANA STALL: 4G-07
Address: Some address Delhi
Contact Person : Mr. Official
Tel./Mobile : 011-12345
E-mail : official@tfah.gov.in
Products on Display : Govt. Schemes
""")
        result = _parse_format_b(lines, page_num=1)
        assert len(result) == 1
        assert "HARYANA" in result[0]["company_name"]
        assert "STALL" not in result[0]["company_name"]

    def test_single_space_before_hall_matched(self):
        # Regression: regex must match single space (not just 2+)
        lines = _lines("""
5 AM FARMS LLP HALL: 2 FF
STALL: H2F-01-L
Address: Mumbai
E-mail : hello@5amfarms.com
Products on Display : Organic Food
""")
        result = _parse_format_b(lines, page_num=1)
        assert len(result) == 1
        assert result[0]["company_name"] == "5 AM FARMS LLP"


# ══════════════════════════════════════════════════════════════════════════════
# Integration — Aahar PDF (skipped if PDF not present)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(
    not AAHAR_PDF.exists(),
    reason="Aahar 2025 Fair Guide.pdf not found in data/"
)
class TestAaharIntegration:
    def test_extract_returns_list(self):
        result = extract_exhibitors(AAHAR_PDF)
        assert isinstance(result, list)

    def test_significant_number_of_exhibitors(self):
        result = extract_exhibitors(AAHAR_PDF)
        # The Aahar 2025 PDF should yield at least 500 exhibitors
        assert len(result) >= 500, f"Only got {len(result)} exhibitors"

    def test_each_record_has_required_keys(self):
        result = extract_exhibitors(AAHAR_PDF)
        required = {"company_name", "address", "contact_person",
                    "tel_mobile", "email", "products_on_display"}
        for rec in result[:20]:   # spot-check first 20
            assert required == set(rec.keys())

    def test_company_name_completeness_100_pct(self):
        result = extract_exhibitors(AAHAR_PDF)
        blank = sum(1 for r in result if not r["company_name"].strip())
        assert blank == 0, f"{blank} records have blank company_name"

    def test_email_completeness_above_85_pct(self):
        result = extract_exhibitors(AAHAR_PDF)
        filled = sum(1 for r in result if r["email"].strip())
        pct = filled / len(result) * 100
        assert pct >= 85, f"Email completeness {pct:.1f}% below 85%"

    def test_address_completeness_above_95_pct(self):
        result = extract_exhibitors(AAHAR_PDF)
        filled = sum(1 for r in result if r["address"].strip())
        pct = filled / len(result) * 100
        assert pct >= 95, f"Address completeness {pct:.1f}% below 95%"

    def test_no_stall_in_company_names(self):
        result = extract_exhibitors(AAHAR_PDF)
        bad = [r["company_name"] for r in result if "STALL:" in r["company_name"].upper()]
        assert bad == [], f"Company names contain STALL: {bad[:3]}"

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            extract_exhibitors("/nonexistent/path/to/file.pdf")
