"""Tests for src/validator.py"""

import pandas as pd
import pytest

from src.validator import (
    validate_table,
    summarize_issues,
    _check_empty_table,
    _check_missing_values,
    _check_duplicate_rows,
    _check_column_consistency,
    _check_mixed_types,
    _check_empty_headers,
    _looks_numeric,
)


# ── _looks_numeric ─────────────────────────────────────────────────────────────

class TestLooksNumeric:
    def test_integer(self):
        assert _looks_numeric("42")

    def test_float(self):
        assert _looks_numeric("3.14")

    def test_negative(self):
        assert _looks_numeric("-10.5")

    def test_currency(self):
        assert _looks_numeric("$1,234.56")
        assert _looks_numeric("$500")

    def test_percent(self):
        assert _looks_numeric("85.5%")
        assert _looks_numeric("100%")

    def test_comma_separated(self):
        assert _looks_numeric("1,000,000")

    def test_word_is_not_numeric(self):
        assert not _looks_numeric("Revenue")
        assert not _looks_numeric("N/A")

    def test_empty_string_is_not_numeric(self):
        assert not _looks_numeric("")

    def test_date_like_is_not_numeric(self):
        assert not _looks_numeric("2025-12-31")


# ── _check_empty_table ─────────────────────────────────────────────────────────

class TestCheckEmptyTable:
    def test_flags_empty(self):
        issues = _check_empty_table(pd.DataFrame(), "T1")
        assert len(issues) == 1
        assert issues[0]["severity"] == "ERROR"

    def test_passes_non_empty(self):
        df = pd.DataFrame({"A": ["x"]})
        assert _check_empty_table(df, "T1") == []


# ── _check_missing_values ──────────────────────────────────────────────────────

class TestCheckMissingValues:
    def test_detects_blank_cells(self):
        df = pd.DataFrame({"A": ["good", "", "also good"]})
        issues = _check_missing_values(df, "T1")
        assert any("A" in i["message"] for i in issues)

    def test_error_when_majority_blank(self):
        df = pd.DataFrame({"A": ["", "", "", "x"]})
        issues = _check_missing_values(df, "T1")
        error_issues = [i for i in issues if i["severity"] == "ERROR"]
        assert error_issues

    def test_warning_when_minority_blank(self):
        df = pd.DataFrame({"A": ["x", "y", "z", ""]})
        issues = _check_missing_values(df, "T1")
        warn_issues = [i for i in issues if i["severity"] == "WARNING"]
        assert warn_issues

    def test_passes_fully_populated(self):
        df = pd.DataFrame({"A": ["a", "b"], "B": ["1", "2"]})
        assert _check_missing_values(df, "T1") == []

    def test_na_string_flagged(self):
        df = pd.DataFrame({"A": ["N/A"]})
        issues = _check_missing_values(df, "T1")
        assert issues


# ── _check_duplicate_rows ──────────────────────────────────────────────────────

class TestCheckDuplicateRows:
    def test_detects_duplicates(self):
        df = pd.DataFrame({"A": ["x", "x"], "B": ["1", "1"]})
        issues = _check_duplicate_rows(df, "T1")
        assert issues
        assert issues[0]["severity"] == "WARNING"

    def test_passes_unique_rows(self):
        df = pd.DataFrame({"A": ["x", "y"], "B": ["1", "2"]})
        assert _check_duplicate_rows(df, "T1") == []


# ── _check_column_consistency ──────────────────────────────────────────────────

class TestCheckColumnConsistency:
    def test_flags_auto_generated_names(self):
        df = pd.DataFrame([[1, 2]], columns=["col_0", "col_1"])
        issues = _check_column_consistency(df, "T1")
        assert issues
        assert issues[0]["check"] == "auto_column_names"

    def test_passes_real_headers(self):
        df = pd.DataFrame([[1, 2]], columns=["Region", "Revenue"])
        assert _check_column_consistency(df, "T1") == []


# ── _check_mixed_types ─────────────────────────────────────────────────────────

class TestCheckMixedTypes:
    def test_flags_mostly_numeric_with_text(self):
        df = pd.DataFrame({"Amount": ["$100", "$200", "$300", "$400", "PENDING", "$500"]})
        issues = _check_mixed_types(df, "T1")
        assert issues

    def test_passes_fully_numeric(self):
        df = pd.DataFrame({"Amount": ["$100", "$200", "$300", "$400", "$500"]})
        issues = _check_mixed_types(df, "T1")
        assert not issues

    def test_passes_fully_text(self):
        df = pd.DataFrame({"Region": ["Northeast", "Southeast", "Midwest"]})
        issues = _check_mixed_types(df, "T1")
        assert not issues


# ── _check_empty_headers ───────────────────────────────────────────────────────

class TestCheckEmptyHeaders:
    def test_flags_empty_header(self):
        df = pd.DataFrame([["a", "b"]], columns=["", "Valid"])
        issues = _check_empty_headers(df, "T1")
        assert issues
        assert issues[0]["severity"] == "ERROR"

    def test_passes_named_headers(self):
        df = pd.DataFrame([["a"]], columns=["Name"])
        assert _check_empty_headers(df, "T1") == []


# ── validate_table (integration) ───────────────────────────────────────────────

class TestValidateTable:
    def test_clean_table_has_no_issues(self):
        df = pd.DataFrame({"Region": ["NE", "SW"], "Revenue": ["$100", "$200"]})
        issues = validate_table(df, "T1")
        assert all(i["check"] not in ("empty_table", "empty_headers") for i in issues)

    def test_issues_sorted_by_severity(self):
        df = pd.DataFrame()   # empty → ERROR
        issues = validate_table(df, "T1")
        severities = [i["severity"] for i in issues]
        order = {"ERROR": 0, "WARNING": 1, "INFO": 2}
        assert severities == sorted(severities, key=lambda s: order.get(s, 99))


# ── summarize_issues ───────────────────────────────────────────────────────────

class TestSummarizeIssues:
    def test_empty_list_passes(self):
        s = summarize_issues([])
        assert s["passed"] is True
        assert s["errors"] == 0
        assert s["warnings"] == 0
        assert s["total"] == 0

    def test_counts_errors_and_warnings(self):
        issues = [
            {"severity": "ERROR"},
            {"severity": "WARNING"},
            {"severity": "WARNING"},
        ]
        s = summarize_issues(issues)
        assert s["errors"] == 1
        assert s["warnings"] == 2
        assert s["total"] == 3
        assert s["passed"] is False
