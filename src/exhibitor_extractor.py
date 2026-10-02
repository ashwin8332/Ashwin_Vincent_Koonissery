"""
PDF Exhibitor Data Extractor — Universal Engine
================================================
Author  : Ashwin
GitHub  : https://github.com/ashwin8332
Version : 4.0.0

Three-pass extraction algorithm that recovers every entry in the PDF:

  PASS 1 — FORMAT-B PROFILE PAGES
  Pages with "COMPANY NAME  HALL: X" headers. Each page may contain 2-4 full
  exhibitor blocks with Address / Contact Person / Tel / E-mail / Products.

  PASS 2 — FORMAT-A PROFILE PAGES
  Pages with standalone field labels but no HALL: header line.

  PASS 3 — FORMAT-C PARTICIPANT LIST PAGES  (new in v4.0)
  Alphabetical list / FHSAI list pages with tabular S.No. rows:
      S.NO.  COMPANY NAME           STALL NO.  HALL NO.
      1      5 AM FARMS LLP         H2F-01-L   2 FF
  Entries only appear here when they have NO full profile page.
  These are stored as partial records (Name + Stall + Hall in address).
  Deduplication prevents double-counting.

OUTPUT KEYS:
    company_name, address, contact_person, tel_mobile, email, products_on_display
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Optional

import pdfplumber

# ── Column Map ─────────────────────────────────────────────────────────────────
COLUMN_MAP: dict[str, str] = {
    "company_name":        "Company Name",
    "address":             "Address",
    "contact_person":      "Contact Person",
    "tel_mobile":          "Tel./Mobile",
    "email":               "E-mail",
    "products_on_display": "Products on Display",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

MIN_FIELDS_TO_QUALIFY: int = 2

SKIP_KEYWORDS: tuple[str, ...] = (
    "key executives",
    "hall plan",
    "floor plan",
    "organised by\nflavours",
    "www.indiatradefair.com",
)


# ══════════════════════════════════════════════════════════════════════════════
# REGEX PATTERNS
# ══════════════════════════════════════════════════════════════════════════════

# Recognised field-label line
_FIELD_RE = re.compile(
    r"^("
    r"Company\s+Name"
    r"|Address"
    r"|Contact\s+Person"
    r"|Tel\.(?:\s*/\s*)?(?:Mob(?:ile)?|Mobile)?"
    r"|Tel\.?(?:\s*/\s*)?Mob(?:ile)?"
    r"|E-?mail"
    r"|Products?\s+on\s+Display"
    r")\s*[:\-]\s*(.*)$",
    re.IGNORECASE,
)

# Format-B company header:  "COMPANY NAME  HALL: 5 GF"
_FORMAT_B_COMPANY_RE = re.compile(
    r"^(.+?)\s+HALL\s*:\s*(.+)$",
    re.IGNORECASE,
)

# Standalone "STALL: ..." line
_FORMAT_B_STALL_RE = re.compile(
    r"^STALL\s*[:\-]?\s*(.*)$",
    re.IGNORECASE,
)

# Company-name wrap ending in "STALL: X"
_CONT_STALL_RE = re.compile(
    r"^(.+?)\s+STALL\s*:\s*\S.*$",
    re.IGNORECASE,
)

# Stray "HALL: X" that bleeds into address continuation lines
_ADDR_HALL_TAIL_RE = re.compile(
    r"\s+HALL\s*:\s*\S+.*$",
    re.IGNORECASE,
)

# Page-artefact lines — never used as field values
_NOISE_RE = re.compile(
    r"^("
    r"AAHAR\s+20\d\d"
    r"|www\."
    r"|HALL\s*:"
    r"|STALL\s*:"
    r"|\d{1,4}$"
    r"|[ivxlcdm]{1,6}$"
    r"|PARTICIPANTS'?\s+PROFILE"
    r"|FAIR\s+GUIDE"
    r"|ORGANISER"
    r")",
    re.IGNORECASE,
)

# Stall-number token: e.g. H5G-04-A  HH7A  14G-28-A  6--39-C  12--02-C
_STALL_TOKEN_RE = re.compile(r"^[A-Z0-9][A-Z0-9\-]{2,}$", re.IGNORECASE)

# Participant-list page identifier
_LIST_PAGE_RE = re.compile(
    r"(S\.?NO\.?\s+COMPANY\s+NAME|S\.?No\.?\s+PARTICIPANTS\s+NAME)",
    re.IGNORECASE,
)

# Stall-token start patterns:
#   H2F  HH7A  12A-  HANGAR  OPEN
#   Also handles double-dash stalls:  12--02-C  6--39-C  9--01-A
_STALL_START_RE = re.compile(
    r"^(H[A-Z0-9]|HH|[1-9]\d?[A-Z]?--?|HANGAR|OPEN)",
    re.IGNORECASE,
)

# Hall-code suffix at end of a row:  "14 FF"  "5 GF"  "12A"  "9"
# Anchored to end-of-string OR end of a word boundary before more text
_HALL_CODE_RE = re.compile(
    r"(\d+[A-Z]?\s*(?:FF|GF|OPEN(?:\s+AREA)?)?)\s*$",
    re.IGNORECASE,
)
# Same but unanchored — used to find hall-codes anywhere in a wrapped row
_HALL_CODE_ANY_RE = re.compile(
    r"\b(\d+[A-Z]?\s*(?:FF|GF|OPEN(?:\s+AREA)?)?)(?=\s+\S|\s*$)",
    re.IGNORECASE,
)

# Format-C row starts with a serial number
_LISTROW_RE = re.compile(r"^(\d+)\s+(.+)", re.IGNORECASE)


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def extract_exhibitors(pdf_path: str | Path) -> list[dict[str, str]]:
    """
    Three-pass extraction returning every exhibitor in the PDF.

    Pass 1+2 : Full profile pages  (Format-B / Format-A)
    Pass 3   : Participant list pages — fills in entries with no full profile

    Returns a deduplicated list of dicts with keys:
        company_name, address, contact_person, tel_mobile, email,
        products_on_display
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    profile_exhibitors: list[dict[str, str]] = []
    list_entries:       list[dict[str, str]] = []
    stats = {"format_a": 0, "format_b": 0, "format_c": 0, "skipped": 0}

    with pdfplumber.open(str(pdf_path)) as pdf:
        total = len(pdf.pages)
        log.info("Opened PDF: %s  (%d pages)", pdf_path.name, total)

        for page_idx, page in enumerate(pdf.pages):
            # Quick probe with layout=False to detect page type
            raw_text: str = page.extract_text(
                x_tolerance=3,
                y_tolerance=3,
                layout=False,
            ) or ""

            if not raw_text.strip():
                stats["skipped"] += 1
                continue

            # ── Pass 3: Participant-list pages ─────────────────────────────
            # Re-extract with layout=True to preserve column whitespace so
            # stall / hall columns stay clearly separated from the company name.
            if _LIST_PAGE_RE.search(raw_text):
                stats["format_c"] += 1
                raw_layout = page.extract_text(
                    x_tolerance=3,
                    y_tolerance=3,
                    layout=True,
                ) or raw_text
                list_entries.extend(_parse_format_c(raw_layout, page_idx + 1))
                continue

            # ── Pass 1+2: Profile pages ────────────────────────────────────
            if _should_skip(raw_text):
                stats["skipped"] += 1
                continue

            lines = [ln.rstrip() for ln in raw_text.splitlines()]
            fmt   = _detect_format(lines)

            if fmt == "A":
                stats["format_a"] += 1
                exhibitors = _parse_format_a(lines, page_idx + 1)
            elif fmt == "B":
                stats["format_b"] += 1
                exhibitors = _parse_format_b(lines, page_idx + 1)
            else:
                stats["skipped"] += 1
                continue

            profile_exhibitors.extend(ex for ex in exhibitors if _is_valid(ex))

            if (page_idx + 1) % 50 == 0:
                log.info(
                    "  Processed page %d / %d  --  %d profile exhibitors so far",
                    page_idx + 1, total, len(profile_exhibitors),
                )

    merged = _merge_list_entries(profile_exhibitors, list_entries)

    log.info(
        "Extraction complete: %d exhibitors total  "
        "(Format-B: %d | Format-A: %d | List-only: %d | Skipped pages: %d)",
        len(merged),
        stats["format_b"], stats["format_a"],
        len(merged) - len(profile_exhibitors),
        stats["skipped"],
    )
    return merged


