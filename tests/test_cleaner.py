"""Tests for src/cleaner.py"""

import pandas as pd
import pytest

from src.cleaner import (
    clean_headers,
    strip_cells,
    coerce_numeric_columns,
    remove_empty_rows,
    remove_duplicate_rows,
    clean_dataframe,
    _dedup_columns,
    _parse_cell,
)


# ── _dedup_columns ─────────────────────────────────────────────────────────────

class TestDedupColumns:
    def test_no_duplicates_unchanged(self):
        assert _dedup_columns(["A", "B", "C"]) == ["A", "B", "C"]

    def test_duplicates_get_suffix(self):
        result = _dedup_columns(["Score", "Score"])
        assert result[0] == "Score"
        assert result[1] == "Score_1"

    def test_triple_duplicates(self):
        result = _dedup_columns(["X", "X", "X"])
        assert result == ["X", "X_1", "X_2"]


# ── _parse_cell ─────────────────────────────────────────────────────────────────

class TestParseCell:
    def test_plain_integer(self):
        assert _parse_cell("42") == 42.0

    def test_float(self):
        assert _parse_cell("3.14") == 3.14

    def test_currency_with_sign_and_commas(self):
        assert _parse_cell("$1,234.56") == 1234.56

    def test_currency_no_cents(self):
        assert _parse_cell("$500") == 500.0

    def test_percentage(self):
        assert _parse_cell("85.5%") == 85.5

    def test_comma_separated_int(self):
        assert _parse_cell("1,000,000") == 1_000_000.0

    def test_na_strings_returned_as_is(self):
        assert _parse_cell("N/A") == "N/A"
        assert _parse_cell("-") == "-"

    def test_text_returned_as_is(self):
        assert _parse_cell("Northeast") == "Northeast"

    def test_empty_returned_as_is(self):
        assert _parse_cell("") == ""


# ── clean_headers ──────────────────────────────────────────────────────────────

class TestCleanHeaders:
    def test_strips_whitespace(self):
        df = pd.DataFrame([[1]], columns=["  Name  "])
        assert clean_headers(df).columns[0] == "name"

    def test_snake_case_conversion(self):
        df = pd.DataFrame([[1]], columns=["Revenue Amount"])
        assert clean_headers(df).columns[0] == "revenue_amount"

    def test_removes_special_chars(self):
        df = pd.DataFrame([[1]], columns=["Amount ($)"])
        col = clean_headers(df).columns[0]
        assert "$" not in col
        assert "(" not in col

    def test_lowercase(self):
        df = pd.DataFrame([[1]], columns=["Region"])
        assert clean_headers(df).columns[0] == "region"

    def test_duplicate_header_deduped(self):
        df = pd.DataFrame([[1, 2]], columns=["Score", "Score"])
        cols = list(clean_headers(df).columns)
        assert "score" in cols
        assert "score_1" in cols

    def test_empty_col_gets_fallback_name(self):
        df = pd.DataFrame([[1, 2]], columns=["", "B"])
        cols = list(clean_headers(df).columns)
        assert cols[0].startswith("col_")


# ── strip_cells ────────────────────────────────────────────────────────────────

class TestStripCells:
    def test_strips_leading_trailing_spaces(self):
        df = pd.DataFrame({"A": ["  hello  "], "B": [" 42 "]})
        result = strip_cells(df)
        assert result.iloc[0]["A"] == "hello"
        assert result.iloc[0]["B"] == "42"

    def test_none_becomes_empty_string(self):
        df = pd.DataFrame({"A": [None]})
        result = strip_cells(df)
        assert result.iloc[0]["A"] == ""


# ── coerce_numeric_columns ──────────────────────────────────────────────────────

class TestCoerceNumericColumns:
    def test_numeric_column_coerced(self):
        df = pd.DataFrame({"Amount": ["$100", "$200", "$300"]})
        result = coerce_numeric_columns(df)
        assert result["Amount"].dtype == float or all(isinstance(v, float) for v in result["Amount"])

    def test_text_column_unchanged(self):
        df = pd.DataFrame({"Region": ["Northeast", "Southeast", "Midwest"]})
        result = coerce_numeric_columns(df)
        assert result["Region"].tolist() == ["Northeast", "Southeast", "Midwest"]

    def test_mixed_column_left_as_is(self):
        # < 60% numeric → not coerced
        df = pd.DataFrame({"Col": ["$100", "text", "more text", "still text"]})
        result = coerce_numeric_columns(df)
        # Should be unchanged (mostly strings)
        assert isinstance(result["Col"].iloc[1], str)


# ── remove_empty_rows ──────────────────────────────────────────────────────────

class TestRemoveEmptyRows:
    def test_drops_all_empty_rows(self):
        df = pd.DataFrame({"A": ["", "x", ""], "B": ["", "y", ""]})
        result = remove_empty_rows(df)
        assert len(result) == 1

    def test_keeps_partial_rows(self):
        df = pd.DataFrame({"A": ["x", ""], "B": ["", "y"]})
        result = remove_empty_rows(df)
        assert len(result) == 2

    def test_index_reset(self):
        df = pd.DataFrame({"A": ["", "x"]})
        result = remove_empty_rows(df)
        assert result.index.tolist() == [0]


# ── remove_duplicate_rows ──────────────────────────────────────────────────────

class TestRemoveDuplicateRows:
    def test_drops_exact_duplicates(self):
        df = pd.DataFrame({"A": ["x", "x", "y"], "B": ["1", "1", "2"]})
        result = remove_duplicate_rows(df)
        assert len(result) == 2

    def test_keeps_unique_rows(self):
        df = pd.DataFrame({"A": ["x", "y"], "B": ["1", "2"]})
        assert len(remove_duplicate_rows(df)) == 2


# ── clean_dataframe (pipeline) ─────────────────────────────────────────────────

class TestCleanDataframe:
    def test_returns_dataframe(self):
        df = pd.DataFrame({"Region": ["NE", "SW"], "Revenue": ["$100", "$200"]})
        result = clean_dataframe(df)
        assert isinstance(result, pd.DataFrame)

    def test_headers_normalized(self):
        df = pd.DataFrame([["NE", "$100"]], columns=["  Region  ", "Revenue Amount"])
        result = clean_dataframe(df)
        assert "region" in result.columns
        assert "revenue_amount" in result.columns

    def test_empty_rows_removed(self):
        df = pd.DataFrame({"A": ["x", "", "y"]})
        result = clean_dataframe(df)
        assert len(result) == 2

    def test_original_not_mutated(self):
        df = pd.DataFrame({"A": [" hello "]})
        original_val = df.iloc[0]["A"]
        clean_dataframe(df)
        assert df.iloc[0]["A"] == original_val
