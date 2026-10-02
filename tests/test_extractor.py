"""Tests for src/extractor.py"""

import io
from pathlib import Path

import pandas as pd
import pytest

from src.extractor import (
    extract_tables_from_path,
    extract_tables_from_bytes,
    get_pdf_info,
    _table_to_dataframe,
)

SAMPLE_PDF = Path(__file__).parent.parent / "data" / "sample_report.pdf"


# ── _table_to_dataframe ────────────────────────────────────────────────────────

class TestTableToDataframe:
    def test_basic_table(self):
        raw = [
            ["Name",    "Value"],
            ["Alpha",   "100"],
            ["Beta",    "200"],
        ]
        df = _table_to_dataframe(raw)
        assert df is not None
        assert list(df.columns) == ["Name", "Value"]
        assert len(df) == 2

    def test_none_cells_become_empty_string(self):
        raw = [
            ["A", "B"],
            [None, "X"],
        ]
        df = _table_to_dataframe(raw)
        assert df.iloc[0]["A"] == ""

    def test_duplicate_headers_deduped(self):
        raw = [
            ["Score", "Score"],
            ["90",    "85"],
        ]
        df = _table_to_dataframe(raw)
        assert "Score" in df.columns
        assert "Score_1" in df.columns

    def test_missing_cells_padded(self):
        raw = [
            ["A", "B", "C"],
            ["1"],           # only one value
        ]
        df = _table_to_dataframe(raw)
        assert len(df.columns) == 3
        assert df.iloc[0]["B"] == ""
        assert df.iloc[0]["C"] == ""

    def test_empty_rows_dropped(self):
        raw = [
            ["X", "Y"],
            ["",  ""],
            ["a", "b"],
        ]
        df = _table_to_dataframe(raw)
        assert len(df) == 1

    def test_returns_none_for_empty_input(self):
        assert _table_to_dataframe([]) is None

    def test_returns_none_for_header_only(self):
        assert _table_to_dataframe([["A", "B"]]) is None

    def test_strips_whitespace_from_cells(self):
        raw = [
            ["  Col A  ", "Col B"],
            ["  value  ", " 42 "],
        ]
        df = _table_to_dataframe(raw)
        assert df.columns[0] == "Col A"
        assert df.iloc[0]["Col A"] == "value"
        assert df.iloc[0]["Col B"] == "42"

    def test_auto_header_names_for_empty_cells(self):
        raw = [
            [None, "B"],
            ["x",  "y"],
        ]
        df = _table_to_dataframe(raw)
        assert df.columns[0] == "col_0"


# ── Integration: sample PDF ────────────────────────────────────────────────────

@pytest.mark.skipif(not SAMPLE_PDF.exists(), reason="sample_report.pdf not generated")
class TestExtractSamplePdf:
    def test_extract_returns_list(self):
        tables = extract_tables_from_path(SAMPLE_PDF)
        assert isinstance(tables, list)

    def test_at_least_one_table_extracted(self):
        tables = extract_tables_from_path(SAMPLE_PDF)
        assert len(tables) >= 1

    def test_each_result_has_required_keys(self):
        tables = extract_tables_from_path(SAMPLE_PDF)
        required = {"page_number", "table_index", "raw_rows", "dataframe", "row_count", "col_count"}
        for tbl in tables:
            assert required.issubset(tbl.keys())

    def test_dataframe_is_not_empty(self):
        tables = extract_tables_from_path(SAMPLE_PDF)
        for tbl in tables:
            assert not tbl["dataframe"].empty

    def test_row_count_matches_dataframe(self):
        tables = extract_tables_from_path(SAMPLE_PDF)
        for tbl in tables:
            assert tbl["row_count"] == len(tbl["dataframe"])

    def test_col_count_matches_dataframe(self):
        tables = extract_tables_from_path(SAMPLE_PDF)
        for tbl in tables:
            assert tbl["col_count"] == len(tbl["dataframe"].columns)

    def test_extract_from_bytes_matches_from_path(self):
        pdf_bytes = SAMPLE_PDF.read_bytes()
        tables_bytes = extract_tables_from_bytes(pdf_bytes)
        tables_path  = extract_tables_from_path(SAMPLE_PDF)
        assert len(tables_bytes) == len(tables_path)

    def test_get_pdf_info_page_count(self):
        info = get_pdf_info(SAMPLE_PDF)
        assert info["page_count"] >= 1

    def test_get_pdf_info_returns_metadata(self):
        info = get_pdf_info(SAMPLE_PDF)
        assert "metadata" in info
        assert isinstance(info["metadata"], dict)