# ══════════════════════════════════════════════════════════════════════════════
# FORMAT DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def _detect_format(lines: list[str]) -> str:
    """Return 'A', 'B', or '' (unknown/skip)."""
    has_field = False
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if _FORMAT_B_COMPANY_RE.match(s):
            return "B"
        if _FIELD_RE.match(s):
            has_field = True
    return "A" if has_field else ""


def _should_skip(raw_text: str) -> bool:
    lower = raw_text.lower()
    if not _has_enough_fields(raw_text):
        return any(kw in lower for kw in SKIP_KEYWORDS)
    return False


def _has_enough_fields(text: str) -> bool:
    count = 0
    for pattern in (
        r"Address\s*[:\-]",
        r"Contact\s+Person\s*[:\-]",
        r"Tel\./",
        r"E-?mail\s*[:\-]",
        r"Products?\s+on\s+Display\s*[:\-]",
    ):
        if re.search(pattern, text, re.IGNORECASE):
            count += 1
            if count >= MIN_FIELDS_TO_QUALIFY:
                return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
# FORMAT-A PARSER
# ══════════════════════════════════════════════════════════════════════════════

def _parse_format_a(lines: list[str], page_num: int) -> list[dict[str, str]]:
    blocks: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        s = line.strip()
        if not s:
            continue
        fm = _FIELD_RE.match(s)
        key = _normalise_label(fm.group(1)) if fm else None

        if key == "address" and _block_has_key(current, "address"):
            blocks.append(current)
            current = [s]
        elif not current and not fm and not _is_noise_line(s):
            current = [s]
        else:
            current.append(s)

    if current:
        blocks.append(current)

    return [
        r for b in blocks
        if (r := _parse_block_a(b, page_num)) and (r.get("company_name") or r.get("address"))
    ]


