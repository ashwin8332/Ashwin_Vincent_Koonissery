"""
Data quality validation for extracted PDF tables.

Each check returns a list of ValidationIssue dicts:
  { severity: "ERROR"|"WARNING"|"INFO", check: str, message: str, rows: list[int] }
"""

import re
import pandas as pd


SEVERITY_ORDER = {"ERROR": 0, "WARNING": 1, "INFO": 2}

CURRENCY_PATTERN = re.compile(r"^\$?[\d,]+(\.\d{1,2})?$")
DATE_PATTERN      = re.compile(r"\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}")
PERCENT_PATTERN   = re.compile(r"^\d+(\.\d+)?%$")


def validate_table(df: pd.DataFrame, table_label: str = "Table") -> list[dict]:
    """Run all validation checks and return a unified list of issues."""
    issues = []
    issues += _check_empty_table(df, table_label)
    issues += _check_missing_values(df, table_label)
    issues += _check_duplicate_rows(df, table_label)
    issues += _check_column_consistency(df, table_label)
    issues += _check_mixed_types(df, table_label)
    issues += _check_empty_headers(df, table_label)
    return sorted(issues, key=lambda x: SEVERITY_ORDER.get(x["severity"], 99))


def _check_empty_table(df: pd.DataFrame, label: str) -> list[dict]:
    if df.empty:
        return [{"severity": "ERROR", "check": "empty_table",
                 "message": f"{label}: Table is empty — no data rows extracted.",
                 "rows": []}]
    return []


def _check_missing_values(df: pd.DataFrame, label: str) -> list[dict]:
    issues = []
    for col in df.columns:
        blank_mask = df[col].apply(lambda v: str(v).strip() in ("", "None", "N/A", "nan"))
        blank_rows = df.index[blank_mask].tolist()
        if blank_rows:
            severity = "ERROR" if len(blank_rows) / len(df) > 0.3 else "WARNING"
            issues.append({
                "severity": severity,
                "check":    "missing_values",
                "message":  f"{label} | Column '{col}': {len(blank_rows)} blank/null value(s) "
                            f"({len(blank_rows)/len(df)*100:.1f}% of rows).",
                "rows":     blank_rows,
            })
    return issues


def _check_duplicate_rows(df: pd.DataFrame, label: str) -> list[dict]:
    dupes = df[df.duplicated()].index.tolist()
    if dupes:
        return [{"severity": "WARNING", "check": "duplicate_rows",
                 "message": f"{label}: {len(dupes)} duplicate row(s) detected.",
                 "rows": dupes}]
    return []


def _check_column_consistency(df: pd.DataFrame, label: str) -> list[dict]:
    # Check for auto-generated column names (col_0, col_1...) which indicate a bad header row
    auto_cols = [c for c in df.columns if re.match(r"^col_\d+$", str(c))]
    if auto_cols:
        return [{"severity": "WARNING", "check": "auto_column_names",
                 "message": f"{label}: {len(auto_cols)} column(s) have auto-generated names — "
                            "header row may not have been detected correctly.",
                 "rows": []}]
    return []


def _check_mixed_types(df: pd.DataFrame, label: str) -> list[dict]:
    """
    Detect columns that look mostly numeric but contain some non-numeric values —
    a common sign of merged cells or OCR errors.
    """
    issues = []
    for col in df.columns:
        non_empty = df[col][df[col].apply(lambda v: str(v).strip() not in ("", "N/A", "nan"))]
        if len(non_empty) < 2:
            continue

        numeric_looking = non_empty.apply(_looks_numeric)
        n_numeric   = numeric_looking.sum()
        n_total     = len(non_empty)
        mixed_ratio = n_numeric / n_total

        # If 50–95% are numeric, the column is suspicious (fully numeric is fine)
        if 0.5 < mixed_ratio < 0.95:
            bad_rows = non_empty[~numeric_looking].index.tolist()
            issues.append({
                "severity": "WARNING",
                "check":    "mixed_types",
                "message":  f"{label} | Column '{col}': appears numeric but "
                            f"{n_total - n_numeric} row(s) contain non-numeric values.",
                "rows":     bad_rows,
            })
    return issues


def _check_empty_headers(df: pd.DataFrame, label: str) -> list[dict]:
    empty_headers = [c for c in df.columns if not str(c).strip()]
    if empty_headers:
        return [{"severity": "ERROR", "check": "empty_headers",
                 "message": f"{label}: {len(empty_headers)} column(s) have empty header names.",
                 "rows": []}]
    return []


def _looks_numeric(value: str) -> bool:
    """Return True if value looks like a number, currency, or percentage."""
    v = str(value).strip()
    return bool(
        CURRENCY_PATTERN.match(v) or
        PERCENT_PATTERN.match(v) or
        re.match(r"^-?[\d,]+(\.\d+)?$", v)
    )


def summarize_issues(issues: list[dict]) -> dict:
    errors   = sum(1 for i in issues if i["severity"] == "ERROR")
    warnings = sum(1 for i in issues if i["severity"] == "WARNING")
    return {
        "total":    len(issues),
        "errors":   errors,
        "warnings": warnings,
        "passed":   len(issues) == 0,
    }