def _block_has_key(block: list[str], target_key: str) -> bool:
    for line in block:
        fm = _FIELD_RE.match(line.strip())
        if fm and _normalise_label(fm.group(1)) == target_key:
            return True
    return False


def _parse_block_a(lines: list[str], page_num: int) -> dict[str, str]:
    ex = _empty()
    current_key: Optional[str] = None
    found_field = False

    for line in lines:
        s = line.strip()
        if not s or _is_noise_line(s):
            continue
        fm = _FIELD_RE.match(s)
        if fm:
            found_field = True
            current_key = _normalise_label(fm.group(1))
            if current_key:
                ex[current_key] = (ex[current_key] + " " + fm.group(2).strip()).strip()
        elif not found_field:
            ex["company_name"] = (ex["company_name"] + " " + s).strip()
        elif current_key:
            ex[current_key] = (ex[current_key] + " " + s).strip()

    return {k: _clean(v) for k, v in ex.items()}


# ══════════════════════════════════════════════════════════════════════════════
# FORMAT-B PARSER
# ══════════════════════════════════════════════════════════════════════════════

def _parse_format_b(lines: list[str], page_num: int) -> list[dict[str, str]]:
    segments: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        s = line.strip()
        if _FORMAT_B_COMPANY_RE.match(s):
            if current:
                segments.append(current)
            current = [s]
        else:
            current.append(s)

    if current:
        segments.append(current)

    return [
        r for seg in segments
        if (r := _parse_segment_b(seg, page_num)) and (r.get("company_name") or r.get("address"))
    ]


def _parse_segment_b(seg: list[str], page_num: int) -> Optional[dict[str, str]]:
    if not seg:
        return None

    hall_match = _FORMAT_B_COMPANY_RE.match(seg[0])
    if not hall_match:
        return None

    company     = hall_match.group(1).strip()
    field_start = 1

    if len(seg) > 1:
        nxt = seg[1].strip()
        if _FORMAT_B_STALL_RE.match(nxt):
            field_start = 2
        elif not _FORMAT_B_COMPANY_RE.match(nxt) and not _FIELD_RE.match(nxt):
            cont = _CONT_STALL_RE.match(nxt)
            if cont:
                part = cont.group(1).strip()
                if not _FIELD_RE.match(part):
                    company = company + " " + part
                field_start = 2
            elif nxt and not _is_noise_line(nxt):
                company = company + " " + nxt
                field_start = 2

    ex = _empty()
    current_key: Optional[str] = None

    for line in seg[field_start:]:
        s = line.strip()
        if not s or _is_noise_line(s):
            continue
        fm = _FIELD_RE.match(s)
        if fm:
            current_key = _normalise_label(fm.group(1))
            if current_key:
                val = fm.group(2).strip()
                if current_key == "address":
                    val = _ADDR_HALL_TAIL_RE.sub("", val).strip()
                ex[current_key] = (ex[current_key] + " " + val).strip()
        elif current_key:
            cont = s
            if current_key == "address":
                cont = _ADDR_HALL_TAIL_RE.sub("", s).strip()
            if cont:
                ex[current_key] = (ex[current_key] + " " + cont).strip()

    header = _clean(company)
    header = re.sub(r"\s+STALL\s*[:\-]?\s*$", "", header, flags=re.IGNORECASE).strip()
    if not ex["company_name"] or len(header) > len(ex["company_name"]):
        ex["company_name"] = header

    res = {k: _clean(v) for k, v in ex.items()}
    if res.get("company_name"):
        res["company_name"] = re.sub(
            r"\s+STALL\s*[:\-]?\s*$", "", res["company_name"], flags=re.IGNORECASE
        ).strip()
    return res


# ══════════════════════════════════════════════════════════════════════════════
# FORMAT-C PARSER  — Participant / S.No. list pages
# ══════════════════════════════════════════════════════════════════════════════

def _split_list_row(rest: str) -> tuple[str, str, str]:
    """
    Split a list-row body (after S.No.) into (company_name, stall, hall).

    The PDF may join multi-line entries, producing:
        "COMPANY_NAME  STALL  HALL"                   (clean)
        "COMPANY_NAME STALL HALL CONTINUATION_TEXT"   (wrapped company suffix)

    Strategy:
      A) Clean 2+-space columns → easy split
      B) HANGAR/OPEN suffix detected
      C) Find hall-code pattern; any text AFTER it is a company-name suffix
         (wrapped continuation). Scan LEFT of hall-code for the stall token.
      D) Fallback: right-to-left stall-token scan
    """
    stripped = rest.strip()

    # ── A: clean 2+-space split ──────────────────────────────────────────────
    parts = re.split(r"\s{2,}", stripped)
    if len(parts) >= 3:
        company = parts[0].strip()
        stall   = parts[1].strip()
        hall    = parts[2].strip()
        if len(parts) > 3:
            suffix = " ".join(p.strip() for p in parts[3:])
            if suffix and not _STALL_START_RE.match(suffix.split()[0]):
                company = (company + " " + suffix).strip()
        return company, stall, hall

    if len(parts) == 2:
        candidate = parts[1].strip()
        toks = candidate.split()
        if toks and _STALL_START_RE.match(toks[0]):
            return parts[0].strip(), toks[0], " ".join(toks[1:])
        return parts[0].strip(), "", candidate

    # ── B: HANGAR/OPEN AREA suffix ───────────────────────────────────────────
    hangar_m = re.search(
        r"\s+(H[A-Z0-9][\w\-]*)\s+((?:HANGAR|OPEN\s*AREA?)\s*[\w]*)\s*",
        stripped, re.IGNORECASE,
    )
    if hangar_m:
        company_base = stripped[: hangar_m.start()].strip()
        stall        = hangar_m.group(1).strip()
        hall         = hangar_m.group(2).strip()
        # Everything after the HANGAR match = wrapped company-name continuation
        company_cont = stripped[hangar_m.end():].strip()
        company = (company_base + " " + company_cont).strip() if company_cont else company_base
        return company or stripped, stall, hall

    # ── C: hall-code + stall scan ────────────────────────────────────────────
    # Strategy: find hall-code candidates from right-to-left (rightmost first).
    # For each candidate, check if a stall token exists in the prefix.
    # Any text AFTER the hall-code is a wrapped company-name continuation.
    #
    # We use _HALL_CODE_ANY_RE (unanchored) but only accept matches where the
    # number is preceded by a stall-like token — this prevents bare numbers
    # inside company names (like "5 AM FARMS") from triggering false matches.
    candidates = list(_HALL_CODE_ANY_RE.finditer(stripped))
    # Iterate from last match to first (right to left)
    for hm in reversed(candidates):
        hall_str     = hm.group(1).strip()
        prefix       = stripped[: hm.start()].strip()
        company_cont = stripped[hm.end():].strip()

        # Must have a stall-like token in the prefix
        p_toks = prefix.split()
        stall_idx = None
        for idx in range(len(p_toks) - 1, -1, -1):
            tok = p_toks[idx]
            if _STALL_START_RE.match(tok) or _STALL_TOKEN_RE.match(tok):
                stall_idx = idx
                break

        if stall_idx is None:
            continue   # no stall in prefix → try next candidate leftward

        company_base = " ".join(p_toks[:stall_idx]).strip()
        stall        = " ".join(p_toks[stall_idx:]).strip()
        company      = (company_base + " " + company_cont).strip() \
                       if company_cont else company_base
        return company or prefix, stall, hall_str

    # ── D: fallback right-to-left stall-token scan ──────────────────────────
    tokens = stripped.split()
    for idx in range(len(tokens) - 1, -1, -1):
        tok = tokens[idx]
        if _STALL_START_RE.match(tok) or _STALL_TOKEN_RE.match(tok):
            company = " ".join(tokens[:idx]).strip()
            stall   = tokens[idx]
            hall    = " ".join(tokens[idx + 1:]).strip()
            return company or stripped, stall, hall

    return stripped, "", ""


def _parse_format_c(raw_text: str, page_num: int) -> list[dict[str, str]]:
    """
    Extract exhibitor stubs from a participant-list / S.No. table page.

    Two-pass:
      Pass A — collect raw rows, joining wrapped continuation lines onto the
               numbered entry above them.
      Pass B — split each joined row into (company_name, stall, hall).
    """
    # ── Pass A: join continuation lines ──────────────────────────────────────
    raw_rows: list[str] = []

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # Skip header row
        if re.match(r"^S\.?NO\.?\s", line, re.IGNORECASE):
            continue
        # Skip roman-numeral page numbers (lv, lxvii …)
        if re.match(r"^[ivxlcdm]{1,8}$", line, re.IGNORECASE):
            continue
        # Skip bare numeric page numbers
        if re.match(r"^\d{1,4}$", line):
            continue

        m = _LISTROW_RE.match(line)
        if m:
            raw_rows.append(line)
        else:
            # Continuation — glue onto the previous numbered row
            if raw_rows:
                raw_rows[-1] = raw_rows[-1] + " " + line

    # ── Pass B: parse each joined row ────────────────────────────────────────
    entries: list[dict[str, str]] = []

    for row in raw_rows:
        m = _LISTROW_RE.match(row)
        if not m:
            continue
        rest = m.group(2).strip()
        company, stall, hall = _split_list_row(rest)

        if not company:
            continue

        addr_parts = []
        if stall:
            addr_parts.append(f"Stall: {stall}")
        if hall:
            addr_parts.append(f"Hall: {hall}")
        address_stub = "  |  ".join(addr_parts)

        ex = _empty()
        ex["company_name"] = _clean(company)
        ex["address"]      = address_stub
        entries.append(ex)

    return entries


# ══════════════════════════════════════════════════════════════════════════════
# DEDUPLICATION — merge list-only entries into full profiles
# ══════════════════════════════════════════════════════════════════════════════

def _normalise_for_dedup(name: str) -> str:
    """Normalise a company name for fuzzy deduplication."""
    n = name.upper().strip()
    for suffix in [
        "PRIVATE LIMITED", "PVT. LTD.", "PVT.LTD.", "PVT LTD",
        "LIMITED", "LTD.", "LTD", "LLP", "& CO.", "& CO", "CO.",
        "INDIA PVT", "INDIA", "(INDIA)", "INC.", "CORP.", "CORPORATION",
    ]:
        n = n.replace(suffix, " ")
    n = re.sub(r"[^A-Z0-9 ]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def _merge_list_entries(
    profiles: list[dict[str, str]],
    list_entries: list[dict[str, str]],
) -> list[dict[str, str]]:
    """
    Return profiles + list_entries whose company name is NOT already in profiles.
    Uses normalised fuzzy matching (exact + substring) for deduplication.
    """
    if not list_entries:
        return profiles

    profile_norm_set: set[str] = {_normalise_for_dedup(p["company_name"]) for p in profiles}

    new_entries: list[dict[str, str]] = []
    for entry in list_entries:
        norm = _normalise_for_dedup(entry["company_name"])
        if not norm:
            continue
        if norm in profile_norm_set:
            continue
        # Substring match handles truncated names in the list
        found = any(
            len(norm) >= 8 and (norm in pnorm or pnorm in norm)
            for pnorm in profile_norm_set
        )
        if not found:
            new_entries.append(entry)
            profile_norm_set.add(norm)

    log.info(
        "  List-page merge: %d list entries scanned, %d new (no full profile found)",
        len(list_entries), len(new_entries),
    )
    return profiles + new_entries


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _empty() -> dict[str, str]:
    return {
        "company_name":        "",
        "address":             "",
        "contact_person":      "",
        "tel_mobile":          "",
        "email":               "",
        "products_on_display": "",
    }


def _normalise_label(raw: str) -> Optional[str]:
    r = raw.strip().lower()
    if re.search(r"company\s+name", r):   return "company_name"
    if r.startswith("address"):           return "address"
    if re.search(r"contact\s+person", r): return "contact_person"
    if re.search(r"tel|mob(?:ile)?", r):  return "tel_mobile"
    if "e-mail" in r or "email" in r:     return "email"
    if re.search(r"products?\s+on", r):   return "products_on_display"
    return None


def _is_noise_line(line: str) -> bool:
    return bool(_NOISE_RE.match(line.strip()))


def _is_valid(ex: dict[str, str]) -> bool:
    return bool(ex.get("company_name") or ex.get("address"))


_MULTI_SPACE   = re.compile(r"\s{2,}")
_TRAILING_JUNK = re.compile(r"[,;\s]+$")


def _clean(v: str) -> str:
    return _TRAILING_JUNK.sub("", _MULTI_SPACE.sub(" ", v).strip())
